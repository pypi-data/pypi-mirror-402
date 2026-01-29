from enum import Enum


class ApplicationStatus(str, Enum):
    PAUSED = "paused"
    RUNNING = "running"
    SET = "set"
    UNSET = "unset"

    def __str__(self) -> str:
        return str(self.value)
