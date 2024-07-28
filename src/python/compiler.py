import logging

from .lexer import TokenType as T
from .type_checker import Scope
from . import ast_nodes as ast


class Compiler:
    def __init__(self):
        self.scope = Scope(None)
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
        raise NotImplementedError

    def build_function_inst(self, signature, ftype, block, is_method=False):
        logging.debug(f"{signature}")
        raise NotImplementedError

    def build_function_declr(self, signature, ftype, block):
        raise NotImplementedError

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
        raise NotImplementedError

    def build_if_stmt(self, condition, if_block, else_block):
        raise NotImplementedError

    def build_while_stmt(self, condition, while_block):
        raise NotImplementedError

    def build_return_stmt(self, value):
        raise NotImplementedError

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
        raise NotImplementedError

    def build_identifier(self, name):
        raise NotImplementedError

    def build_group_expr(self, expr):
        return self.build_node(expr)

    def build_range_expr(self, start, end):
        raise NotImplementedError
