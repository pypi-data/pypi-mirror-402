from enum import Enum


class CloudApplicationType(str, Enum):
    PLAIN = "plain"

    def __str__(self) -> str:
        return str(self.value)
