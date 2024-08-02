import logging

from .scope import Scope
from . import ast_nodes as ast
from . import type_defs as types
from . import builtin
from . import ir_nodes as ir


class IRNoder:
    def __init__(self):
        self.scope = Scope(None)
        self.scope.name_map |= builtin.types

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
                typ = self.scope.lookup(name.value)
                assert isinstance(typ, types.Type)
                return typ
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
            case ast.DeclrStmt(declr):
                return self.make_declr(declr)
            case ast.ExprStmt(expr):
                return self.make_expr(declr)
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
                return self.make_variable_declr(name, typ, value)
            case _:
                assert False, f"Unexpected declr {node}"

    def make_function_signature(self, name, return_type, params):
        if return_type is not None:
            return_type = self.make_type(return_type)

        param_names = []
        param_types = []
        for param in params:
            param_names.append(param.name.value)
            ptype = None
            if param.typ is not None:
                ptype = self.make_type(param.typ)
            param_types.append(ptype)
        type_hint = types.FunctionType(return_type, param_types)
        return ir.FunctionSignatureRef(name.value, param_names, type_hint)

    def make_function_declr(self, signature, block):
        sig = self.make_type(signature)
        self.scope = Scope(self.scope)
        for pname, ptype in zip(sig.params, sig.type_hint.param_types):
            ref = ir.Ref(pname, ptype)
            self.scope.declare(pname, ref)
        block = self.make_stmt(block)
        func_scope = self.scope
        self.scope = self.scope.parent
        return ir.DefFunc(sig, block, func_scope)

    def make_variable_declr(self, name, typ, value):
        name = name.value
        type_hint = None
        if typ is not None:
            type_hint = self.make_type(typ)
        ref = ir.Ref(name, type_hint)
        self.scope.declare(name, ref)
        instr = ir.Declare(ref)
        if value is not None:
            value = self.make_expr(value)
            ref.values.append(value)
            assign_instr = ir.Assign(ref, value)
            instr = ir.MultiInstr(instr, assign_instr)
        return instr


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

