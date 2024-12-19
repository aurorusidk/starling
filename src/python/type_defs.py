from dataclasses import dataclass
from enum import Flag, auto


class TypeFlag(Flag):
    META = auto()
    SIGNED_INT = auto()
    UNSIGNED_INT = auto()
    FLOAT = auto()
    RATIONAL = auto()
    STRING = auto()
    BOOLEAN = auto()
    FUNCTION = auto()
    STRUCT = auto()
    ARRAY = auto()
    VECTOR = auto()

    NUMERIC = SIGNED_INT | UNSIGNED_INT | FLOAT | RATIONAL
    ITERABLE = ARRAY | VECTOR | STRING


@dataclass(eq=False, repr=False)
class Type:
    bit_width: int
    flags: TypeFlag
    _string: str

    # base class for all types
    @property
    def string(self):
        return self._string

    def __str__(self):
        return self.string

    def __repr__(self):
        return self.string

    def __eq__(self, other):
        if not isinstance(other, Type):
            return False
        # The types are equal if all flags exactly match
        return (self.flags & other.flags) and not (self.flags ^ other.flags)

    def __hash__(self):
        # the type string should be unique
        return hash(self.string)


@dataclass(eq=False, repr=False)
class CompoundType(Type):
    fields: list[Type]

    @property
    def string(self):
        types = [f.string if f else "nil" for f in self.fields]
        return f"{self._string}<{', '.join(types)}>"

    def __eq__(self, other):
        return super.__eq__(other) and self.fields == other.fields


"""
@dataclass(eq=False, repr=False)
class SequenceType(Type):
    elem_type: Type

    @property
    def string(self):
        return f"sequence[{self.elem_type}]"


@dataclass(eq=False, repr=False)
class ArrayType(SequenceType):
    length: int

    @property
    def string(self):
        return f"arr<{self.elem_type}[{self.length}]>"


@dataclass(eq=False, repr=False)
class VectorType(SequenceType):
    @property
    def string(self):
        return f"vec<{self.elem_type}>"


@dataclass(eq=False, repr=False)
class FunctionType(Type):
    return_type: Type
    param_types: list[Type]

    @property
    def string(self):
        format_ptypes = ", ".join(str(p) for p in self.param_types)
        return f"fn ({format_ptypes}) -> {self.return_type}"


@dataclass(eq=False, repr=False)
class StructType(Type):
    fields: list[Type]

    @property
    def string(self):
        format_fields = ", ".join(str(f) for f in self.fields)
        return f"struct {{{format_fields}}}"


@dataclass(eq=False, repr=False)
class Interface(Type):
    name: str
    funcs: dict[str, FunctionType]

    @property
    def string(self):
        format_methods = ", ".join(str(m) for m in self.funcs)
        return f"interface {self.name} {{{format_methods}}}"
"""


def is_basic(typ, flag=None):
    if flag:
        return is_basic(typ) and (typ.flags & flag)
    else:
        return isinstance(typ, Type) and not isinstance(typ, CompoundType)
    # return isinstance(typ, BasicType) and (typ.flags & (flag if flag else True))


def is_numeric(typ):
    return is_basic(typ, TypeFlag.NUMERIC)


def is_string(typ):
    return is_basic(typ, TypeFlag.STRING)


def is_bool(typ):
    return is_basic(typ, TypeFlag.BOOLEAN)


def is_iterable(typ):
    return typ.flags & TypeFlag.ITERABLE
