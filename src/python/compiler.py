from llvmcpy import LLVMCPy

from . import ir_nodes as ir
from . import builtin


llvm = LLVMCPy()


type_map = {
    builtin.types["int"]: llvm.int32_type(),
    builtin.types["float"]: llvm.double_type(),
    builtin.types["bool"]: llvm.int1_type(),
}


class Compiler:
    def __init__(self):
        self.refs = {}
        self.module = llvm.module_create_with_name("main")
        self.builder = llvm.create_builder()
        self.i = 0

    def name(self):
        name = "test" + str(self.i)
        self.i += 1
        return name

    def build(self, node, **kwargs):
        # We don't want to build anything more than once
        if (obj := self.refs.get(id(node))):
            return obj
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
            case ir.Type():
                return type_map[node.checked]
            case _:
                assert False, f"Unreachable: {node}"

    def build_ref(self, node):
        match node:
            case ir.FunctionRef():
                ftype = self.build(node.typ)
                name = node.name
                if isinstance(node, ir.MethodRef):
                    name = node.parent.name + "." + node.name
                func = self.module.add_function(name, ftype)
                block = func.append_basic_block("entry")
                self.builder.position_builder_at_end(block)
                for param, arg in zip(node.params, func.iter_params()):
                    ptr = self.build(param)
                    self.builder.build_store(arg, ptr)
                    self.refs[id(param)] = ptr
                # cannot build the block because no function is set yet
                for instr in node.block.instrs:
                    self.build(instr)
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
            case ir.Ref():
                typ = self.build(node.typ)
                ptr = self.builder.build_alloca(typ, node.name)
                return ptr
        return obj

    def build_instr(self, node):
        match node:
            case ir.Declare(ref):
                var = self.build(ref)
                self.refs[id(ref)] = var
            case ir.DeclareMethods(_, block):
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
                self.builder.build_br(self.build(block))
            case ir.CBranch(condition, t_block, f_block):
                cond = self.build(condition)
                self.builder.build_cond_br(
                    cond,
                    self.build(t_block),
                    self.build(f_block)
                )
            case ir.Binary():
                return self.build_binary(node)
            case ir.Unary():
                return self.build_unary(node)
            case _:
                assert False, f"Unexpected instruction {type(node)}"

    def build_object(self, node):
        match node:
            case ir.Block(instrs):
                prev_block = self.builder.insert_block
                parent = self.builder.insert_block.get_parent()
                block = self.module.context.append_basic_block(parent, "")
                self.builder.position_builder_at_end(block)
                for instr in instrs:
                    self.build(instr)
                self.builder.position_builder_at_end(prev_block)
                self.refs[id(node)] = block
                return block
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
                    case llvm.DoubleTypeKind:
                        return typ.const_real(value)
                    case _:
                        raise NotImplementedError
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
        if left.type_of() == type_map[builtin.types["int"]]:
            return self.builder.build_add(left, right, "")
        elif left.type_of() == type_map[builtin.types["float"]]:
            return self.builder.build_f_add(left, right, "")
        else:
            raise NotImplementedError

    def build_sub(self, left, right):
        if left.type_of() == type_map[builtin.types["int"]]:
            return self.builder.build_sub(left, right, "")
        elif left.type_of() == type_map[builtin.types["float"]]:
            return self.builder.build_f_sub(left, right, "")
        else:
            raise NotImplementedError

    def build_mul(self, left, right):
        if left.type_of() == type_map[builtin.types["int"]]:
            return self.builder.build_mul(left, right, "")
        elif left.type_of() == type_map[builtin.types["float"]]:
            return self.builder.build_f_mul(left, right, "")
        else:
            raise NotImplementedError

    def build_div(self, left, right):
        if left.type_of() == type_map[builtin.types["int"]]:
            float_type = type_map[builtin.types["float"]]
            left = self.builder.build_si_to_fp(left, float_type, "")
            right = self.builder.build_si_to_fp(right, float_type, "")
            return self.builder.build_f_div(left, right, "")
        elif left.type_of() == type_map[builtin.types["float"]]:
            return self.builder.build_f_div(left, right, "")
        else:
            raise NotImplementedError

    def build_equal(self, left, right):
        if left.type_of() == type_map[builtin.types["int"]]:
            # 32 represents integer equality
            return self.builder.build_i_cmp(32, left, right, "")
        elif left.type_of() == type_map[builtin.types["float"]]:
            # 1 represents real ordered equality
            return self.builder.build_f_cmp(1, left, right, "")
        elif left.type_of() == type_map[builtin.types["bool"]]:
            return self.builder.build_i_cmp(32, left, right, "")
        else:
            raise NotImplementedError

    def build_not_equal(self, left, right):
        if left.type_of() == type_map[builtin.types["int"]]:
            # 33 represents integer inequality
            return self.builder.build_i_cmp(33, left, right, "")
        elif left.type_of() == type_map[builtin.types["float"]]:
            # 6 represents real ordered inequality
            return self.builder.build_f_cmp(6, left, right, "")
        elif left.type_of() == type_map[builtin.types["bool"]]:
            return self.builder.build_i_cmp(33, left, right, "")
        else:
            raise NotImplementedError

    def build_less_than(self, left, right):
        if left.type_of() == type_map[builtin.types["int"]]:
            # 40 represents integer signed less than
            return self.builder.build_i_cmp(40, left, right, "")
        elif left.type_of() == type_map[builtin.types["float"]]:
            # 4 represents real ordered less than
            return self.builder.build_f_cmp(4, left, right, "")
        else:
            raise NotImplementedError

    def build_greater_than(self, left, right):
        if left.type_of() == type_map[builtin.types["int"]]:
            # 38 represents integer signed greater than
            return self.builder.build_i_cmp(38, left, right, "")
        elif left.type_of() == type_map[builtin.types["float"]]:
            # 2 represents real ordered greater than
            return self.builder.build_f_cmp(2, left, right, "")
        else:
            raise NotImplementedError

    def build_less_than_equal(self, left, right):
        if left.type_of() == type_map[builtin.types["int"]]:
            # 41 represents integer signed less than equal to
            return self.builder.build_i_cmp(41, left, right, "")
        elif left.type_of() == type_map[builtin.types["float"]]:
            # 5 represents real ordered less than equal to
            return self.builder.build_f_cmp(5, left, right, "")
        else:
            raise NotImplementedError

    def build_greater_than_equal(self, left, right):
        if left.type_of() == type_map[builtin.types["int"]]:
            # 39 represents integer signed greater than equal to
            return self.builder.build_i_cmp(39, left, right, "")
        elif left.type_of() == type_map[builtin.types["float"]]:
            # 3 represents real ordered greater than equal to
            return self.builder.build_f_cmp(3, left, right, "")
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
        if right.type_of() == type_map[builtin.types["bool"]]:
            return self.builder.build_not(right, "")
        else:
            raise NotImplementedError

    def build_neg(self, right):
        if right.type_of() == type_map[builtin.types["int"]]:
            # 39 represents integer signed greater than equal to
            return self.builder.build_neg(right, "")
        elif right.type_of() == type_map[builtin.types["float"]]:
            # 3 represents real ordered greater than equal to
            return self.builder.build_f_neg(right, "")
        else:
            raise NotImplementedError


def execute_module(mod, entry="main"):
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
