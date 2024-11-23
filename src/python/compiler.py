import logging
from llvmcpy import llvm
from ctypes import CFUNCTYPE, c_int

from . import ir_nodes as ir
from . import type_defs as types
from . import builtin


type_map = {
    builtin.types["int"]: llvm.int32_type(),
    builtin.types["float"]: llvm.double_type(),
    builtin.types["bool"]: llvm.int1_type(),
    builtin.types["char"]: llvm.int8_type(),
}


class Compiler:
    def __init__(self):
        self.refs = {}
        self.module = llvm.module_create_with_name("main")
        self.builder = llvm.create_builder()
        self.i = 0

        self.init_builtins()

    def init_builtins(self):
        # string type
        # assume c-style \00 terminated for now
        string_type = self.module.context.struct_create_named("@String")
        # TODO: include dynamic memory allocation
        string_field_types = [
            self.module.context.pointer_type(0)
        ]
        string_type.struct_set_body(string_field_types, 0)
        type_map[builtin.types["str"]] = string_type

        # array type
        # largely mirrors the string type for now
        # TODO: this is bad, find a better way
        array_type = self.module.context.struct_create_named("@Array")
        array_type.struct_set_body(string_field_types, 0)
        type_map["arr"] = array_type

        # vector type
        # TODO: see above
        vector_type = self.module.context.struct_create_named("@Vector")
        vector_type.struct_set_body(string_field_types, 0)
        type_map["vec"] = vector_type

    def name(self):
        name = "test" + str(self.i)
        self.i += 1
        return name

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
                return return_type.function(param_types, 0)
            case ir.StructRef():
                field_types = [self.build(f) for f in node.fields.values()]
                typ = self.module.context.struct_create_named(node.name)
                typ.struct_set_body(field_types, 0)
                return typ
            case ir.VectorType():
                return type_map["vec"]
            case ir.SequenceType():
                if node.checked == builtin.types["str"]:
                    return type_map[node.checked]
                # If a non-vector non-string sequence type, treat as an array
                # TODO: should SequenceType (non-string) be a valid input here?
                #       should it already have become ArrayType at typechecking?
                return type_map["arr"]
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
                    func = self.module.add_function(name, ftype)
                    block = func.append_basic_block("entry")
                    self.refs[id(node.block)] = block
                    self.builder.position_builder_at_end(block)
                    for param, arg in zip(node.params, func.iter_params()):
                        ptr = self.build(param)
                        self.builder.build_store(arg, ptr)
                        self.refs[id(param)] = ptr
                    # TODO: builtins
                    self.build(node.block)
                    obj = func
                case ir.FieldRef():
                    if isinstance(node.typ, ir.FunctionSigRef):
                        obj = self.build(node.method)
                    else:
                        idx = list(node.parent.typ.fields.keys()).index(node.name)
                        parent = self.build(node.parent)
                        parent_type = self.build(node.parent.typ)
                        return self.builder.build_struct_ge2(parent_type, parent, idx, "")
                    self.refs[id(node)] = obj
                case ir.IndexRef():
                    parent = self.build(node.parent)
                    if isinstance(node.parent, ir.Ref):
                        # this expects a struct with the sequence ptr inside
                        # which is the case if the parent is a Ref
                        parent_type = self.build(node.parent.typ)
                        inner_ptr = self.builder.build_struct_ge2(
                            parent_type, parent, 0, ""
                        )
                        ptr = self.builder.build_load2(inner_ptr.type_of(), inner_ptr, "")
                    else:
                        # this is the case if the parent is a Sequence literal
                        ptr = parent
                    elem_type = self.build(node.parent.typ.elem_type)
                    idx = self.build(node.index)
                    return self.builder.build_in_bounds_ge2(
                        elem_type, ptr, [idx], ""
                    )
                case ir.Ref():
                    typ = self.build(node.typ)
                    ptr = self.builder.build_alloca(typ, node.name)
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
                self.builder.build_store(val, var)
            case ir.Load(ref):
                var = self.build(ref)
                return self.builder.build_load2(self.build(ref.typ), var, "")
            case ir.Call(ref, args):
                func = self.build(ref)
                args = [self.build(a) for a in args]
                return self.builder.build_call2(self.build(ref.typ), func, args, "")
            case ir.Return(value):
                val = self.build(value)
                self.builder.build_ret(val)
            case ir.Branch(block):
                self.builder.build_branch(self.get_block(block))
                self.build(block)
            case ir.CBranch(condition, t_block, f_block):
                cond = self.build(condition)
                self.builder.build_cbranch(
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
                self.builder.position_builder_at_end(block)
                for instr in instrs:
                    self.build(instr)
            case ir.Program(block):
                # cannot build the block because no IRBuilder is set
                # perhaps there should be a global func/block
                for instr in block.instrs:
                    self.build(instr)
            case ir.Constant(value):
                typ = self.build(node.typ)
                match typ.get_kind():
                    case llvm.IntegerTypeKind:
                        return typ.const_int(value, 0)
                    case _:
                        raise NotImplementedError
            case ir.Sequence(value):
                if node.typ == builtin.scope.lookup("str"):
                    typ = self.build(node.typ)
                    literal = "".join(c.value for c in value)
                    const_cstr = llvm.const_string(literal, len(value), 0)
                    cstr_ptr = self.module.add_global(const_cstr.type_of(), "")
                    cstr_ptr.set_initializer(const_cstr)
                    const_str = typ.const_named_struct([cstr_ptr])
                    str_ptr = self.module.add_global(typ, "")
                    str_ptr.set_initializer(const_str)
                    return const_str
                elif isinstance(node.typ, ir.SequenceType):
                    typ = self.build(node.typ)
                    elem_type = self.build(node.typ.elem_type)
                    ptr = self.builder.build_alloca(typ, "sequencelit")
                    for idx in range(len(value)):
                        # Convert the index into an LLVM int
                        element_idx = type_map[builtin.types["int"]].const_int(idx, 0)
                        element_ptr = self.builder.build_ge2(elem_type, ptr, [element_idx], "idx")
                        self.builder.build_store(self.build(value[idx]), element_ptr)
                    return ptr
                else:
                    assert False, f"Unreachable: {node}"
            case ir.StructLiteral(fields):
                typ = self.build(node.typ)
                fields = [self.build(f) for f in fields.values()]
                return typ.const_named_struct(fields)
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


def execute_module(mod, entry="main", return_type=c_int):
    mod.dump()
    mod.verify(llvm.AbortProcessAction)
    llvm.link_in_mcjit()
    llvm.initialize_x86_target()
    llvm.initialize_x86_asm_printer()
    llvm.initialize_x86_asm_parser()
    llvm.initialize_x86_target_mc()
    llvm.initialize_x86_target_info()
    engine = llvm.create_execution_engine_for_module(mod)
    entrypoint = engine.find_function(entry)
    res = engine.run_function_as_main(entrypoint, 0, [], [])
    return res


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
