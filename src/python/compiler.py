import logging
from llvmlite import ir as llvm
from llvmlite import binding
from ctypes import CFUNCTYPE, c_int

from . import ir_nodes as ir
from . import type_defs as types
from . import builtin


type_map = {
    builtin.types["int"]: llvm.IntType(32),
    builtin.types["float"]: llvm.DoubleType(),
    builtin.types["bool"]: llvm.IntType(1),
}


class Compiler:
    def __init__(self):
        self.refs = {}
        self.module = llvm.Module()
        self.builder = None

    def get_block(self, block):
        if id(block) not in self.refs:
            b = self.builder.append_basic_block()
            self.refs[id(block)] = b
            return b
        else:
            return self.refs[id(block)]

    def build(self, node, **kwargs):
        match node:
            case ir.Type():
                return self.build_type(node)
            case ir.Ref():
                return self.build_ref(node)
            case ir.Instruction():
                return self.build_instr(node)
            case ir.Object():
                return self.build_object(node)
            case _:
                assert False, f"Unreachable: {node}"

    def build_type(self, node):
        if (t := self.refs.get(id(node))):
            return t
        match node:
            case ir.FunctionSigRef():
                param_types = [self.build(p) for p in node.params.values()]
                return_type = self.build(node.return_type)
                return llvm.FunctionType(return_type, param_types)
            case ir.StructRef():
                field_types = [self.build(f) for f in node.fields.values()]
                typ = self.module.context.get_identified_type(node.name)
                typ.set_body(*field_types)
                return typ
            case ir.Type():
                return type_map[node.checked]
            case _:
                assert False, f"Unreachable: {node}"

    def build_ref(self, node):
        # using id() to get a unique hashable object for refs
        if id(node) not in self.refs:
            # make a new object for the ref
            match node:
                case ir.FunctionRef():
                    ftype = self.build(node.typ)
                    name = node.name
                    if isinstance(node, ir.MethodRef):
                        name = node.parent.name + "." + node.name
                    func = llvm.Function(self.module, ftype, name=name)
                    block = func.append_basic_block("entry")
                    self.refs[id(node.block)] = block
                    prev_builder = self.builder
                    self.builder = llvm.IRBuilder(block)
                    for param, arg in zip(node.params, func.args):
                        ptr = self.build(param)
                        self.builder.store(arg, ptr)
                        self.refs[id(param)] = ptr
                    self.build(node.block)
                    self.builder = prev_builder
                    obj = func
                case ir.FieldRef():
                    if isinstance(node.typ, ir.FunctionSigRef):
                        obj = self.build(node.method)
                    else:
                        idx = list(node.parent.typ.fields.keys()).index(node.name)
                        parent = self.build(node.parent)
                        ptr_idx = llvm.Constant(llvm.IntType(32), 0)
                        field_idx = llvm.Constant(llvm.IntType(32), idx)
                        return self.builder.gep(parent, [ptr_idx, field_idx])
                    self.refs[id(node)] = obj
                case ir.Ref():
                    typ = self.build(node.typ)
                    ptr = self.builder.alloca(typ)
                    return ptr
            return obj
        else:
            return self.refs[id(node)]

    def build_instr(self, node):
        match node:
            case ir.Declare(ref):
                var = self.build(ref)
                self.refs[id(ref)] = var
            case ir.DeclareMethods(typ, block):
                for instr in block.instrs:
                    self.build(instr)
            case ir.Assign(ref, value):
                var = self.build(ref)
                val = self.build(value)
                self.builder.store(val, var)
            case ir.Load(ref):
                var = self.build(ref)
                return self.builder.load(var)
            case ir.Call(ref, args):
                func = self.build(ref)
                args = [self.build(a) for a in args]
                return self.builder.call(func, args)
            case ir.Return(value):
                val = self.build(value)
                self.builder.ret(val)
            case ir.Branch(block):
                self.builder.branch(self.get_block(block))
                self.build(block)
            case ir.CBranch(condition, t_block, f_block):
                cond = self.build(condition)
                self.builder.cbranch(
                    cond,
                    self.get_block(t_block),
                    self.get_block(f_block)
                )
                self.build(t_block)
                self.build(f_block)
            case ir.Binary():
                return self.build_binary(node)
            case ir.Unary():
                return self.build_unary(node)
            case _:
                assert False, f"Unexpected instruction {type(node)}"

    def build_object(self, node):
        match node:
            case ir.Block(instrs):
                block = self.get_block(node)
                self.builder.position_at_end(block)
                for instr in instrs:
                    self.build(instr)
            case ir.Program(block):
                # cannot build the block because no IRBuilder is set
                # perhaps there should be a global func/block
                for instr in block.instrs:
                    self.build(instr)
            case ir.Constant(value):
                typ = self.build(node.typ)
                return llvm.Constant(typ, value)
            case ir.StructLiteral(fields):
                typ = self.build(node.typ)
                fields = [self.build(f) for f in fields.values()]
                return llvm.Constant(typ, fields)
                raise NotImplementedError
            case _:
                assert False

    def build_binary(self, node):
        left = self.build(node.lhs)
        right = self.build(node.rhs)
        match node.op:
            case '+':
                return self.build_add(left, right)
            case '-':
                return self.build_sub(left, right)
            case '*':
                return self.build_mul(left, right)
            case '/':
                return self.build_div(left, right)
            case '==':
                return self.build_equal(left, right)
            case '!=':
                return self.build_not_equal(left, right)
            case '<':
                return self.build_less_than(left, right)
            case '>':
                return self.build_greater_than(left, right)
            case '<=':
                return self.build_less_than_equal(left, right)
            case '>=':
                return self.build_greater_than_equal(left, right)
            case _:
                assert False, f"Unimplemented operator: {node.op}"

    def build_add(self, left, right):
        # Type coercion not implemented, so only left.typ needs checking
        if left.type == llvm.IntType(32):
            return self.builder.add(left, right)
        elif left.type == llvm.DoubleType():
            return self.builder.fadd(left, right)
        else:
            raise NotImplementedError

    def build_sub(self, left, right):
        if left.type == llvm.IntType(32):
            return self.builder.sub(left, right)
        elif left.type == llvm.DoubleType():
            return self.builder.fsub(left, right)
        else:
            raise NotImplementedError

    def build_mul(self, left, right):
        if left.type == llvm.IntType(32):
            return self.builder.mul(left, right)
        elif left.type == llvm.DoubleType():
            return self.builder.fmul(left, right)
        else:
            raise NotImplementedError

    def build_div(self, left, right):
        if left.type == llvm.IntType(32):
            left = self.builder.sitofp(left, llvm.DoubleType())
            right = self.builder.sitofp(right, llvm.DoubleType())
            return self.builder.fdiv(left, right)
        elif left.type == llvm.DoubleType():
            return self.builder.fdiv(left, right)
        else:
            raise NotImplementedError

    def build_equal(self, left, right):
        if left.type == llvm.IntType(32):
            return self.builder.icmp_signed("==", left, right)
        elif left.type == llvm.DoubleType():
            return self.builder.fcmp_ordered("==", left, right)
        elif left.type == llvm.IntType(1):
            return self.builder.icmp_unsigned("==", left, right)
        else:
            raise NotImplementedError

    def build_not_equal(self, left, right):
        if left.type == llvm.IntType(32):
            return self.builder.icmp_signed("!=", left, right)
        elif left.type == llvm.DoubleType():
            return self.builder.fcmp_ordered("!=", left, right)
        elif left.type == llvm.IntType(1):
            return self.builder.icmp_unsigned("!=", left, right)
        else:
            raise NotImplementedError

    def build_less_than(self, left, right):
        if left.type == llvm.IntType(32):
            return self.builder.icmp_signed("<", left, right)
        elif left.type == llvm.DoubleType():
            return self.builder.fcmp_ordered("<", left, right)
        else:
            raise NotImplementedError

    def build_greater_than(self, left, right):
        if left.type == llvm.IntType(32):
            return self.builder.icmp_signed(">", left, right)
        elif left.type == llvm.DoubleType():
            return self.builder.fcmp_ordered(">", left, right)
        else:
            raise NotImplementedError

    def build_less_than_equal(self, left, right):
        if left.type == llvm.IntType(32):
            return self.builder.icmp_signed("<=", left, right)
        elif left.type == llvm.DoubleType():
            return self.builder.fcmp_ordered("<=", left, right)
        else:
            raise NotImplementedError

    def build_greater_than_equal(self, left, right):
        if left.type == llvm.IntType(32):
            return self.builder.icmp_signed(">=", left, right)
        elif left.type == llvm.DoubleType():
            return self.builder.fcmp_ordered(">=", left, right)
        else:
            raise NotImplementedError

    def build_unary(self, node):
        right = self.build(node.rhs)
        match node.op:
            case '!':
                return self.build_not(right)
            case '-':
                return self.build_neg(right)
            case _:
                assert False, f"Unimplemented operator: {node.op}"

    def build_not(self, right):
        raise NotImplementedError

    def build_neg(self, right):
        raise NotImplementedError


def compile_ir(llvmir):
    mod = binding.parse_assembly(llvmir)
    mod.verify()
    return mod


def create_execution_engine():
    target = binding.Target.from_default_triple()
    target_machine = target.create_target_machine()
    backing_mod = binding.parse_assembly("")
    engine = binding.create_mcjit_compiler(backing_mod, target_machine)
    return engine


def execute_ir(llvmir, entry="main", return_type=c_int):
    binding.initialize()
    binding.initialize_native_target()
    binding.initialize_native_asmprinter()
    mod = compile_ir(llvmir)
    engine = create_execution_engine()
    engine.add_module(mod)
    engine.finalize_object()
    engine.run_static_constructors()
    func_ptr = engine.get_function_address(entry)
    cfunc = CFUNCTYPE(return_type)(func_ptr)
    return cfunc()


if __name__ == "__main__":
    import sys

    from .lexer import tokenise
    from .parser import parse
    from .type_checker import TypeChecker

    logging.basicConfig(format="%(levelname)s: %(message)s")
    logging.getLogger().setLevel(logging.DEBUG)

    assert len(sys.argv) == 2, "no input file"
    with open(sys.argv[1]) as f:
        src = f.read()
    tokens = tokenise(src)
    tree = parse(tokens)
    tc = TypeChecker(tree)
    tc.check(tree)
    compiler = Compiler()
    compiler.build_node(tree)
    res = execute_ir(str(compiler.module))
    print("program exited with code:", res)
