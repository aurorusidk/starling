from dataclasses import dataclass, field
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


@dataclass(eq=False)
class Type:
    methods: dict = field(default_factory=dict, kw_only=True)

    # base class for all types
    @property
    def string(self):
        raise NotImplementedError

    def __str__(self):
        return self.string

    def __eq__(self, other):
        return self.string == other.string

    def __hash__(self):
        # the type string should be unique
        return hash(self.string)


@dataclass(eq=False)
class BasicType(Type):
    kind: BasicTypeKind
    flags: BasicTypeFlag
    _string: str

    @property
    def string(self):
        return self._string


@dataclass(eq=False)
class OptionalType(Type):
    some_type: Type

    @property
    def string(self):
        return f"Optional<{self.some_type}>"


@dataclass(eq=False)
class ArrayType(Type):
    elem_type: Type
    length: int

    @property
    def string(self):
        return f"[{self.length}]{self.elem_type}"


@dataclass(eq=False)
class VectorType(Type):
    elem_type: Type

    @property
    def string(self):
        return f"[]{self.elem_type}"


@dataclass(eq=False)
class FunctionType(Type):
    return_type: Type
    param_types: list[Type]

    @property
    def string(self):
        format_ptypes = ", ".join(str(p) for p in self.param_types)
        return f"fn ({format_ptypes}) -> {self.return_type}"


@dataclass(eq=False)
class StructType(Type):
    name: str
    fields: dict[str, Type]

    @property
    def string(self):
        format_fields = ", ".join(str(f) for f in self.fields)
        return f"struct {{{format_fields}}}"


@dataclass(eq=False)
class Interface(Type):
    name: str
    methods: dict[str, FunctionType]

    @property
    def string(self):
        format_methods = ", ".join(str(m) for m in self.methods)
        return f"interface {self.name} {{{format_methods}}}"


def is_basic(typ, flag=None):
    return isinstance(typ, BasicType) and typ.flags & flag if flag else True


def is_numeric(typ):
    return is_basic(typ, BasicTypeFlag.NUMERIC)


def is_string(typ):
    return is_basic(typ, BasicTypeFlag.STRING)


def is_bool(typ):
    return is_basic(typ, BasicTypeFlag.BOOLEAN)


def is_iterable(typ):
    return isinstance(typ, (ArrayType, VectorType))
