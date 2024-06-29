from dataclasses import dataclass
from enum import Enum, Flag, auto


BasicTypeKind = Enum("BasicTypeKind", [
    "INT", "FLOAT", "FRAC", "STR", "BOOL",
])


class BasicTypeFlag(Flag):
    INTEGER = auto()
    FLOAT = auto()
    RATIONAL = auto()
    STRING = auto()
    BOOLEAN = auto()
    
    NUMERIC = INTEGER | FLOAT | RATIONAL


class Type:
    # base class for all types
    pass


@dataclass
class BasicType(Type):
    kind: BasicTypeKind
    flags: BasicTypeFlag
    string: str


@dataclass
class ArrayType(Type):
    elem_type: Type
    length: int


@dataclass
class FunctionType(Type):
    return_type: Type
    param_types: list[Type]
