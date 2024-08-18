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
        for name, typ in builtin.types.items():
            self.scope.declare(name, typ)
        self.exprs = []
        self.block = ir.Block([])
        self.current_func = None
        self.blocks = {}

    @property
    def instrs(self):
        return self.block.instrs

    def new_block(self):
        block = ir.Block([])
        self.blocks[ir.id_hash(block)] = block
        return block

    def branch(self, block, from_block=None):
        if from_block is None:
            from_block = self.block
        from_block.deps.append(block)
        instr = ir.Branch(block)
        from_block.instrs.append(instr)
        return instr

    def cbranch(self, cond, t_block, f_block, from_block=None):
        if from_block is None:
            from_block = self.block
        from_block.deps.extend((t_block, f_block))
        instr = ir.CBranch(cond, t_block, f_block)
        from_block.instrs.append(instr)
        return instr

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
                return ir.Program(block)
            case _:
                assert False, f"Unexpected node {node}"

    def make_expr(self, node, load=True):
        match node:
            case ast.Literal(tok):
                return self.make_literal(tok)
            case ast.Identifier(name):
                return self.make_identifier(name, load)
            case ast.RangeExpr(start, end):
                raise NotImplementedError
            case ast.GroupExpr(expr):
                return self.make_expr(expr, load)
            case ast.CallExpr(target, args):
                return self.make_call_expr(target, args)
            case ast.IndexExpr(target, index):
                raise NotImplementedError
            case ast.SelectorExpr(target, name):
                return self.make_selector_expr(target, name, load)
            case ast.UnaryExpr(op, rhs):
                return self.make_unary_expr(op, rhs)
            case ast.BinaryExpr(op, lhs, rhs):
                return self.make_binary_expr(op, lhs, rhs)
            case _:
                assert False, f"Unexpected expr {node}"

    def make_type(self, node):
        match node:
            case ast.TypeName(name):
                typ = self.make_identifier(name.value, load=False)
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
                block = self.new_block()
                self.block = block
                for stmt in stmts:
                    self.make_stmt(stmt)
                return block
            case ast.DeclrStmt(declr):
                self.make_declr(declr)
            case ast.ExprStmt(expr):
                self.instrs.append(self.make_expr(expr))
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
                self.make_interface_declr(name, methods)
            case ast.ImplDeclr(target, interface, methods):
                self.make_impl_declr(target, interface, methods)
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

    def make_identifier(self, name, load=True):
        ref = self.scope.lookup(name)
        if ref is None:
            assert False, f"Unknown name {name}"
        if load:
            return ir.Load(ref)
        return ref

    def make_call_expr(self, target, args):
        target = self.make_expr(target, load=False)
        args = [self.make(a) for a in args]
        if isinstance(target, ir.FunctionRef):
            for param, arg in zip(target.params, args):
                values = target.param_values.get(param.name, [])
                values.append(arg)
                target.param_values[param.name] = values
                param.values.append(arg)
        elif isinstance(target, ir.FieldRef):
            # method so add `self`
            args.insert(0, target.parent)
            target.param_values = args
        return ir.Call(target, args)

    def make_selector_expr(self, target, name, load=True):
        target = self.make_expr(target, load=False)
        field_name = name.value
        ref = target.members.get(field_name)

        if not ref:
            type_hint = None
            if isinstance(target.type_hint, types.StructType):
                type_hint = target.type_hint.fields.get(name.value)
            ref = ir.FieldRef(field_name, type_hint, target)
            target.members[field_name] = ref
        if load:
            return ir.Load(ref)
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
            if_block = self.new_block()
            self.block = if_block
            self.make_stmt(stmt)
        if_block_end = self.block

        if else_block is not None:
            if isinstance(else_block, ast.Block):
                else_block = self.make_stmt(else_block)
            else:
                stmt = else_block
                else_block = self.new_block()
                self.block = else_block
                self.make_stmt(stmt)
        else_block_end = self.block

        # if there is an empty block ready we can use that as the merge block
        if self.block.instrs:
            merge_block = self.new_block()
        else:
            merge_block = self.block

        if not if_block_end.is_terminated:
            self.branch(merge_block, from_block=if_block_end)

        if else_block is None:
            else_block = merge_block
        elif not else_block_end.is_terminated:
            # if we didn't create a new merge block
            # then the else_block_end might be the merge_block
            if else_block_end != merge_block:
                self.branch(merge_block, from_block=else_block_end)

        self.cbranch(condition, if_block, else_block, from_block=prev_block)
        self.block = merge_block

    def make_while_stmt(self, condition, block):
        cond_block = self.new_block()
        self.branch(cond_block)
        self.block = cond_block
        condition = self.make_expr(condition)
        loop_block = self.make_stmt(block)
        loop_block_end = self.block
        end_block = self.new_block()
        self.cbranch(condition, loop_block, end_block, from_block=cond_block)
        if not loop_block_end.is_terminated:
            self.branch(cond_block, from_block=loop_block_end)
        self.block = end_block

    def make_return_stmt(self, value):
        value = self.make_expr(value)
        assert self.current_func is not None, "Return statement outside a function"
        self.current_func.return_values.append(value)
        self.instrs.append(ir.Return(value))

    def make_assignment_stmt(self, target, value):
        target = self.make_expr(target, load=False)
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
        return ir.FunctionRef(name.value, type_hint, param_names)

    def make_function_declr(self, signature, block):
        def_block = self.block
        func = self.make_type(signature)
        prev_func = self.current_func
        self.current_func = func
        self.scope.declare(func.name, func)
        self.scope = Scope(self.scope)
        param_refs = []
        for pname, ptype in zip(func.param_names, func.type_hint.param_types):
            ref = ir.Ref(pname, ptype)
            self.scope.declare(pname, ref)
            param_refs.append(ref)
        func.params = param_refs
        block = self.make_stmt(block)
        self.block = def_block
        self.scope = self.scope.parent
        self.current_func = prev_func
        func.block = block
        def_block.instrs.append(ir.Declare(func))
        def_block.deps.append(block)
        return func

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
        type_hint = types.StructType(dict(zip(field_names, field_types)))
        self.scope.declare(name, type_hint)
        self.instrs.append(ir.Declare(ir.StructRef(name, type_hint, field_names)))

    def make_method(self, target, method):
        def_block = self.block
        func = self.make_type(method.signature)
        func.name = func.name
        func.param_names.insert(0, "self")
        func.type_hint.param_types.insert(0, target)
        prev_func = self.current_func
        self.current_func = func
        self.scope.declare(func.name, func)
        self.scope = Scope(self.scope)
        param_refs = []
        for pname, ptype in zip(func.param_names, func.type_hint.param_types):
            ref = ir.Ref(pname, ptype)
            self.scope.declare(pname, ref)
            param_refs.append(ref)
        func.params = param_refs
        block = self.make_stmt(method.block)
        self.block = def_block
        self.scope = self.scope.parent
        self.current_func = prev_func
        func.block = block
        def_block.instrs.append(ir.Declare(func))
        def_block.deps.append(block)
        return func

    def make_impl_declr(self, target, interface, methods):
        target = self.make_type(target)
        self.scope = Scope(self.scope)
        prev_block = self.block
        block = ir.Block([])
        self.block = block
        if interface is None:
            for method in methods:
                method = self.make_method(target, method)
                target.methods[method.name] = method
        else:
            interface = self.make_expr(interface, load=False)
            defined_methods = set()
            for method in methods:
                method = self.make_method(target, method)
                target.methods[method.name] = method
                defined_methods.add(method.name)
            # TODO: proper errors and should determine the missing/unwanted methods
            assert defined_methods == set(interface.funcs.keys())
        self.block = prev_block
        self.scope = self.scope.parent
        self.instrs.append(ir.DeclareMethods(target, block))
        self.block.deps.append(block)

    def make_interface_declr(self, name, methods):
        name = name.value
        method_refs = {}
        for method in methods:
            method_ref = self.make_type(method)
            method_refs[method_ref.name] = method_ref
        interface = types.Interface(name, method_refs)
        self.scope.declare(name, interface)
        self.instrs.append(ir.Declare(ir.InterfaceRef(name, interface, list(method_refs.keys()))))

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
    from . import control_flows as cf

    logging.basicConfig(format="%(levelname)s: %(message)s")
    logging.getLogger().setLevel(logging.DEBUG)

    assert len(sys.argv) == 2, "no input file"
    with open(sys.argv[1]) as f:
        src = f.read()
    toks = lexer.tokenise(src)
    tree = parser.parse(toks)
    logging.debug(tree)
    noder = IRNoder()
    block = noder.block
    iir = noder.make(tree)
    logging.debug(iir)
    print(ir.IRPrinter().to_string(iir))
    flows = cf.create_flows(block)
    cf.ControlFlows(flows).draw_flow()
