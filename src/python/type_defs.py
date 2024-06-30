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
    @property
    def string(self):
        raise NotImplementedError

    def __str__(self):
        return self.string


@dataclass
class BasicType(Type):
    kind: BasicTypeKind
    flags: BasicTypeFlag
    _string: str

    @property
    def string(self):
        return self._string


@dataclass
class ArrayType(Type):
    elem_type: Type
    length: int

    @property
    def string(self):
        return f"[{self.length}]{self.elem_type.string}"


@dataclass
class VectorType(Type):
    elem_type: Type

    @property
    def string(self):
        return f"[]{self.elem_type.strin}"


@dataclass
class FunctionType(Type):
    return_type: Type
    param_types: list[Type]

    @property
    def string(self):
        format_ptypes = ", ".join(p.string for p in self.param_types)
        return f"fn ({format_ptypes}) -> {self.return_type.string}"


def is_basic(typ, flag=None):
    return isinstance(typ, BasicType) and typ.flags & flag if flag else True

def is_numeric(typ):
    return is_basic(typ, BasicTypeFlag.NUMERIC)

def is_string(typ):
    return is_basic(typ, BasicTypeFlag.STRING)
