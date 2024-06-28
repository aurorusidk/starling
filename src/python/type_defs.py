from dataclasses import dataclass
from enum import Enum, Flag, auto


BaseTypeKind = Enum("BaseTypeKind", [
    "INT", "FLOAT", "FRAC", "STR", "BOOL",
])


class BaseTypeFlag(Flag):
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
class BaseType(Type):
    kind: BaseTypeKind
    flags: BaseTypeFlag
    string: str


@dataclass
class ArrayType(Type):
    elem_type: Type
    length: int


@dataclass
class FunctionType(Type):
    return_type: Type
    param_types: list[Type]
