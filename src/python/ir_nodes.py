from dataclasses import dataclass

from . import type_defs as types
from .scope import Scope


class Object:
    pass


class Ref:
    def __init__(self, name, type_hint, *, checked_type=None, values=None):
        self.name = name
        self.type_hint = type_hint
        self.checked_type = checked_type
        self.values = values
        if values is None:
            self.values = []

    def __repr__(self):
        return (
            f"Ref(name={self.name}, type_hint={self.type_hint}, "
            f"checked_type={self.checked_type}, values={self.values})"
        )


class Instruction:
    pass


@dataclass
class FieldRef(Ref):
    parent: Ref


@dataclass
class FunctionSignatureRef(Ref):
    name: str
    params: list[str]
    type_hint: types.FunctionType
    checked_type: types.FunctionType = None


@dataclass
class Block:
    stmts: list


@dataclass
class MultiInstr(Instruction):
    intstrs: list[Instruction]


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
