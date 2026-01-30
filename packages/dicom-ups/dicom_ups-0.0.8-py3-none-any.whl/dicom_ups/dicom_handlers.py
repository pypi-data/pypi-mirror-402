from __future__ import annotations

import enum
import typing
from typing import Any, Self

import pydicom
import pydicom.uid
import pynetdicom.dimse_primitives
from pydicom import Dataset
from pynetdicom.ae import ApplicationEntity
from pynetdicom.sop_class import (  # type: ignore
    ModalityPerformedProcedureStep,  # type: ignore
    PatientRootQueryRetrieveInformationModelFind,  # type: ignore
    UnifiedProcedureStepEvent,  # type: ignore
    UnifiedProcedureStepPull,  # type: ignore
    UnifiedProcedureStepPush,  # type: ignore
    UnifiedProcedureStepQuery,  # type: ignore
    UnifiedProcedureStepWatch  # type: ignore
)

from dicom_ups.options import ActionType, get_servers

if typing.TYPE_CHECKING:
    from collections.abc import Generator
    import types
    from pynetdicom.events import Event
    from dicom_ups.options import Server


class DbProtocol(typing.Protocol):
    def add_job(self, ds: Dataset) -> None:
        ...

    def get_job(self, uid: str | pydicom.uid.UID) -> Dataset | None:
        ...

    def update_job(self, ds: Dataset) -> None:
        ...

    def remove_job(self, uid: str | pydicom.uid.UID) -> None:
        ...

    def get_uids(self) -> list[str]:
        ...

    def get_all_jobs(self) -> list[Dataset]:
        ...

    def get_jobs_status(self, status: Status) -> list[Dataset]:
        ...

    def checkpoint(self) -> None:
        ...


class Status(enum.Enum):
    SCHEDULED = 'SCHEDULED'
    IN_PROGRESS = 'IN PROGRESS'
    CANCELED = 'CANCELED'
    COMPLETED = 'COMPLETED'


SUBSCRIBED_AE: set[Server] = set()


class DicomAssociation:
    def __init__(self, node_name: str = 'conductor') -> None:
        self._server = get_servers()[node_name]
        assert self._server.port

        application_entity = ApplicationEntity()
        application_entity.add_requested_context(ModalityPerformedProcedureStep)
        application_entity.add_requested_context(PatientRootQueryRetrieveInformationModelFind)
        application_entity.add_requested_context(UnifiedProcedureStepPush)
        application_entity.add_requested_context(UnifiedProcedureStepWatch)
        application_entity.add_requested_context(UnifiedProcedureStepPull)
        application_entity.add_requested_context(UnifiedProcedureStepEvent)
        application_entity.add_requested_context(UnifiedProcedureStepQuery)
        self.assoc = application_entity.associate(self._server.host, self._server.port)

    @property
    def server(self) -> Server:
        return self._server

    def __enter__(self) -> Self:
        return self

    def __exit__(self,
                 exc_type: type[BaseException] | None,
                 exc_val: BaseException | None,
                 exc_tb: types.TracebackType | None) -> None:
        if self.assoc:
            self.assoc.release()


def n_action(event: Event, database: DbProtocol) -> tuple[int, pydicom.Dataset | None]:  # noqa: PLR0911, C901  # pylint: disable=too-many-return-statements
    assert isinstance(event.request, pynetdicom.dimse_primitives.N_ACTION)

    match ActionType(event.action_type):  # type: ignore
        case ActionType.DELETE:
            database.remove_job(event.action_information.AffectedSOPInstanceUID)
            return 0x0000, pydicom.Dataset()

        case ActionType.RESTART:
            job = database.get_job(event.action_information.AffectedSOPInstanceUID)

            if job is None:
                return 0x0110, pydicom.Dataset()

            job.PerformedProcedureStepStatus = Status.SCHEDULED.value
            database.update_job(job)

            return 0x0000, pydicom.Dataset()

        case ActionType.SUBSCRIBE:
            ae = event.action_information.ReceivingAE
            for server in get_servers().values():
                if isinstance(server, dict):
                    continue
                if server.ae == ae:
                    SUBSCRIBED_AE.add(server)
                    return 0x0000, pydicom.Dataset()
            return 0x0110, pydicom.Dataset()

        case ActionType.UNSUBSCRIBE:
            ae = event.action_information.ReceivingAE
            for server in get_servers().values():
                if isinstance(server, dict):
                    continue
                if server.ae == ae:
                    SUBSCRIBED_AE.remove(server)
                    return 0x0000, pydicom.Dataset()
            return 0x0110, pydicom.Dataset()

        case _:
            pass

    # Processing Failure
    return 0x0110, pydicom.Dataset()


def n_create(event: Event, database: DbProtocol) -> tuple[int, pydicom.Dataset | None]:
    assert isinstance(event.request, pynetdicom.dimse_primitives.N_CREATE)

    req = event.request

    if req.AffectedSOPInstanceUID is None:
        # Failed - invalid attribute value
        return 0x0106, None

    uids = database.get_uids()

    # Can't create a duplicate SOP Instance
    if req.AffectedSOPInstanceUID in uids:
        # Failed - duplicate SOP Instance
        return 0x0111, None

    # The N-CREATE request's *Attribute List* dataset
    attr_list = event.attribute_list

    # Performed Procedure Step Status must be 'IN PROGRESS'
    if "PerformedProcedureStepStatus" not in attr_list:
        # Failed - missing attribute
        return 0x0120, None

    if attr_list.PerformedProcedureStepStatus.upper() != 'SCHEDULED':
        return 0x0106, None

    # Skip other tests...

    # Create a Modality Performed Procedure Step SOP Class Instance
    #   DICOM Standard, Part 3, Annex B.17
    ds = pydicom.Dataset()

    # Add the SOP Common module elements (Annex C.12.1)
    # ds.SOPClassUID = ModalityPerformedProcedureStep
    ds.SOPInstanceUID = req.AffectedSOPInstanceUID

    # Update with the requested attributes
    ds.update(attr_list)

    # Add the dataset to the managed SOP Instances
    database.add_job(ds)

    # Return status, dataset
    return 0x0000, ds


def c_find(event: Event, database: DbProtocol) -> Generator[tuple[int, Any] | tuple[int, None]]:
    """
    Event handler for C-FIND events.
    This function is called when the SCP receives a C-FIND request.
    """
    assert isinstance(event.request, pynetdicom.dimse_primitives.C_FIND)

    request_ds = event.identifier

    # Extract query keys from the request_ds
    # For a C-FIND, keys typically contain wildcards or specific values.
    # We'll use a simple matching logic for demonstration.
    query_patient_id = request_ds.get("PatientID", None)
    query_patient_name = request_ds.get("PatientName", None)
    query_procedure_state = request_ds.get("ProcedureStepState", None)
    query_req_proc_desc = request_ds.get("RequestedProcedureDescription", None)

    found_matches = []
    for ups_data in database.get_all_jobs():
        if query_patient_id and query_patient_id != '*' and query_patient_id != ups_data.get("PatientID"):
            continue
        if (query_patient_name and query_patient_name != '*' and
                query_patient_name.upper() not in ups_data.get("PatientName", "").upper()):
            continue
        if (query_procedure_state and query_procedure_state != '*' and
                query_procedure_state != ups_data.get("ProcedureStepState")):
            continue
        if (query_req_proc_desc and query_req_proc_desc != '*' and
                query_req_proc_desc.upper() not in ups_data.get("RequestedProcedureDescription", "").upper()):
            continue

        found_matches.append(ups_data)

    # Yield each match with a 'Pending' status (0xFF00)
    for match_ds in found_matches:
        yield 0xFF00, match_ds  # 0xFF00: Pending

    # After yielding all matches, yield a 'Success' status (0x0000)
    yield 0x0000, None  # 0x0000: Success, Identifier is not returned for success


def n_get(event: Event, database: DbProtocol) -> tuple[int, pydicom.Dataset | None]:
    assert isinstance(event.request, pynetdicom.dimse_primitives.N_GET)
    uid = event.request.RequestedSOPInstanceUID
    assert uid is not None

    ds = database.get_job(uid)

    if ds is None:
        # Failure - SOP Instance not recognized
        return 0x0112, None

    # Return status, dataset
    return 0x0000, ds


def n_set(event: Event, database: DbProtocol) -> tuple[int, pydicom.Dataset | None]:
    assert isinstance(event.request, pynetdicom.dimse_primitives.N_SET)

    uid = event.request.RequestedSOPInstanceUID
    assert uid is not None

    ds = database.get_job(uid)

    if ds is None:
        # Failure - SOP Instance not recognized
        return 0x0112, None

    # The N-SET request's *Modification List* dataset
    mod_list = event.attribute_list

    # Skip other tests...
    ds.update(mod_list)

    database.update_job(ds)

    # Return status, dataset
    return 0x0000, ds
