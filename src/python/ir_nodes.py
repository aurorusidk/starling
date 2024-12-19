from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha1

from . import type_defs as types


def id_hash(obj):
    return sha1(str(id(obj)).encode("UTF-8")).hexdigest()[:4]


@dataclass
class Object:
    is_expr = False
    is_const = False
    typ: "Ref" = field(default=None, kw_only=True)


@dataclass
class Constant(Object):
    is_expr = True
    value: object


@dataclass
class Sequence(Object):
    is_expr = True
    elements: list[Object]


@dataclass
class Array(Sequence):
    pass


@dataclass
class Vector(Sequence):
    pass


@dataclass
class StructLiteral(Object):
    is_expr = True
    fields: dict[str, Object]


@dataclass
class Ref(Object):
    is_expr = True
    is_global = False
    is_const = False
    name: str
    values: list = field(default_factory=list, kw_only=True)
    members: dict = field(default_factory=dict, kw_only=True)
    methods: dict[str, Ref] = field(default_factory=dict, kw_only=True)


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
class IndexRef(Ref):
    parent: Ref
    index: Constant | Ref


@dataclass
class FieldRef(Ref):
    parent: Ref
    # mimic functions for methods
    return_values: list[Object] = field(default_factory=list, init=False)
    param_values: dict[str, list[Object]] = field(default_factory=dict, init=False)
    method: Ref = field(default=None, kw_only=True)


@dataclass
class SequenceType(Ref):
    elem_type: Ref


@dataclass
class ArrayType(SequenceType):
    length: int


@dataclass
class VectorType(SequenceType):
    pass


@dataclass
class FunctionSigRef(Ref):
    params: dict[str, Ref]
    return_type: Ref


@dataclass
class FunctionRef(Ref):
    params: list[Ref] = field(default=None, kw_only=True)
    block: Block = field(default=None, kw_only=True)
    # we do not use `self.values`. maybe for function objects?
    return_values: list[Object] = field(default_factory=list, init=False)
    param_values: dict[str, list[Object]] = field(default_factory=dict, init=False)
    builtin: bool = field(default=False, kw_only=True)


@dataclass
class MethodRef(FunctionRef):
    parent: Ref


@dataclass
class InterfaceRef(Ref):
    methods: dict[str, FunctionSigRef]


@dataclass
class StructRef(Ref):
    fields: dict[str, Ref]


@dataclass
class ConstRef(Ref):
    is_const = True
    value: Object


@dataclass
class Declare(Instruction):
    ref: Ref


@dataclass
class Assign(Instruction):
    target: Ref
    value: Object


@dataclass
class Load(Instruction):
    is_expr = True
    ref: Ref


@dataclass
class Call(Instruction):
    is_expr = True
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
    target: Ref
    block: Block


# this is the same as in the AST
# maybe we want to define the ops separately to remove the dependence on tokens
# for now the op will just be the op string
@dataclass
class Unary(Instruction):
    is_expr = True
    op: str
    rhs: Object


@dataclass
class Binary(Instruction):
    is_expr = True
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
        cache[obj] = str(i)
        return cache[obj]

    return inner


class IRPrinter:
    def __init__(self, test=False, show_types=True):
        self.show_types = show_types
        self.blocks_seen = []
        self.blocks_to_add = []
        self.make_id = id_hash
        if test:
            self.make_id = counter()

    def defer_block(self, block):
        prev_bta = self.blocks_to_add
        self.blocks_to_add = []
        block, block_name = self._to_string(block)
        prev_bta.append(block)
        prev_bta.extend(self.blocks_to_add)
        self.blocks_to_add = prev_bta
        return block, block_name

    def _to_string(self, ir, show_types=None):
        if show_types is None:
            show_types = self.show_types
        string = ""
        match ir:
            case Program(block):
                block, _ = self._to_string(block)
                string = block
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
                name = f"#{name}"
                return block, name
            case Declare(ref):
                string = f"DECLARE {self._to_string(ref)}"
                if isinstance(ref, StructRef) and show_types:
                    string += f" [{self._to_string(ref.checked)}]"
            case DeclareMethods(typ, block):
                block, block_name = self.defer_block(block)
                string = f"DECLARE_METHODS {self._to_string(typ)} {block_name}"
            case Assign(target, value):
                string = f"ASSIGN {self._to_string(target)} <- {self._to_string(value)}"
            case Return(value):
                string = f"RETURN {self._to_string(value)}"
            case Branch(block):
                block, block_name = self._to_string(block)
                string = f"BRANCH {block_name}{block}"
            case CBranch(condition, t_block, f_block):
                t_block, t_block_name = self._to_string(t_block)
                f_block, f_block_name = self._to_string(f_block)
                string = (
                    f"CBRANCH {self._to_string(condition)} "
                    f"{t_block_name} {f_block_name}{t_block}{f_block}"
                )
            case Constant(value):
                string += str(value)
            case Sequence(elements):
                if isinstance(ir, Array):
                    string += "arr"
                elif isinstance(ir, Vector):
                    string += "vec"
                string += "["
                string += ",".join(self._to_string(i, show_types=False) for i in elements)
                string += "]"
            case IndexRef():
                string = (
                    f"{self._to_string(ir.parent, show_types=False)}"
                    f"[{self._to_string(ir.index, show_types=False)}]"
                )
            case FieldRef():
                string = f"{self._to_string(ir.parent, show_types=False)}.{ir.name}"
            case FunctionSigRef():
                params = ', '.join(self._to_string(p) for p in ir.params.values())
                string += f"fn ({params}) -> {self._to_string(ir.return_type)}"
            case FunctionRef():
                block, block_name = self.defer_block(ir.block)
                string += f"{ir.name}({', '.join(ir.typ.params)}) {block_name}"
            case StructRef():
                fields = ', '.join(ir.fields)
                string += f"{ir.name}{{{fields}}}"
            case ConstRef(name, value):
                string += f"CONST {name} = {self._to_string(value)}"
                return string  # avoids duplication of type
            case StructLiteral():
                fields = ', '.join(self._to_string(f) for f in ir.fields.values())
                string = f"{{{fields}}}"
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
                string += f"({self._to_string(lhs)} {op} {self._to_string(rhs)})"
            case types.Type():
                return str(ir)
            case None:
                return "nil"
            case _:
                assert False, ir

        if ir.typ is not None and show_types:
            string += f" [{self._to_string(ir.typ)}]"
        return string

    def to_string(self, ir):
        string = self._to_string(ir)
        # add deferred blocks
        for block in self.blocks_to_add:
            string += block
        return string.lstrip()
