from enum import Enum


class CloudApplicationStatus(str, Enum):
    CHANGED = "changed"
    CLOUD_ONLY = "cloud-only"
    SYNCD = "syncd"

    def __str__(self) -> str:
        return str(self.value)
