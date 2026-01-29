from enum import Enum


class ApplicationLifecycleTransitionTransition(str, Enum):
    PAUSE = "pause"
    START = "start"
    STOP = "stop"

    def __str__(self) -> str:
        return str(self.value)
