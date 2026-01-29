from enum import Enum


class ComponentLifecycleTransitionTransition(str, Enum):
    ACTIVATE = "activate"
    ACTIVE_SHUTDOWN = "active_shutdown"
    CLEANUP = "cleanup"
    CONFIGURE = "configure"
    DEACTIVATE = "deactivate"
    INACTIVE_SHUTDOWN = "inactive_shutdown"
    UNCONFIGURED_SHUTDOWN = "unconfigured_shutdown"

    def __str__(self) -> str:
        return str(self.value)
