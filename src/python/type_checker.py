from enum import Enum
import logging

from .lexer import TokenType as T
from . import ir_nodes as ir
from . import builtin
from . import type_defs as types


progress = Enum("progress", [
    "COMPLETED", "UPDATING", "EMPTY",
])


unary_op_preds = {
    T.MINUS: types.is_numeric,
    T.BANG: types.is_bool,
}

binary_op_preds = {
    T.PLUS: lambda t: types.is_numeric(t) or types.is_string(t),
    T.MINUS: types.is_numeric,
    T.STAR: types.is_numeric,
    T.SLASH: types.is_numeric,
}


def is_comparison_op(op):
    return op.typ in (
        T.GREATER_THAN, T.LESS_THAN, T.GREATER_EQUALS, T.LESS_EQUALS,
        T.EQUALS_EQUALS, T.BANG_EQUALS,
    )


class TypeChecker:
    def __init__(self, iir, error_handler=None):
        self.ir = iir
        # used to infer return types
        self.function = None
        self.error_handler = error_handler

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
        match target:
            case None:
                pass
            case types.BasicType():
                assert target == new
            case type.FunctionType():
                r_type = self.update_types(target.return_type, new.return_type)
                assert len(target.param_types) == len(new.param_types)
                p_types = []
                for target_p, new_p in zip(target.param_types, new.param_types):
                    p_types.append(self.update_types(target_p, new_p))
                final = types.FunctionType(r_type, p_types)
            case _:
                assert False, "Unexpected type {target}"
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
        match node:
            case ir.Ref():
                self.check_ref(node)
            case ir.Instruction():
                self.check_instr(node)
            case ir.Program(instrs):
                for instr in instrs:
                    self.check_instr(instr)
            case ir.Object():
                # misc
                self.check_object(node)
            case _:
                assert False, f"Unexpected node {node}"

    def check_ref(self, node):
        if node.type_hint is not None and node.checked_type is None:
            node.checked_type = node.type_hint
        for value in node.values:
            self.check(value)
            node.checked_type = self.update_types(node.checked_type, value.checked_type)
        match node:
            case ir.FunctionSignatureRef():
                if node.checked_type is None:
                    node.checked_type = types.FunctionType()
                for value in node.return_values:
                    self.check(value)
                    node.checked_type.return_type = self.update_types(node.checked_type.return_type, value.checked_type)
                pass
            case ir.StructTypeRef():
                pass
            case ir.FieldRef():
                pass
            case ir.Ref():
                pass
            case _:
                assert False, f"Unexpected ref {node}"

        node.progress = progress.COMPLETED

    def check_instr(self, node):
        match node:
            case ir.Declare(ref):
                self.check(ref)
            case ir.Assign(ref, value):
                self.check(ref)
                self.check(value)
            case ir.Return(value):
                self.check(value)
            case ir.Branch(block):
                self.check(block)
            case ir.CBranch(condition, t_block, f_block):
                self.check(condition)
                self.check(t_block)
                self.check(f_block)
            case ir.DefFunc(target, block, scope):
                self.check(target)
                self.check(block)
            case ir.Binary(op, lhs, rhs):
                self.check(lhs)
                self.check(rhs)
            case ir.Unary(op, rhs):
                self.check(rhs)
            case _:
                assert False, f"Unexpected instruction {node}"

    def check_object(self, node):
        match node:
            case ir.Block(instrs) | ir.Program(instrs):
                for instr in instrs:
                    self.check(instr)
            case ir.Constant():
                node.progress = progress.COMPLETED
            case _:
                assert False, f"Unexpected object {node}"


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
