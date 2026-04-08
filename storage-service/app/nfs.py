"""NFS export management.

Requirements: 5.2
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class NFSExport:
    path: str
    allowed_hosts: list[str] = field(default_factory=lambda: ["*"])
    options: str = "rw,sync,no_subtree_check"


class NFSManager:
    def __init__(self) -> None:
        self._exports: dict[str, NFSExport] = {}

    def add_export(self, export: NFSExport) -> None:
        self._exports[export.path] = export

    def remove_export(self, path: str) -> bool:
        return self._exports.pop(path, None) is not None

    def list_exports(self) -> list[NFSExport]:
        return list(self._exports.values())

    def generate_exports_line(self, export: NFSExport) -> str:
        hosts = " ".join(f"{h}({export.options})" for h in export.allowed_hosts)
        return f"{export.path} {hosts}"
