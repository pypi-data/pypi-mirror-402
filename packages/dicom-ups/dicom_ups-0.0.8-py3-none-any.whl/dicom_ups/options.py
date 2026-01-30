from __future__ import annotations

import enum
import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Final


@dataclass(frozen=True)
class Server:
    host: str
    port: int | None
    ae: str | None

    def __str__(self) -> str:
        if self.ae:
            return f'DIMSE: "{self.ae}" {self.host}:{self.port}'
        return f'DICOM Web: "{self.host}"'

    def __repr__(self) -> str:
        return str(self)


class ActionType(enum.IntEnum):
    DELETE = 1
    RESTART = 2
    SUBSCRIBE = 3
    UNSUBSCRIBE = 4
    SUSPEND_SUBSCRIPTION = 5


def get_servers() -> dict[str, Server]:
    servers: dict[str, Server | dict[str, Server]] = {}

    with Path(os.environ['SERVERS_TOML']).open('rb') as f:
        data = tomllib.load(f)

    for k, v in data['server'].items():
        if isinstance(v, list):
            servers[k] = {
                s['name']: Server(
                    host=s['host'],
                    port=int(s['port']) if 'port' in v else None,
                    ae=s.get('ae', None)
                ) for s in v}
        else:
            servers[k] = Server(v['host'], int(v['port']) if 'port' in v else None, v.get('ae', None))

    return servers


TIMEOUT: Final[int] = 15 * 60  # Timeout 15 min


if __name__ == '__main__':
    os.environ['SERVERS_TOML'] = r'D:\Symphony\dashboard\servers.toml'
    a = get_servers()
