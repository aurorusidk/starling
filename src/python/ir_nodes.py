from dataclasses import dataclass, field
from hashlib import sha1

from . import type_defs as types
from .scope import Scope


def id_hash(obj):
    return sha1(str(id(obj)).encode("UTF-8")).hexdigest()[:4]


@dataclass
class Object:
    progress: object = field(default=None, init=False)
    checked_type: types.Type = field(default=None, init=False)


@dataclass
class Constant(Object):
    value: object


@dataclass
class Ref(Object):
    name: str
    type_hint: types.Type
    values: list = field(default_factory=list, init=False)


class Instruction(Object):
    is_terminator = False


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
    param_names: list[str]
    params: list[Ref] = None
    # we do not use `self.values`. maybe for function objects?
    return_values: list[Object] = field(default_factory=list, init=False)
    param_values: dict[str, list[Object]] = field(default_factory=dict, init=False)


@dataclass
class Block(Object):
    instrs: list
    deps: list = field(default_factory=list)

    @property
    def is_terminated(self):
        if self.instrs:
            return self.instrs[-1].is_terminator
        return False


@dataclass
class Declare(Instruction):
    ref: Ref


@dataclass
class Assign(Instruction):
    target: Ref
    value: Object


@dataclass
class Load(Instruction):
    ref: Ref


@dataclass
class Call(Instruction):
    target: FunctionSignatureRef
    args: list[Object]


@dataclass
class Return(Instruction):
    is_terminator = True
    value: Object


@dataclass
class Branch(Instruction):
    is_terminator = True
    block: Block


@dataclass
class CBranch(Instruction):
    is_terminator = True
    condition: Object
    t_block: Block
    f_block: Block


@dataclass
class DefFunc(Instruction):
    target: FunctionSignatureRef
    block: Block


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
class Program(Object):
    block: Block


class IRPrinter:
    def __init__(self):
        self.blocks_seen = []

    def to_string(self, ir):
        string = ""
        match ir:
            case Constant(value):
                string += str(value)
            case StructTypeRef():
                string += f"{ir.name}{{{', '.join(ir.fields)}}}"
            case FunctionSignatureRef():
                string += f"{ir.name}({', '.join(ir.param_names)})"
            case Ref(name):
                string += name
            case Block():
                if id_hash(ir) not in self.blocks_seen:
                    block_hash = id_hash(ir)
                    self.blocks_seen.append(block_hash)
                    instrs = '\n'.join(' ' + self.to_string(i) for i in ir.instrs)
                    if not instrs:
                        instrs = " [empty]"
                    string += f"\n{block_hash}:\n{instrs}"
            case Declare(ref):
                string += f"DECLARE {self.to_string(ref)}"
            case Assign(target, value):
                string += f"ASSIGN {self.to_string(target)} <- {self.to_string(value)}"
            case Load(ref):
                string += f"LOAD({self.to_string(ref)})"
            case Call(ref, args):
                args = ', '.join(self.to_string(a) for a in args)
                string += f"CALL {self.to_string(ref)} ({args})"
            case Return(value):
                string += f"RETURN {self.to_string(value)}"
            case Branch(block):
                string += f"BRANCH {id_hash(block)}{self.to_string(block)}"
            case CBranch(condition, t_block, f_block):
                string += (
                    f"CBRANCH {self.to_string(condition)} "
                    f"{id_hash(t_block)} {id_hash(f_block)}"
                    f"{self.to_string(t_block)}{self.to_string(f_block)}"
                )
            case DefFunc(target, block):
                string += f"DEFINE {self.to_string(target)}{self.to_string(block)}"
            case Unary(op, rhs):
                string += f"{op}{self.to_string(rhs)}"
            case Binary(op, lhs, rhs):
                string += f"({self.to_string(lhs)} {op} {self.to_string(rhs)})"
            case Program(block):
                string += self.to_string(block)
            case _:
                assert False, ir
        if ir.checked_type is not None:
            string += f" [{ir.checked_type}]"
        return string
