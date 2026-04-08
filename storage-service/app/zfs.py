"""ZFS dataset and snapshot management.

Requirements: 5.3, 5.6
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass
class ZFSDataset:
    name: str
    mountpoint: str
    compression: str = "lz4"
    checksum: str = "on"


@dataclass
class ZFSSnapshot:
    dataset: str
    name: str

    @property
    def full_name(self) -> str:
        return f"{self.dataset}@{self.name}"


class ZFSManager:
    """Manages ZFS datasets and snapshots via CLI commands."""

    @staticmethod
    def create_dataset(dataset: ZFSDataset) -> str:
        return (
            f"zfs create -o mountpoint={dataset.mountpoint} "
            f"-o compression={dataset.compression} "
            f"-o checksum={dataset.checksum} {dataset.name}"
        )

    @staticmethod
    def create_snapshot(snapshot: ZFSSnapshot) -> str:
        return f"zfs snapshot {snapshot.full_name}"

    @staticmethod
    def restore_snapshot(snapshot: ZFSSnapshot) -> str:
        return f"zfs rollback {snapshot.full_name}"

    @staticmethod
    def list_snapshots(dataset: str) -> str:
        return f"zfs list -t snapshot -r {dataset}"
