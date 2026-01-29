from enum import Enum


class CustomComponentCodeType(str, Enum):
    SNIPPETS = "snippets"
    SOURCE = "source"

    def __str__(self) -> str:
        return str(self.value)
