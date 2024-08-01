from dataclasses import dataclass

from . import type_defs as types


@dataclass
class Ref:
    typ: types.Type


@dataclass
class FieldRef:
    parent: Ref


@dataclass
class Block:
    stmts: list


@dataclass
class FunctionSignature:
    name: str
    params: list[str]
    type_hint: types.FunctionType
    checked_type: types.FunctionType = None


@dataclass
class Function:
    sig: FunctionSignature
    block: Block


@dataclass
class Program:
    declrs: list
