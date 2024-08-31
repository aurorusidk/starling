from contextlib import contextmanager
from fractions import Fraction
import logging

from .lexer import TokenType as T
from .scope import Scope
from . import ast_nodes as ast
from . import type_defs as types
from . import builtin
from . import ir_nodes as ir


class IRNoder:
    def __init__(self, error_handler=None):
        self.scope = Scope(builtin.scope)
        self.exprs = []
        self.block = ir.Block([])
        self.current_func = None
        self.blocks = {}
        self.error_handler = error_handler

    def error(self, msg):
        # add position info
        msg = f"Syntax error: {msg}"
        if self.error_handler is None:
            assert False, msg

        self.error_handler(msg)

    @property
    def instrs(self):
        return self.block.instrs

    @contextmanager
    def new_scope(self):
        prev_scope = self.scope
        self.scope = Scope(prev_scope)
        yield self.scope
        self.scope = prev_scope

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
                return self.make_call_expr(
                    ast.Identifier("range_constructor@builtin"),
                    [start, end]
                )
            case ast.SequenceExpr(elements):
                return self.make_sequence_expr(node, elements)
            case ast.GroupExpr(expr):
                return self.make_expr(expr, load)
            case ast.CallExpr(target, args):
                return self.make_call_expr(target, args)
            case ast.IndexExpr(target, index):
                return self.make_index_expr(target, index, load)
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
                assert isinstance(typ, ir.Type)
                return typ
            case ast.ArrayType(elem_type, length):
                return ir.Type(
                    f"arr[{elem_type},{length}]",
                    types.ArrayType(elem_type, length)
                )
            case ast.VectorType(elem_type):
                return ir.Type(
                    f"vec[{elem_type}]",
                    types.VectorType(elem_type)
                )
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
                val.typ = self.scope.lookup("int")
            case T.FLOAT:
                val = ir.Constant(float(tok.lexeme))
                val.typ = self.scope.lookup("float")
            case T.RATIONAL:
                val = ir.Constant(Fraction(tok.lexeme.replace("//", "/")))
                val.typ = self.scope.lookup("frac")
            case T.STRING:
                val = ir.Constant(str(tok.lexeme[1:-1]))
                val.typ = self.scope.lookup("str")
            case T.BOOLEAN:
                val = ir.Constant(tok.lexeme == "true")
                val.typ = self.scope.lookup("bool")
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

    def make_sequence_expr(self, node, elements):
        elements = [self.make(element) for element in elements]
        match node:
            case ast.ArrayExpr():
                return ir.Array(elements)
            case ast.VectorExpr():
                return ir.Vector(elements)
            case _:
                return ir.Sequence(elements)

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
            args.insert(0, ir.Load(target.parent))
            target.param_values = args
        elif isinstance(target, ir.StructRef):
            assert len(args) == len(target.fields)
            fields = {}
            for fname, value in zip(target.fields, args):
                fields[fname] = value
            return ir.StructLiteral(fields, typ=target)
        return ir.Call(target, args)

    def make_index_expr(self, target, index, load=True):
        target = self.make_expr(target, load=False)
        index = self.make_expr(index)

        if isinstance(index, ir.Constant):
            index_name = f"{target.name}[{str(index.value)}]"
        elif isinstance(index, ir.Ref):
            index_name = f"{target.name}[{index.name}]"
        else:
            assert False, "Unreachable"

        ref = ir.IndexRef(index_name, target, index)
        if load:
            return ir.Load(ref)
        return ref

    def make_selector_expr(self, target, name, load=True):
        target = self.make_expr(target, load=False)
        field_name = name.value
        ref = target.members.get(field_name)

        if not ref:
            type_hint = None
            if isinstance(target.typ, ir.StructRef):
                type_hint = target.typ.hint.fields.get(name.value)
            ref = ir.FieldRef(field_name, target, typ=type_hint)
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
        name = name.value
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
        return ir.FunctionSigRef(name, type_hint, dict(zip(param_names, param_types)), return_type)

    def make_method_signature(self, method, target=None):
        sig = self.make_type(method)
        sig.params = {"self": target} | sig.params
        return sig

    def make_function_body(self, func, block):
        prev_block = self.block
        prev_func = self.current_func
        self.current_func = func
        self.scope.declare(func.name, func)
        self.instrs.append(ir.Declare(func))
        with self.new_scope():
            param_refs = []
            for pname, ptype in func.typ.params.items():
                ref = ir.Ref(pname, typ=ptype)
                self.scope.declare(pname, ref)
                param_refs.append(ref)
            func.params = param_refs
            block = self.make_stmt(block)
        self.block = prev_block
        self.current_func = prev_func
        func.block = block
        self.block.deps.append(block)
        return func

    def make_function_declr(self, signature, block):
        sig = self.make_type(signature)
        func = ir.FunctionRef(sig.name, typ=sig)
        return self.make_function_body(func, block)

    def make_method_declr(self, method, target):
        sig = self.make_method_signature(method.signature, target)
        func = ir.MethodRef(sig.name, target, typ=sig)
        return self.make_function_body(func, method.block)

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
        fields = dict(zip(field_names, field_types))
        type_hint = types.StructType(fields)
        ref = ir.StructRef(name, type_hint, fields)
        self.scope.declare(name, ref)
        self.instrs.append(ir.Declare(ref))

    def make_impl_declr(self, target, interface, methods):
        target = self.make_type(target)
        self.scope = Scope(self.scope)
        prev_block = self.block
        block = ir.Block([])
        self.block = block
        if interface is None:
            for method in methods:
                method = self.make_method_declr(method, target)
                target.methods[method.name] = method
        else:
            interface = self.make_expr(interface, load=False)
            defined_methods = set()
            for method in methods:
                method = self.make_method_declr(method, target)
                target.methods[method.name] = method
                interface.methods[method.name].values.append(method.typ)
                method.typ = interface.methods[method.name]
                defined_methods.add(method.name)
            # TODO: proper errors and should determine the missing/unwanted methods
            assert defined_methods == set(interface.methods.keys())
        self.block = prev_block
        self.scope = self.scope.parent
        self.instrs.append(ir.DeclareMethods(target, block))
        self.block.deps.append(block)

    def make_interface_declr(self, name, methods):
        name = name.value
        method_refs = {}
        for method in methods:
            method_ref = self.make_method_signature(method)
            method_refs[method_ref.name] = method_ref
        interface = types.Interface(name, method_refs)
        ref = ir.InterfaceRef(name, interface, method_refs)
        self.scope.declare(name, ref)
        # self.instrs.append(ir.Declare(ref))

    def make_variable_declr(self, name, typ, value):
        name = name.value
        type_hint = None
        if typ is not None:
            type_hint = self.make_type(typ)
        ref = ir.Ref(name, typ=type_hint)
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
