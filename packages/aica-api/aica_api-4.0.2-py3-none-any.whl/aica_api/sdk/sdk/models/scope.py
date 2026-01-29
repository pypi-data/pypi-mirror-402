from enum import Enum


class Scope(str, Enum):
    CLOUD_CONFIG = "cloud-config"
    CONTROL = "control"
    MONITOR = "monitor"
    STATUS = "status"
    USER = "user"
    USERS = "users"

    def __str__(self) -> str:
        return str(self.value)
