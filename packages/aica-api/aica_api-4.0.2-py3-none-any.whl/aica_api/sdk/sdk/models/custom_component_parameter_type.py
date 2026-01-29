from enum import Enum


class CustomComponentParameterType(str, Enum):
    BOOL = "bool"
    BOOL_ARRAY = "bool_array"
    DOUBLE = "double"
    DOUBLE_ARRAY = "double_array"
    INT = "int"
    INT_ARRAY = "int_array"
    MATRIX = "matrix"
    STATE = "state"
    STRING = "string"
    STRING_ARRAY = "string_array"
    VECTOR = "vector"

    def __str__(self) -> str:
        return str(self.value)
