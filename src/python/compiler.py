import logging

from .lexer import TokenType as T
from .type_checker import Scope
from . import ast_nodes as ast


class Compiler:
    def __init__(self):
        self.scope = Scope(None)
        # TODO: builtins

    def eval_node(self, node):
        match node:
            case ast.Literal(tok):
                return self.eval_literal(tok, node.typ)
            case ast.Identifier(name):
                return self.eval_identifier(name)
            case ast.RangeExpr(start, end):
                return self.eval_range_expr(start, end)
            case ast.GroupExpr(expr):
                return self.eval_group_expr(expr)
            case ast.CallExpr(target, args):
                return self.eval_call_expr(target, args)
            case ast.IndexExpr(target, index):
                return self.eval_index_expr(target, index)
            case ast.SelectorExpr(target, name):
                return self.eval_selector_expr(target, name)
            case ast.UnaryExpr(op, rhs):
                return self.eval_unary_expr(op, rhs)
            case ast.BinaryExpr(op, lhs, rhs):
                return self.eval_binary_expr(op, lhs, rhs)

            case ast.TypeName(name):
                return self.eval_type(name)
            case ast.ArrayType(length, elem_type):
                return self.eval_array_type(length, elem_type)

            case ast.Block(stmts):
                return self.eval_block(stmts)
            case ast.DeclrStmt(declr):
                return self.eval_node(declr)
            case ast.ExprStmt(expr):
                return self.eval_node(expr)
            case ast.IfStmt(condition, if_block, else_block):
                return self.eval_if_stmt(condition, if_block, else_block)
            case ast.WhileStmt(condition, block):
                return self.eval_while_stmt(condition, block)
            case ast.ReturnStmt(value):
                return self.eval_return_stmt(value)
            case ast.AssignmentStmt(target, value):
                return self.eval_assignment_stmt(target, value)

            case ast.FunctionDeclr(signature, block):
                return self.eval_function_declr(
                    signature, node.checked_type, block
                )
            case ast.StructDeclr(name, fields):
                return self.eval_struct_declr(name, node.checked_type, fields)
            case ast.InterfaceDeclr(name, methods):
                return self.eval_interface_declr(
                    name, node.checked_type, methods
                )
            case ast.ImplDeclr(target, interface, methods):
                return self.eval_impl_declr(
                    target, interface, node.checked_type, methods
                )
            case ast.VariableDeclr(name, _, value):
                return self.eval_variable_declr(name, node.checked_type, value)

            case ast.Program(declrs):
                return self.eval_program(declrs)

            case _:
                assert False, f"Unreachable: {node}"

    def eval_program(self, declrs):
        logging.debug(f"{declrs}")
        raise NotImplementedError

    def eval_function_inst(self, signature, ftype, block, is_method=False):
        logging.debug(f"{signature}")
        raise NotImplementedError

    def eval_function_declr(self, signature, ftype, block):
        raise NotImplementedError

    def eval_struct_declr(self, name, typ, members):
        logging.debug(f"{name}, {members}")
        raise NotImplementedError

    def eval_interface_declr(self, name, typ, methods):
        logging.debug(f"{name}, {methods}")
        raise NotImplementedError

    def eval_impl_declr(self, target, interface, typ, methods):
        logging.debug(f"{target}<{interface}>, {methods}")
        raise NotImplementedError

    def eval_variable_declr(self, name, typ, value):
        raise NotImplementedError

    def eval_type(self, name):
        raise NotImplementedError

    def eval_array_type(self, length, elem_type):
        raise NotImplementedError

    def eval_block(self, stmts):
        raise NotImplementedError

    def eval_if_stmt(self, condition, if_block, else_block):
        raise NotImplementedError

    def eval_while_stmt(self, condition, while_block):
        raise NotImplementedError

    def eval_return_stmt(self, value):
        raise NotImplementedError

    def eval_assignment_stmt(self, target, value):
        raise NotImplementedError

    def eval_binary_expr(self, op, left, right):
        left = self.eval_node(left)
        right = self.eval_node(right)
        assert left.typ == right.typ, "Type coercion not implemented"
        match op.typ:
            case T.PLUS:
                return self.eval_add(left, right)
            case T.MINUS:
                return self.eval_sub(left, right)
            case T.STAR:
                return self.eval_mul(left, right)
            case T.SLASH:
                return self.eval_div(left, right)
            case T.EQUALS_EQUALS:
                return self.eval_equal(left, right)
            case T.BANG_EQUALS:
                return self.eval_not_equal(left, right)
            case T.LESS_THAN:
                return self.eval_less_than(left, right)
            case T.GREATER_THAN:
                return self.eval_greater_than(left, right)
            case T.LESS_EQUALS:
                return self.eval_less_than_equal(left, right)
            case T.GREATER_EQUALS:
                return self.eval_greater_than_equal(left, right)
            case _:
                assert False, f"Unimplemented operator: {op.typ}"

    def eval_add(self, left, right):
        raise NotImplementedError

    def eval_sub(self, left, right):
        raise NotImplementedError

    def eval_mul(self, left, right):
        raise NotImplementedError

    def eval_div(self, left, right):
        raise NotImplementedError

    def eval_equal(self, left, right):
        raise NotImplementedError

    def eval_not_equal(self, left, right):
        raise NotImplementedError

    def eval_less_than(self, left, right):
        raise NotImplementedError

    def eval_greater_than(self, left, right):
        raise NotImplementedError

    def eval_less_than_equal(self, left, right):
        raise NotImplementedError

    def eval_greater_than_equal(self, left, right):
        raise NotImplementedError

    def eval_unary_expr(self, op, right):
        right = self.eval_node(right)
        match op.typ:
            case T.BANG:
                return self.eval_not(right)
            case T.MINUS:
                return self.eval_neg(right)
            case _:
                assert False, f"Unimplemented operator: {op.typ}"

    def eval_not(self, right):
        raise NotImplementedError

    def eval_neg(self, right):
        raise NotImplementedError

    def eval_selector_expr(self, target, name):
        logging.debug(f"{target}.{name}")
        raise NotImplementedError

    def eval_index_expr(self, target, index):
        raise NotImplementedError

    def eval_call_expr(self, callee, args):
        logging.debug("evaluating call")
        raise NotImplementedError

    def eval_literal(self, value, typ):
        raise NotImplementedError

    def eval_identifier(self, name):
        raise NotImplementedError

    def eval_group_expr(self, expr):
        return self.eval_node(expr)

    def eval_range_expr(self, start, end):
        raise NotImplementedError
