import logging

from . import ast_nodes as ast
from . import type_defs as types
from . import ir_nodes as ir


class IRNoder:
    def __init__(self):
        pass

    def make(self, node):
        match node:
            case ast.Expr():
                self.make_expr(node)
            case ast.Type():
                self.make_type(node)
            case ast.Stmt():
                self.make_stmt(node)
            case ast.Declr():
                self.make_declr(node)
            case ast.Program(declrs):
                declrs = [self.make_declr(d) for d in declrs]
                return ir.Program(declrs)
            case _:
                assert False, f"Unexpected node {node}"

    def make_expr(self, node):
        match node:
            case ast.Literal(tok):
                raise NotImplementedError
            case ast.Identifier(name):
                raise NotImplementedError
            case ast.RangeExpr(start, end):
                raise NotImplementedError
            case ast.GroupExpr(expr):
                raise NotImplementedError
            case ast.CallExpr(target, args):
                raise NotImplementedError
            case ast.IndexExpr(target, index):
                raise NotImplementedError
            case ast.SelectorExpr(target, name):
                raise NotImplementedError
            case ast.UnaryExpr():
                raise NotImplementedError
            case ast.BinaryExpr():
                raise NotImplementedError
            case _:
                assert False, f"Unexpected expr {node}"

    def make_type(self, node):
        match node:
            case ast.TypeName(name):
                raise NotImplementedError
            case ast.ArrayType(length, elem_type):
                raise NotImplementedError
            case ast.FunctionSignature(name, return_type, params):
                return self.make_function_signature(name, return_type, params)
            case _:
                assert False, f"Unexpected type {node}"

    def make_stmt(self, node):
        match node:
            case ast.Block(stmts):
                stmts = [self.make_stmt(s) for s in stmts]
                return ir.Block(stmts)
                for stmt in stmts:
                    self.make_stmt(stmt)
            case ast.DeclrStmt(declr):
                self.make_declr(declr)
            case ast.ExprStmt(expr):
                self.make_expr(declr)
            case ast.IfStmt(condition, if_block, else_block):
                raise NotImplementedError
            case ast.WhileStmt(condition, block):
                raise NotImplementedError
            case ast.ReturnStmt(value):
                raise NotImplementedError
            case ast.AssignmentStmt(target, value):
                raise NotImplementedError
            case _:
                assert False, f"Unexpected stmt {node}"

    def make_declr(self, node):
        match node:
            case ast.FunctionDeclr(signature, block):
                return self.make_function_declr(signature, block)
            case ast.StructDeclr(name, fields):
                raise NotImplementedError
            case ast.InterfaceDeclr(name, methods):
                raise NotImplementedError
            case ast.ImplDeclr(target, interface, methods):
                raise NotImplementedError
            case ast.VariableDeclr(name, typ, value):
                raise NotImplementedError
            case _:
                assert False, f"Unexpected declr {node}"

    def make_function_signature(self, name, return_type, params):
        if return_type is not None:
            return_type = self.make_type(return_type)

        param_names = []
        param_types = []
        for param in params:
            param_names.append(p.name.value)
            ptype = None
            if p.typ is not None:
                ptype = self.make_type(p.typ)
            param_types.append(ptype)
        type_hint = types.FunctionType(return_type, param_types)
        return ir.FunctionSignature(name.value, param_names, type_hint)

    def make_function_declr(self, signature, block):
        sig = self.make_type(signature)
        block = self.make_stmt(block)
        return ir.Function(sig, block)


if __name__ == "__main__":
    import sys

    from . import lexer
    from . import parser

    logging.basicConfig(format="%(levelname)s: %(message)s")
    logging.getLogger().setLevel(logging.DEBUG)

    assert len(sys.argv) == 2, "no input file"
    with open(sys.argv[1]) as f:
        src = f.read()
    toks = lexer.tokenise(src)
    tree = parser.parse(toks)
    noder = IRNoder()
    ir = noder.make(tree)
    print(ir)

