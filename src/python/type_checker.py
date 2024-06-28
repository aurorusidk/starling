from dataclasses import dataclass

import ast_nodes as ast
import builtin


class Scope:
    def __init__(self, parent):
        self.parent = parent
        self.children = []
        self.name_map = {}

    def strict_lookup(self, name):
        return self.name_map.get(name)

    def lookup(self, name):
        s = self
        while not (val := s.strict_lookup(name)):
            s = s.parent
            if not s:
                return None
        return val


class TypeChecker:
    def __init__(self, root):
        self.scope = Scope(None)
        self.root = root

    def check(self, node):
        match node:
            case ast.Expr():
                self.check_expr(node)
            case ast.Type():
                self.check_type(node)
            case ast.Stmt():
                self.check_stmt(node)
            case ast.Declr():
                self.check_declr(node)
            case ast.Program(declrs):
                for declr in declrs:
                    self.check(declr)
            case _:
                assert False, f"Unexpected node {node}"

    def check_expr(self, node):
        match node:
            case ast.Literal(tok):
                pass
            case ast.Identifier(name):
                pass
            case ast.RangeExpr(start, end):
                pass
            case ast.GroupExpr(value):
                pass
            case ast.CallExpr(target, args):
                target = self.check(target)
                args = [self.check_expr(arg) for arg in args]
                # TODO: check args against signature in target
            case ast.IndexExpr(target, index):
                pass
            case ast.SelectorExpr(target, name):
                pass
            case ast.UnaryExpr(op, rhs):
                pass
            case ast.BinaryExpr(op, lhs, rhs):
                pass
            case _:
                assert False, f"Unreachable: could not match expr {node}"

    def check_type(self, node):
        match node:
            case ast.TypeName(value):
                pass
            case ast.ArrayType(length, elem_t):
                pass
            case _:
                assert False, f"Unreachable: could not match type {node}"

    def check_stmt(self, node):
        match node:
            case ast.Block(stmts):
                for stmt in stmts:
                    self.check_stmt(stmt)
            case ast.DeclrStmt(declr):
                self.check_declr(declr)
            case ast.ExprStmt(expr):
                self.check_expr(expr)
            case ast.IfStmt(condition, if_block, else_block):
                pass
            case ast.WhileStmt(condition, block):
                pass
            case ast.ReturnStmt(value):
                pass
            case ast.AssignmentStmt(target, value):
                pass
            case _:
                assert False, f"Unreachable: could not match stmt {node}"

    def check_declr(self, node):
        match node:
            case ast.FunctionDeclr(name, return_t, params, block):
                # TODO: add FunctionType to scope and allow for type inference
                self.check(block)
            case ast.VariableDeclr(name, typ, value):
                pass
            case _:
                assert False, f"Unreachable: could not match declr {node}"



if __name__ == "__main__":
    import lexer, parser
    with open("input.txt") as f:
        src = f.read()
    toks = lexer.tokenise(src)
    tree = parser.parse(toks)
    tc = TypeChecker(tree)
    tc.check(tree)
