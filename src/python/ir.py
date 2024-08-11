from fractions import Fraction
import logging

from .lexer import TokenType as T
from .scope import Scope
from . import ast_nodes as ast
from . import type_defs as types
from . import builtin
from . import ir_nodes as ir


class IRNoder:
    def __init__(self):
        self.scope = Scope(None)
        self.scope.name_map |= builtin.types
        self.exprs = []
        self.block = ir.Block([])
        self.current_func = None

    @property
    def instrs(self):
        return self.block.instrs

    def make(self, node):
        match node:
            case ast.Expr():
                return self.make_expr(node)
            case ast.Type():
                self.make_type(node)
            case ast.Stmt():
                self.make_stmt(node)
            case ast.Declr():
                self.make_declr(node)
            case ast.Program(declrs):
                block = self.block
                for declr in declrs:
                    self.make_declr(declr)
                return ir.Program(block.instrs)
            case _:
                assert False, f"Unexpected node {node}"

    def make_expr(self, node):
        match node:
            case ast.Literal(tok):
                return self.make_literal(tok)
            case ast.Identifier(name):
                return self.make_identifier(name)
            case ast.RangeExpr(start, end):
                raise NotImplementedError
            case ast.GroupExpr(expr):
                return self.make_expr(expr)
            case ast.CallExpr(target, args):
                return self.make_call_expr(target, args)
            case ast.IndexExpr(target, index):
                raise NotImplementedError
            case ast.SelectorExpr(target, name):
                return self.make_selector_expr(target, name)
            case ast.UnaryExpr(op, rhs):
                return self.make_unary_expr(op, rhs)
            case ast.BinaryExpr(op, lhs, rhs):
                return self.make_binary_expr(op, lhs, rhs)
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
                block = ir.Block([])
                self.block = block
                for stmt in stmts:
                    self.make_stmt(stmt)
                return block
            case ast.DeclrStmt(declr):
                self.make_declr(declr)
            case ast.ExprStmt(expr):
                self.make_expr(expr)
            case ast.IfStmt(condition, if_block, else_block):
                self.make_if_stmt(condition, if_block, else_block)
            case ast.WhileStmt(condition, block):
                self.make_while_stmt(condition, block)
            case ast.ReturnStmt(value):
                self.make_return_stmt(value)
            case ast.AssignmentStmt(target, value):
                self.make_assignment_stmt(target, value)
            case _:
                assert False, f"Unexpected stmt {node}"

    def make_declr(self, node):
        match node:
            case ast.FunctionDeclr(signature, block):
                self.make_function_declr(signature, block)
            case ast.StructDeclr(name, fields):
                self.make_struct_declr(name, fields)
            case ast.InterfaceDeclr(name, methods):
                raise NotImplementedError
            case ast.ImplDeclr(target, interface, methods):
                raise NotImplementedError
            case ast.VariableDeclr(name, typ, value):
                self.make_variable_declr(name, typ, value)
            case _:
                assert False, f"Unexpected declr {node}"

    def make_literal(self, tok):
        match tok.typ:
            case T.INTEGER:
                val = ir.Constant(int(tok.lexeme))
                val.checked_type = self.scope.lookup("int")
            case T.FLOAT:
                val = ir.Constant(float(tok.lexeme))
                val.checked_type = self.scope.lookup("float")
            case T.RATIONAL:
                val = ir.Constant(Fraction(tok.lexeme.replace("//", "/")))
                val.checked_type = self.scope.lookup("frac")
            case T.STRING:
                val = ir.Constant(str(tok.lexeme[1:-1]))
                val.checked_type = self.scope.lookup("str")
            case T.BOOLEAN:
                val = ir.Constant(tok.lexeme == "true")
                val.checked_type = self.scope.lookup("bool")
            case _:
                assert False, f"Unexpected literal token {tok}"
        return val

    def make_identifier(self, name):
        return self.scope.lookup(name)

    def make_call_expr(self, target, args):
        raise NotImplementedError

    def make_selector_expr(self, target, name):
        target = self.make_expr(target)
        field_id = target.name + "." + name.value
        if (ref := self.scope.lookup(field_id)):
            return ref

        type_hint = None
        if isinstance(target.type_hint, ir.StructTypeRef):
            index = target.type_hint.fields.index(name.value)
            type_hint = target.type_hint.type_hint.fields[index]
        ref = ir.FieldRef(field_id, type_hint, target)
        self.scope.declare(field_id, ref)
        return ref

    def make_unary_expr(self, op, rhs):
        rhs = self.make_expr(rhs)
        return ir.Unary(op.lexeme, rhs)

    def make_binary_expr(self, op, lhs, rhs):
        lhs = self.make_expr(lhs)
        rhs = self.make_expr(rhs)
        return ir.Binary(op.lexeme, lhs, rhs)

    def make_if_stmt(self, condition, if_block, else_block):
        logging.debug("making if ir")
        condition = self.make_expr(condition)
        prev_block = self.block

        if isinstance(if_block, ast.Block):
            if_block = self.make_stmt(if_block)
        else:
            stmt = if_block
            if_block = ir.Block([])
            self.block = if_block
            self.make_stmt(stmt)
        if_block_end = self.block

        if else_block is not None:
            if isinstance(else_block, ast.Block):
                else_block = self.make_stmt(else_block)
            else:
                stmt = else_block
                else_block = ir.Block([])
                self.block = else_block
                self.make_stmt(stmt)
        else_block_end = self.block

        # if there is an empty block ready we can use that as the merge block
        if self.block.instrs:
            merge_block = ir.Block([])
        else:
            merge_block = self.block

        if not if_block_end.is_terminated:
            if_block_end.instrs.append(ir.Branch(merge_block))

        if else_block is None:
            else_block = merge_block
        elif not else_block_end.is_terminated:
            # if we didn't create a new merge block
            # then the else_block_end might be the merge_block
            if else_block_end != merge_block:
                else_block_end.instrs.append(ir.Branch(merge_block))

        prev_block.instrs.append(ir.CBranch(condition, if_block, else_block))
        self.block = merge_block

    def make_while_stmt(self, condition, block):
        cond_block = ir.Block([])
        self.instrs.append(ir.Branch(cond_block))
        self.block = cond_block
        condition = self.make_expr(condition)
        loop_block = self.make_stmt(block)
        loop_block_end = self.block
        end_block = ir.Block([])
        cond_block.instrs.append(ir.CBranch(condition, loop_block, end_block))
        if not loop_block_end.is_terminated:
            loop_block_end.instrs.append(ir.Branch(cond_block))
        self.block = end_block

    def make_return_stmt(self, value):
        value = self.make_expr(value)
        assert self.current_func is not None, "Return statement outside a function"
        self.current_func.return_values.append(value)
        self.instrs.append(ir.Return(value))

    def make_assignment_stmt(self, target, value):
        target = self.make_expr(target)
        value = self.make_expr(value)
        target.values.append(value)
        self.instrs.append(ir.Assign(target, value))

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
        return ir.FunctionSignatureRef(name.value, type_hint, param_names)

    def make_function_declr(self, signature, block):
        def_block = self.block
        sig = self.make_type(signature)
        prev_func = self.current_func
        self.current_func = sig
        self.scope.declare(sig.name, sig)
        prev_block = self.block
        self.scope = Scope(self.scope)
        for pname, ptype in zip(sig.params, sig.type_hint.param_types):
            ref = ir.Ref(pname, ptype)
            self.scope.declare(pname, ref)
        block = self.make_stmt(block)
        self.block = prev_block
        func_scope = self.scope
        self.scope = self.scope.parent
        self.current_func = prev_func
        def_block.instrs.append(ir.DefFunc(sig, block, func_scope))

    def make_struct_declr(self, name, fields):
        name = name.value
        field_names = []
        field_types = []
        for field in fields:
            field_names.append(field.name.value)
            ftype = None
            if field.typ is not None:
                ftype = self.make_type(field.typ)
            field_types.append(ftype)
        type_hint = types.StructType(field_types)
        ref = ir.StructTypeRef(name, type_hint, field_names)
        self.scope.declare(name, ref)
        self.instrs.append(ir.Declare(ref))

    def make_variable_declr(self, name, typ, value):
        name = name.value
        type_hint = None
        if typ is not None:
            type_hint = self.make_type(typ)
        ref = ir.Ref(name, type_hint)
        self.scope.declare(name, ref)
        self.instrs.append(ir.Declare(ref))
        if value is not None:
            value = self.make_expr(value)
            ref.values.append(value)
            self.instrs.append(ir.Assign(ref, value))


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
    print(tree)
    noder = IRNoder()
    iir = noder.make(tree)
    print(noder.scope)
    logging.debug(iir)
    print(ir.IRPrinter().to_string(iir))
