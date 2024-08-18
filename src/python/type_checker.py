from enum import Enum
import logging

from . import ir_nodes as ir
from . import builtin
from . import type_defs as types


progress = Enum("progress", [
    "COMPLETED", "UPDATING", "EMPTY",
])


unary_op_preds = {
    '-': types.is_numeric,
    '!': types.is_bool,
}

binary_op_preds = {
    '+': lambda t: types.is_numeric(t) or types.is_string(t),
    '-': types.is_numeric,
    '*': types.is_numeric,
    '/': types.is_numeric,
}


def is_comparison_op(op):
    return op in (
        '>', '<', '>=', '<=', '==', '!=',
    )


class DeferChecking(Exception):
    pass


class TypeChecker:
    def __init__(self, error_handler=None):
        # used to infer return types
        self.function = None
        self.error_handler = error_handler
        self.deferred = []

    def error(self, msg):
        if self.error_handler is None:
            assert False, msg

        self.error_handler(msg)

    def match_types(self, lhs, rhs):
        if types.is_basic(lhs):
            return lhs == rhs \
                or types.is_numeric(lhs) and types.is_numeric(rhs)
        else:
            assert False, f"Unimplemented: cannot match types {lhs}, {rhs}"

    def update_types(self, target, new):
        final = new
        if target is not None and new is not None:
            assert type(new) is type(target), f"{target} doesn't match {new}"
        if new is None:
            return target
        match target:
            case None:
                pass
            case types.BasicType():
                assert target == new
            case types.FunctionType():
                r_type = self.update_types(target.return_type, new.return_type)
                assert len(target.param_types) == len(new.param_types)
                p_types = []
                for target_p, new_p in zip(target.param_types, new.param_types):
                    p_types.append(self.update_types(target_p, new_p))
                final = types.FunctionType(r_type, p_types)
            case types.StructType():
                for field in target.fields:
                    ftype = target.fields[field]
                    new_ftype = new.fields[field]
                    target.fields[field] = self.update_types(ftype, new_ftype)
            case _:
                assert False, f"Unexpected type {target}"
        return final

    def get_binary_numeric(self, lhs, rhs):
        if builtin.types["float"] in (lhs.typ, rhs.typ):
            return builtin.types["float"]
        elif builtin.types["frac"] in (lhs.typ, rhs.typ):
            return builtin.types["frac"]
        elif builtin.types["int"] in (lhs.typ, rhs.typ):
            return builtin.types["int"]
        else:
            assert False, f"Unimplemented: cannot get numeric" \
                f"from {lhs.typ}, {rhs.typ}"

    def check(self, node):
        if node.progress == progress.UPDATING:
            return
        node.progress = progress.UPDATING
        try:
            match node:
                case ir.Program(block):
                    self.check(block)
                    while self.deferred:
                        node = self.deferred.pop(0)
                        node.progress = progress.EMPTY
                        try:
                            self.check(node)
                        except DeferChecking:
                            # probably unable to check this
                            self.deferred.remove(node)
                    node.progress = progress.COMPLETED
                case ir.Ref():
                    self.check_ref(node)
                case ir.Instruction():
                    self.check_instr(node)
                case ir.Object():
                    # misc
                    self.check_object(node)
                case _:
                    assert False, f"Unexpected node {node}"
        except DeferChecking:
            self.deferred.append(node)
            if node.is_expr:
                raise DeferChecking("Propagating expr defer")
        else:
            if node.progress != progress.COMPLETED:
                raise DeferChecking(f"Incomplete type checking for {type(node)} node")

    def check_ref(self, node):
        if node.type_hint is not None and node.checked_type is None:
            # this can make the type hint appear wrong
            # as the checked type now shares an object with the type hint
            # probably not an issue though?
            node.checked_type = node.type_hint
        for value in node.values:
            self.check(value)
            node.checked_type = self.update_types(node.checked_type, value.checked_type)
        match node:
            case ir.FunctionRef():
                if node.checked_type is None:
                    node.checked_type = types.FunctionType()
                typ = node.checked_type
                for value in node.return_values:
                    self.check(value)
                    typ.return_type = self.update_types(typ.return_type, value.checked_type)

                param_types = []
                for i, param_name in enumerate(node.param_names):
                    values = node.param_values.get(param_name, [])
                    new_type = node.checked_type.param_types[i]
                    for value in values:
                        self.check(value)
                        new_type = self.update_types(new_type, value.checked_type)
                    param_types.append(new_type)
                typ.param_types = param_types
                self.check(node.block)
            case ir.StructRef():
                pass
            case ir.FieldRef():
                self.check(node.parent)
                field = None
                if isinstance(node.parent.checked_type, types.StructType):
                    field = node.parent.checked_type.fields.get(node.name)
                method = node.parent.checked_type.methods.get(node.name)
                if method:
                    for name, value in zip(method.param_names, node.param_values):
                        prev_values = method.param_values.get(name, [])
                        prev_values.append(value)
                        method.param_values[name] = prev_values
                    param_types = method.checked_type.param_types
                    for i, (param, value) in enumerate(zip(method.params, node.param_values)):
                        self.check(value)
                        param.values.append(value)
                        self.check(param)
                    self.check(method)
                    method = method.checked_type
                value = field or method
                assert value, f"{node.name} is not a field or method of {node.parent.name}"
                assert not (field and method)
                node.checked_type = value
            case ir.Ref():
                pass
            case _:
                assert False, f"Unexpected ref {node}"

        if node.checked_type is not None:
            node.progress = progress.COMPLETED
        else:
            node.progress = progress.EMPTY
            raise DeferChecking

    def check_instr(self, node):
        match node:
            case ir.Declare(ref):
                self.check(ref)
            case ir.DeclareMethods(typ, block):
                if isinstance(typ, types.StructType):
                    assert all(m not in typ.fields for m in typ.methods)
                for method in typ.methods.values():
                    self.check(method)
                self.check(block)
            case ir.Assign(ref, value):
                self.check(ref)
                self.check(value)
            case ir.Load(ref):
                self.check(ref)
                node.checked_type = ref.checked_type
            case ir.Call(ref, args):
                self.check(ref)
                assert len(args) == len(ref.checked_type.param_types)
                for i, arg in enumerate(args):
                    self.check(arg)
                    ref.checked_type.param_types[i] = self.update_types(ref.checked_type.param_types[i], arg.checked_type)
                node.checked_type = ref.checked_type.return_type
            case ir.Return(value):
                self.check(value)
            case ir.Branch(block):
                self.check(block)
            case ir.CBranch(condition, t_block, f_block):
                self.check(condition)
                if condition.checked_type != builtin.types["bool"]:
                    self.error("Branch condition must be a boolean")
                self.check(t_block)
                self.check(f_block)
            case ir.Binary():
                self.check_binary(node)
            case ir.Unary():
                self.check_unary(node)
            case _:
                assert False, f"Unexpected instruction {node}"
        node.progress = progress.COMPLETED

    def check_binary(self, node):
        self.check(node.lhs)
        self.check(node.rhs)

        if node.lhs.checked_type != node.rhs.checked_type:
            self.error(f"Mismatched types for {node.lhs} and {node.rhs}")
        if is_comparison_op(node.op):
            node.checked_type = builtin.types["bool"]
            return

        pred = binary_op_preds[node.op]
        if not pred(node.lhs.checked_type):
            self.error(f"Unsupported op '{node.op}' on {node.lhs.checked_type}")
        elif node.op == '/':
            node.checked_type = builtin.types["float"]
        else:
            node.checked_type = node.lhs.checked_type

    def check_unary(self, node):
        self.check(node.rhs)

        pred = unary_op_preds[node.op]
        if not pred(node.rhs.checked_type):
            self.error(f"Unsupported op {node.op} on {node.rhs.checked_type}")
        else:
            node.checked_type = node.rhs.checked_type

    def check_object(self, node):
        match node:
            case ir.Block(instrs):
                for instr in instrs:
                    self.check(instr)
            case ir.Constant():
                pass
            case _:
                assert False, f"Unexpected object {node}"
        node.progress = progress.COMPLETED


if __name__ == "__main__":
    from . import lexer
    from . import parser
    from . import ir as noder

    logging.basicConfig(format="%(levelname)s: %(message)s")
    logging.getLogger().setLevel(logging.DEBUG)
    with open("input.txt") as f:
        src = f.read()
    toks = lexer.tokenise(src)
    tree = parser.parse(toks)
    iir = noder.IRNoder().make(tree)
    print(iir)
    print(ir.IRPrinter().to_string(iir))
    tc = TypeChecker(iir)
    tc.check(iir)
    print(iir)
    print(ir.IRPrinter().to_string(iir))
