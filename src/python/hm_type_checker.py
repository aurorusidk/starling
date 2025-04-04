import sys

from . import builtin
from . import cmd
from . import ir_nodes as ir
from . import tir_nodes as tir


class TypeVariable:
    next_var_id = 0

    def __init__(self):
        self.id = TypeVariable.next_var_id
        TypeVariable.next_var_id += 1
        self.__name = None
        self.forwarded = None

    next_var_name = 'a'

    @property
    def name(self):
        if self.__name is None:
            self.__name = TypeVariable.next_var_name
            TypeVariable.next_var_name = chr(ord(TypeVariable.next_var_name) + 1)
        return self.__name

    def __str__(self):
        if self.forwarded is not None:
            return str(self.forwarded)
        else:
            return self.name

    def __repr__(self):
        return f"TypeVariable(id = {self.id})"


class TypeConstructor:
    def __init__(self, name, types):
        self.name = name
        self.types = types

    def __str__(self):
        if len(self.types) == 0:
            return self.name
        elif len(self.types) == 2:
            return f"({self.types[0]} {self.name} {self.types[1]})"
        else:
            return f"{self.name} {' '.join(self.types)}"


class Function(TypeConstructor):
    def __init__(self, from_type, to_type):
        super().__init__("->", [from_type, to_type])


class EmptyRow:
    def __str__(self):
        return "{}"


class TypeRow:
    def __init__(self, fields, rest=EmptyRow()):
        self.fields = fields
        self.rest = rest
        self._str = ""

    def __str__(self):
        if self._str:
            return self._str

        self._str = "self"
        rest, fields = row_flatten(self)

        field_strings = []
        method_strings = []
        for k, v in fields.items():
            if isinstance((v := prune(v)), Function):
                self_type = v.types[0]
                v.types[0] = "self"
                v_str = str(v)
                v.types[0] = self_type
                method_strings.append(f"{k} = {v_str}")
            else:
                field_strings.append(f"{k} = {v}")
        row_format = ", ".join(field_strings + method_strings)
        self._str = ""
        return f"{{{row_format}, ...{str(rest)}}}"


Void = TypeConstructor("void", [])
Integer = TypeConstructor("int", [])
Float = TypeConstructor("float", [])
Rational = TypeConstructor("frac", [])
Char = TypeConstructor("char", [])
Bool = TypeConstructor("bool", [])
None_ = TypeConstructor("none", [])


class Optional(TypeRow):
    def __init__(self, some_type=TypeVariable()):
        fields = {"some": some_type, "none": None_}
        super().__init__(fields)


Any = TypeVariable()

type_map = {
    builtin.types["int"]: Integer,
    builtin.types["float"]: Float,
    builtin.types["frac"]: Rational,
    builtin.types["char"]: Char,
    builtin.types["bool"]: Bool,
    builtin.types["none"]: None_, # TODO: naming convention?
}

operator_table = {
    "+": Function(Any, Function(Any, Any)),
    "*": Function(Integer, Function(Integer, Integer)),
    "<": Function(Any, Function(Any, Bool)),
    "-": Function(Integer, Integer),
}


def analyse(node, env, non_generic=None):
    if non_generic is None:
        non_generic = set()

    match node:
        case ir.Module(block):
            module_types = {}
            instrs = []
            for instr in block.instrs:
                instr = analyse(instr, env, non_generic)
                if isinstance(instr, tir.Declare):
                    module_types[instr.ref.name] = instr.typ
                instrs.append(instr)
            module_type = TypeRow(module_types)
            return tir.Module(tir.Block(instrs), typ=module_type)
        case ir.Block():
            return analyse_block(node, env, non_generic)
        case ir.Instruction():
            return analyse_instruction(node, env, non_generic)
        # not in use
        case ir.StructLiteral():
            struct_ref = analyse(node.typ, env, non_generic)
            row = TypeRow({
                name: analyse(obj, env, non_generic)
                for name, obj in node.fields.items()
            }, TypeVariable())
            unify(row, struct_ref)
            return row
        case ir.Ref():
            return lookup_ref(node, env, non_generic)
        case ir.Constant():
            typ = type_map[node.typ.value.value]
            if typ == None_:
                typ = Optional()
            return tir.Constant(node.value, typ=typ)
        case _:
            raise Exception(node)


def analyse_block(node, env, non_generic):
    if node in env:
        return env[node]
    block_type = TypeVariable()
    block = tir.Block(None, typ=block_type)
    env[node] = block
    instrs = []
    for i, instr in enumerate(node.instrs):
        instr = analyse(instr, env, non_generic)
        instrs.append(instr)
        if isinstance(instr, (tir.Branch, tir.CBranch)):
            unify(block_type, instr.typ)
        elif isinstance(instr, tir.Return):
            unify(block_type, instr.typ)
            # TODO: handle properly instead of asserting
            assert i == len(node.instrs) - 1, "Return not last instruction in block"
    block.instrs = instrs
    return block


def analyse_instruction(node, env, non_generic):
    tir_node = None
    match node:
        case ir.Assign(target, value):
            target = analyse(target, env, non_generic)
            value = analyse(value, env, non_generic)
            unify(target.typ, value.typ)
            tir_node = tir.Assign(target, value, typ=target.typ)
        case ir.Binary(op, lhs, rhs):
            target_type = operator_table[op]
            args = []
            for arg in [lhs, rhs]:
                value = analyse(arg, env, non_generic)
                args.append(value)
                result_type = TypeVariable()
                unify(Function(value.typ, result_type), target_type)
                target_type = result_type
            # TODO: should we convert this into a function call to the op
            tir_node = tir.Binary(op, *args, typ=result_type)
        case ir.Unary(op, rhs):
            target_type = operator_table[op]
            arg = analyse(rhs, env, non_generic)
            result_type = TypeVariable()
            unify(Function(arg.typ, result_type), target_type)
            # TODO: should we convert this into a function call to the op
            tir_node = tir.Unary(op, arg, typ=result_type)
        case ir.Branch(block):
            block = analyse(block, env, non_generic)
            tir_node = tir.Branch(block, typ=block.typ)
        case ir.CBranch(cond, t_block, f_block):
            cond = analyse(cond, env, non_generic)
            unify(cond.typ, Bool)
            t_block = analyse(t_block, env, non_generic)
            f_block = analyse(f_block, env, non_generic)
            unify(t_block.typ, f_block.typ)
            tir_node = tir.CBranch(cond, t_block, f_block, typ=t_block.typ)
        case ir.Call(target, args):
            ir_target = target
            target = analyse(target, env, non_generic)
            if isinstance((s := prune(target.typ)), TypeRow):
                fields = {}
                args = [analyse(arg, env, non_generic) for arg in args]
                for i, field in enumerate(s.fields):
                    if isinstance(prune(s.fields[field]), Function):
                        continue
                    fields[field] = args[i]
                field_types = {k: v.typ for k, v in fields.items()}
                result = TypeRow(field_types, TypeVariable())
                unify(result, target.typ)
                tir_node = tir.StructLiteral(fields, typ=result)
            else:
                # TODO: need to account for methods (add the parent as arg 0)
                target_type = target.typ
                if isinstance(target, (tir.MethodRef, tir.FieldRef)):
                    args.insert(0, ir_target.parent)
                tir_args = []
                for arg in args:
                    arg = analyse(arg, env, non_generic)
                    result_type = TypeVariable()
                    unify(Function(arg.typ, result_type), target_type)
                    tir_args.append(arg)
                    target_type = result_type
                tir_node = tir.Call(target, tir_args, typ=target_type)
        case ir.Declare(ref):
            if isinstance(ref, ir.FunctionRef):
                tir_node = declare_function(ref, env, non_generic)
            elif isinstance(ref, ir.StructRef):
                tir_node = declare_struct(ref, env, non_generic)
            else:
                tir_node = analyse(ref, env, non_generic)
            tir_node = tir.Declare(tir_node, typ=tir_node.typ)
        case ir.DeclareMethods(ref, block):
            ref = analyse(ref, env, non_generic)
            temp_non_generic = non_generic.copy()
            temp_non_generic.add(ref.typ)
            block = analyse(block, env, temp_non_generic)
            method_types = {i.ref.name: i.ref.typ for i in block.instrs}
            method_row = TypeRow(method_types, TypeVariable())
            unify(ref.typ, method_row)
            tir_node = tir.DeclareMethods(ref, block, typ=ref.typ)
        case ir.Load(ref):
            ref = analyse(ref, env, non_generic)
            tir_node = tir.Load(ref, typ=ref.typ)
        case ir.Return(value):
            value = analyse(value, env, non_generic)
            tir_node = tir.Return(value, typ=value.typ)
    return tir_node

def declare_function(ref, env, non_generic):
    params = []
    for param in ref.params:
        tir_param = analyse(param, env, non_generic)
        if param.typ is not None:
            type_hint = analyse(param.typ, env, non_generic)
            unify(tir_param.typ, type_hint.typ)
        params.append(tir_param)
    if len(params) == 0:
        params = [tir.VoidDummy(typ=Void)]
    return_type = TypeVariable()  # TODO: annotated return type not checked here
    func_type = Function(params[-1].typ, return_type)
    for param in params[-2::-1]:
        func_type = Function(param.typ, func_type)
    func = tir.FunctionRef(ref.name, params=params, typ=func_type)
    if ref in env:
        unify(func.typ, env[ref].typ)
    else:
        env[ref] = func
    temp_env = env.copy()
    temp_non_generic = non_generic.copy()
    temp_non_generic.add(func_type)
    for ir_param, tir_param in zip(ref.params, params):
        temp_env[ir_param] = tir_param
        temp_non_generic.add(tir_param.typ)
    block = analyse(ref.block, temp_env, temp_non_generic)
    unify(return_type, block.typ)
    func.block = block
    return func


def declare_struct(ref, env, non_generic):
    fields = {
        name: analyse(field, env, non_generic)
        for name, field in ref.fields.items()
    }
    methods = {
        name: analyse(method, env, non_generic)
        for name, method in ref.methods.items()
    }
    row_inner_type = {k: v.typ for k, v in (fields | methods).items()}
    row = TypeRow(row_inner_type)
    struct_type = tir.Type(ref.name, typ=row)
    env[ref] = struct_type
    # TODO: feels wrong?
    #       maybe make an empty subclass just to have the named type
    return struct_type

def lookup_ref(node, env, non_generic):
    if node in env:
        pass
    elif isinstance(node, ir.FieldRef):
        parent = analyse(node.parent, env, non_generic)
        node_type = TypeVariable()
        unify(TypeRow({node.name: node_type}, TypeVariable()), parent.typ)
        if isinstance(prune(node_type), Function):
            env[node] = tir.MethodRef(node.name, parent, typ=node_type)
        else:
            env[node] = tir.FieldRef(node.name, parent, typ=node_type)
    else:
        node_type = TypeVariable()
        env[node] = tir.Ref(node.name, typ=node_type)
    return env[node]


def unify(t1, t2):
    a = prune(t1)
    b = prune(t2)
    if a == b:
        return
    elif isinstance(a, Optional):
        if isinstance(b, Optional):
            return unify(a.fields["some"], b.fields["some"])
        elif t2 != b:
            unify(a.fields["some"], b)
        t2.forwarded = a
    elif isinstance(b, Optional):
        unify(t2, t1)
    elif isinstance(a, TypeVariable):
        if a != b:
            if occurs_in_type(a, b):
                raise InferenceError("Recursive unification")
            a.forwarded = b
    elif isinstance(b, TypeVariable):
        unify(b, a)
    elif isinstance(a, TypeConstructor) and isinstance(b, TypeConstructor):
        if a.name != b.name or len(a.types) != len(b.types):
            raise InferenceError(f"Type mismatch: {str(a)} != {str(b)}")
        for p, q in zip(a.types, b.types):
            unify(p, q)
    elif isinstance(a, EmptyRow) and isinstance(b, EmptyRow):
        return
    elif isinstance(a, EmptyRow) and isinstance(b, TypeRow):
        unify(b, a)
    elif isinstance(a, TypeRow) and isinstance(b, EmptyRow):
        raise InferenceError("Cannot unify EmptyRow and TypeRow")
    elif isinstance(a, TypeRow) and isinstance(b, TypeRow):
        a_rest, a_fields = row_flatten(a)
        b_rest, b_fields = row_flatten(b)
        a_keys = set(a_fields.keys())
        b_keys = set(b_fields.keys())

        a_missing = {key: b_fields[key] for key in b_keys - a_keys}
        b_missing = {key: a_fields[key] for key in a_keys - b_keys}

        for key in a_keys & b_keys:
            unify(a_fields[key], b_fields[key])

        if a_keys == b_keys:
            unify(a_rest, b_rest)
        elif b_keys - a_keys and a_keys - b_keys:
            rest = TypeVariable()
            unify(a_rest, TypeRow(a_missing, rest))
            unify(b_rest, TypeRow(b_missing, rest))
        elif b_keys - a_keys:
            unify(a_rest, TypeRow(a_missing, b_rest))
        elif a_keys - b_keys:
            unify(b_rest, TypeRow(b_missing, a_rest))
    else:
        assert False, "Not unified"


def prune(t):
    if isinstance(t, TypeVariable):
        if t.forwarded is not None:
            t.forwarded = prune(t.forwarded)
            return t.forwarded
    return t


def row_flatten(t):
    row = prune(t)
    if isinstance(row, TypeVariable) or isinstance(row, EmptyRow):
        return row, {}
    elif isinstance(row, TypeRow):
        rest, flat = row_flatten(row.rest)
        return rest, (flat | row.fields)
    raise InferenceError(f"Attempted to flatten non-Row type: {row}")


def occurs_in_type(v, type2):
    pruned_type2 = prune(type2)
    if pruned_type2 == v:
        return True
    elif isinstance(pruned_type2, TypeConstructor):
        return occurs_in(v, pruned_type2.types)
    return False


def occurs_in(t, types):
    return any(occurs_in_type(t, t2) for t2 in types)


class InferenceError(Exception):
    def __init__(self, message):
        self.__message = message

    message = property(lambda self: self.__message)

    def __str__(self):
        return str(self.message)


def main():
    filename = sys.argv[1]
    with open(filename) as f:
        src = f.read()
    ir = cmd.translate(src, filename=filename, make_ir=True)
    program = analyse(ir, {})
    print("\n".join(f"{name}:\t{t}" for name, t in program.typ.fields.items()))
    printer = tir.IRPrinter()
    print(printer.to_string(program))


if __name__ == "__main__":
    main()
