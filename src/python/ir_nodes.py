from dataclasses import dataclass, field
from hashlib import sha1

from . import type_defs as types


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
    type_hint: Object
    values: list = field(default_factory=list, kw_only=True)
    members: dict = field(default_factory=dict, kw_only=True)


@dataclass
class Type(Ref):
    name: str
    methods: list = field(default_factory=list, kw_only=True)


class Instruction(Object):
    is_terminator = False


@dataclass
class Block(Object):
    instrs: list[Instruction]
    deps: list = field(default_factory=list)

    def __hash__(self):
        return hash(id(self))

    @property
    def is_terminated(self):
        if self.instrs:
            return self.instrs[-1].is_terminator
        return False


@dataclass
class FieldRef(Ref):
    parent: Ref


@dataclass
class StructTypeRef(Type):
    name: str
    fields: list[str]

    @property
    def string(self):
        if self.checked_type is None:
            return str(self.type_hint)
        return str(self.checked_type)


@dataclass
class FunctionRef(Ref):
    name: str
    param_names: list[str]
    params: list[Ref] = None
    block: Block = None
    # we do not use `self.values`. maybe for function objects?
    return_values: list[Object] = field(default_factory=list, init=False)
    param_values: dict[str, list[Object]] = field(default_factory=dict, init=False)


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
    target: FunctionRef
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
class DeclareMethods(Instruction):
    target: Type
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


def counter():
    i = 0
    cache = {}
    def inner(obj):
        nonlocal i
        if obj in cache:
            return cache[obj]
        i += 1
        cache[obj] = i
        return i
    return inner


class IRPrinter:
    def __init__(self, test=False):
        self.blocks_seen = []
        self.blocks_to_add = []
        self.make_id = id_hash
        if test:
            self.make_id = counter()

    def _to_string(self, ir, show_type=True):
        string = ""
        match ir:
            case Program(block):
                block, _ = self._to_string(block)
                return block
            case Block(instrs):
                name = self.make_id(ir)
                if name in self.blocks_seen:
                    block = ""
                else:
                    self.blocks_seen.append(name)
                    instrs = '\n'.join(' ' + self._to_string(i) for i in instrs)
                    if not instrs:
                        instrs = " [empty]"
                    block = f"\n{name}:\n{instrs}"
                return block, name
            case Declare(ref):
                return f"DECLARE {self._to_string(ref)}"
            case DeclareMethods(typ, block):
                block, block_name = self._to_string(block)
                self.blocks_to_add.append(block)
                return f"DECLARE_METHODS {self._to_string(typ)} {block_name}"
            case Assign(target, value):
                return f"ASSIGN {self._to_string(target)} <- {self.to_string(value)}"
            case Return(value):
                return f"RETURN {self._to_string(value)}"
            case Branch(block):
                block, block_name = self._to_string(block)
                return f"BRANCH {block_name}{block}"
            case CBranch(condition, t_block, f_block):
                t_block, t_block_name = self._to_string(t_block)
                f_block, f_block_name = self._to_string(f_block)
                return (
                    f"CBRANCH {self._to_string(condition)} "
                    f"{t_block_name} {f_block_name}{t_block}{f_block}"
                )
            case StructTypeRef():
                string += f"{ir.name}{{{', '.join(ir.fields)}}}"
            case Type(name, value):
                return name
            case Constant(value):
                string += str(value)
            case FieldRef():
                return f"{self._to_string(ir.parent, show_type=False)}.{ir.name}"
            case FunctionRef():
                block, block_name = self._to_string(ir.block)
                self.blocks_to_add.append(block)
                string += f"{ir.name}({', '.join(ir.param_names)}) {block_name}"
            case Ref(name):
                string += name
            case Load(ref):
                string += f"LOAD({self._to_string(ref)})"
            case Call(ref, args):
                args = ', '.join(self._to_string(a) for a in args)
                string += f"CALL {self._to_string(ref)} ({args})"
            case Unary(op, rhs):
                string += f"{op}{self._to_string(rhs)}"
            case Binary(op, lhs, rhs):
                string += f"({self._to_string(lhs)} {op} {self.to_string(rhs)})"
            case _:
                assert False, ir

        if ir.checked_type is not None:
            string += f" [{self._to_string(ir.checked_type)}]"
        return string

    def to_string(self, ir):
        string = self._to_string(ir)
        # add deferred blocks
        for block in self.blocks_to_add:
            string += block
        return string
