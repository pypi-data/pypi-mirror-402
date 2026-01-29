from enum import Enum


class CustomComponentServiceType(str, Enum):
    EMPTY = "empty"
    STRING = "string"

    def __str__(self) -> str:
        return str(self.value)
