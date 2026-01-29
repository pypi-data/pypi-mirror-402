from enum import Enum


class SequenceLifecycleTransitionTransition(str, Enum):
    ABORT = "abort"
    RESTART = "restart"
    START = "start"

    def __str__(self) -> str:
        return str(self.value)
