import logging

from .lexer import TokenType as T
from .type_checker import Scope
from . import ast_nodes as ast
from . import builtin
from llvmlite import ir


type_map = {
    builtin.types["int"]: ir.IntType(32),
    builtin.types["float"]: ir.DoubleType(),
    builtin.types["bool"]: ir.IntType(1),
}


class Compiler:
    def __init__(self):
        self.scope = Scope(None)
        self.module = ir.Module()
        self.builder = None
        # TODO: builtins

    def build_node(self, node):
        match node:
            case ast.Literal(tok):
                return self.build_literal(tok, node.typ)
            case ast.Identifier(name):
                return self.build_identifier(name)
            case ast.RangeExpr(start, end):
                return self.build_range_expr(start, end)
            case ast.GroupExpr(expr):
                return self.build_group_expr(expr)
            case ast.CallExpr(target, args):
                return self.build_call_expr(target, args)
            case ast.IndexExpr(target, index):
                return self.build_index_expr(target, index)
            case ast.SelectorExpr(target, name):
                return self.build_selector_expr(target, name)
            case ast.UnaryExpr(op, rhs):
                return self.build_unary_expr(op, rhs)
            case ast.BinaryExpr(op, lhs, rhs):
                return self.build_binary_expr(op, lhs, rhs)

            case ast.TypeName(name):
                return self.build_type(name)
            case ast.ArrayType(length, elem_type):
                return self.build_array_type(length, elem_type)

            case ast.Block(stmts):
                return self.build_block(stmts)
            case ast.DeclrStmt(declr):
                return self.build_node(declr)
            case ast.ExprStmt(expr):
                return self.build_node(expr)
            case ast.IfStmt(condition, if_block, else_block):
                return self.build_if_stmt(condition, if_block, else_block)
            case ast.WhileStmt(condition, block):
                return self.build_while_stmt(condition, block)
            case ast.ReturnStmt(value):
                return self.build_return_stmt(value)
            case ast.AssignmentStmt(target, value):
                return self.build_assignment_stmt(target, value)

            case ast.FunctionDeclr(signature, block):
                return self.build_function_declr(
                    signature, node.checked_type, block
                )
            case ast.StructDeclr(name, fields):
                return self.build_struct_declr(name, node.checked_type, fields)
            case ast.InterfaceDeclr(name, methods):
                return self.build_interface_declr(
                    name, node.checked_type, methods
                )
            case ast.ImplDeclr(target, interface, methods):
                return self.build_impl_declr(
                    target, interface, node.checked_type, methods
                )
            case ast.VariableDeclr(name, _, value):
                return self.build_variable_declr(name, node.checked_type, value)

            case ast.Program(declrs):
                return self.build_program(declrs)

            case _:
                assert False, f"Unreachable: {node}"

    def build_program(self, declrs):
        logging.debug(f"{declrs}")
        for declr in declrs:
            self.build_node(declr)

    def build_function_inst(self, signature, ftype, block, is_method=False):
        logging.debug(f"{signature}")
        if is_method:
            raise NotImplementedError
        else:
            return_type = type_map[ftype.return_type]
            param_types = (type_map[p] for p in ftype.param_types)

            ftype = ir.FunctionType(return_type, param_types)
            func = ir.Function(self.module, ftype, name=signature.name.value)
            return func

    def build_function_declr(self, signature, ftype, block):
        func = self.build_function_inst(signature, ftype, block)
        fblock = func.append_basic_block("entry")
        prev_builder = self.builder
        self.builder = ir.IRBuilder(fblock)

        for arg, param in zip(func.args, signature.params):
            self.scope.declare(param.name, arg)
        self.build_node(block)

        self.builder = prev_builder

    def build_struct_declr(self, name, typ, members):
        logging.debug(f"{name}, {members}")
        raise NotImplementedError

    def build_interface_declr(self, name, typ, methods):
        logging.debug(f"{name}, {methods}")
        raise NotImplementedError

    def build_impl_declr(self, target, interface, typ, methods):
        logging.debug(f"{target}<{interface}>, {methods}")
        raise NotImplementedError

    def build_variable_declr(self, name, typ, value):
        raise NotImplementedError

    def build_type(self, name):
        raise NotImplementedError

    def build_array_type(self, length, elem_type):
        raise NotImplementedError

    def build_block(self, stmts):
        for stmt in stmts:
            self.build_node(stmt)

    def build_if_stmt(self, condition, if_block, else_block):
        # TODO: Fully implement expression building
        condition = self.build_node(condition)

        if else_block is None:
            with self.builder.if_then(condition):
                self.build_node(if_block)
        else:
            with self.builder.if_else(condition) as (then, otherwise):
                with then:
                    self.build_node(if_block)
                with otherwise:
                    self.build_node(else_block)

    def build_while_stmt(self, condition, while_block):
        raise NotImplementedError

    def build_return_stmt(self, value):
        value = self.build_node(value)
        self.builder.ret(value)

    def build_assignment_stmt(self, target, value):
        raise NotImplementedError

    def build_binary_expr(self, op, left, right):
        left = self.build_node(left)
        right = self.build_node(right)
        assert left.typ == right.typ, "Type coercion not implemented"
        match op.typ:
            case T.PLUS:
                return self.build_add(left, right)
            case T.MINUS:
                return self.build_sub(left, right)
            case T.STAR:
                return self.build_mul(left, right)
            case T.SLASH:
                return self.build_div(left, right)
            case T.EQUALS_EQUALS:
                return self.build_equal(left, right)
            case T.BANG_EQUALS:
                return self.build_not_equal(left, right)
            case T.LESS_THAN:
                return self.build_less_than(left, right)
            case T.GREATER_THAN:
                return self.build_greater_than(left, right)
            case T.LESS_EQUALS:
                return self.build_less_than_equal(left, right)
            case T.GREATER_EQUALS:
                return self.build_greater_than_equal(left, right)
            case _:
                assert False, f"Unimplemented operator: {op.typ}"

    def build_add(self, left, right):
        raise NotImplementedError

    def build_sub(self, left, right):
        raise NotImplementedError

    def build_mul(self, left, right):
        raise NotImplementedError

    def build_div(self, left, right):
        raise NotImplementedError

    def build_equal(self, left, right):
        raise NotImplementedError

    def build_not_equal(self, left, right):
        raise NotImplementedError

    def build_less_than(self, left, right):
        raise NotImplementedError

    def build_greater_than(self, left, right):
        raise NotImplementedError

    def build_less_than_equal(self, left, right):
        raise NotImplementedError

    def build_greater_than_equal(self, left, right):
        raise NotImplementedError

    def build_unary_expr(self, op, right):
        right = self.build_node(right)
        match op.typ:
            case T.BANG:
                return self.build_not(right)
            case T.MINUS:
                return self.build_neg(right)
            case _:
                assert False, f"Unimplemented operator: {op.typ}"

    def build_not(self, right):
        raise NotImplementedError

    def build_neg(self, right):
        raise NotImplementedError

    def build_selector_expr(self, target, name):
        logging.debug(f"{target}.{name}")
        raise NotImplementedError

    def build_index_expr(self, target, index):
        raise NotImplementedError

    def build_call_expr(self, callee, args):
        logging.debug("building call")
        raise NotImplementedError

    def build_literal(self, value, typ):
        if typ == builtin.types["int"]:
            return ir.Constant(ir.IntType(32), int(value.lexeme))
        elif typ == builtin.types["float"]:
            return ir.Constant(ir.DoubleType(), float(value.lexeme))
        elif typ == builtin.types["bool"]:
            return ir.Constant(ir.IntType(1), value.lexeme == "true")
        else:
            raise NotImplementedError

    def build_identifier(self, name):
        raise NotImplementedError

    def build_group_expr(self, expr):
        return self.build_node(expr)

    def build_range_expr(self, start, end):
        raise NotImplementedError
