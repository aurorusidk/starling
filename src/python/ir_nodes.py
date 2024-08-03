from dataclasses import dataclass, field

from . import type_defs as types
from .scope import Scope


class Object:
    pass


@dataclass
class Value(Object):
    value: object
    typ: types.Type


@dataclass
class Constant(Object):
    value: Value
    typ: types.Type


@dataclass
class Ref:
    name: str
    type_hint: types.Type
    checked_type: types.Type = field(default=None, init=False)
    values: list = field(default_factory=list, init=False)


class Instruction:
    pass


@dataclass
class FieldRef(Ref):
    parent: Ref


@dataclass
class StructTypeRef(Ref, types.Type):
    name: str
    fields: list[str]

    @property
    def string(self):
        if self.checked_type is None:
            return str(self.type_hint)
        return str(self.checked_type)


@dataclass
class FunctionSignatureRef(Ref):
    name: str
    params: list[str]


@dataclass
class Block:
    stmts: list


@dataclass
class Declare(Instruction):
    ref: Ref


@dataclass
class Assign(Instruction):
    target: Ref
    value: Object


@dataclass
class DefFunc(Instruction):
    target: FunctionSignatureRef
    block: Block
    scope: Scope


@dataclass
class Program:
    declrs: list
