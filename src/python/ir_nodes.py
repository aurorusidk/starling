from dataclasses import dataclass, field
from hashlib import sha1

from . import type_defs as types
from .scope import Scope


def id_hash(obj):
    return sha1(str(id(obj)).encode("UTF-8")).hexdigest()[:4]


class Object:
    pass


@dataclass
class Value(Object):
    value: object
    typ: types.Type


@dataclass
class Constant(Object):
    value: object
    typ: types.Type


@dataclass
class Ref(Object):
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
    instrs: list


@dataclass
class Declare(Instruction):
    ref: Ref


@dataclass
class Assign(Instruction):
    target: Ref
    value: Object


@dataclass
class Return(Instruction):
    value: Object


@dataclass
class Branch(Instruction):
    block: Block


@dataclass
class CBranch(Instruction):
    condition: Object
    t_block: Block
    f_block: Block


@dataclass
class DefFunc(Instruction):
    target: FunctionSignatureRef
    block: Block
    scope: Scope


# this is the same as in the AST
# maybe we want to define the ops separately to remove the dependence on tokens
# for now the op will just be the op string
@dataclass
class Unary(Instruction):
    op: str
    rhs: Object


@dataclass
class Binary(Instruction):
    op: str
    lhs: Object
    rhs: Object


@dataclass
class Program:
    declrs: list[Instruction]


class IRPrinter:
    def __init__(self):
        self.blocks_seen = []

    def to_string(self, ir):
        match ir:
            case Value(value, _):
                return str(value)
            case Constant(value, _):
                return str(value)
            case StructTypeRef():
                return f"{ir.name}{{{', '.join(ir.fields)}}}"
            case FunctionSignatureRef():
                return f"{ir.name}({', '.join(ir.params)})"
            case Ref(name):
                return name
            case Block():
                if id_hash(ir) not in self.blocks_seen:
                    block_hash = id_hash(ir)
                    self.blocks_seen.append(block_hash)
                    instrs = '\n'.join(' ' + self.to_string(i) for i in ir.instrs)
                    if not instrs:
                        instrs = " [empty]"
                    return f"\n{block_hash}:\n{instrs}"
                return ""
            case Declare(ref):
                return f"DECLARE {self.to_string(ref)}"
            case Assign(target, value):
                return f"ASSIGN {self.to_string(target)} <- {self.to_string(value)}"
            case Return(value):
                return f"RETURN {self.to_string(value)}"
            case Branch(block):
                return f"BRANCH {id_hash(block)}{self.to_string(block)}"
            case CBranch(condition, t_block, f_block):
                return (
                    f"CBRANCH {self.to_string(condition)} "
                    f"{id_hash(t_block)} {id_hash(f_block)}"
                    f"{self.to_string(t_block)}{self.to_string(f_block)}"
                )
            case DefFunc(target, block):
                return f"DEFINE {self.to_string(target)}{self.to_string(block)}"
            case Unary(op, rhs):
                return f"{op}{self.to_string(rhs)}"
            case Binary(op, lhs, rhs):
                return f"({self.to_string(lhs)} {op} {self.to_string(rhs)})"
            case Program(declrs):
                return '\n'.join(self.to_string(d) for d in declrs)
            case _:
                assert False, ir
