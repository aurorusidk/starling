import sys

from . import builtin
from . import cmd
from . import ir_nodes as ir
from . import tir_nodes as tir


class TypeVariable:
    next_var_id = 0

    def __init__(self, name=None):
        self.id = TypeVariable.next_var_id
        TypeVariable.next_var_id += 1
        self.__name = name
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
                method_strings.append(f"{k} = {v}")
            else:
                field_strings.append(f"{k} = {v}")
        row_format = ", ".join(field_strings + method_strings)
        self._str = ""
        return f"{{{row_format}, ...{str(rest)}}}"


class TypeScheme:
    def __init__(self, tyvars, typ):
        self.tyvars = tyvars
        self.typ = typ

    def __str__(self):
        tyvars_string = ",".join(str(t) for t in self.tyvars)
        return f"∀{{{tyvars_string}}}.{self.typ}"


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
    "+": TypeScheme([Any], Function(Any, Function(Any, Any))),
    "*": TypeScheme([Integer], Function(Integer, Function(Integer, Integer))),
    "<": TypeScheme([Any], Function(Any, Function(Any, Bool))),
    "-": TypeScheme([Integer], Function(Integer, Integer)),
}

analysed_modules = {}


def analyse(node, env, non_generic=None):
    if non_generic is None:
        non_generic = set()

    match node:
        case ir.Module(block):
            if node.path in analysed_modules:
                return analysed_modules[node.path]
            deps = []
            for dep in reversed(node.dependencies):
                deps.append(analyse(dep, env, non_generic)[0])
            module_types = {}
            instrs = []
            for instr in block.instrs:
                instr, i_type = analyse(instr, env, non_generic)
                if isinstance(instr, tir.Declare):
                    module_types[instr.ref.name] = i_type
                instrs.append(instr)
            module_type = TypeRow(module_types)
            tir_node = tir.Module(tir.Block(instrs), typ=module_type)
            analysed_modules[node.path] = (tir_node, module_type)
            tir_node.dependencies = deps
            return tir_node, module_type
        case ir.Block():
            return analyse_block(node, env, non_generic)
        case ir.Instruction():
            return analyse_instruction(node, env, non_generic)
        case ir.ImportResult(value):
            # TODO: find a way of storing polymorphism in ImportResult type thing
            # (we want polymorphism to persist across imports,
            #  currently everything in an import gets instantiated when imported)
            # note that a.c and b.c have different versions of import_test
            import_struct, import_type = analyse(value, env, non_generic)
            return tir.ImportResult(import_struct), import_type
        case ir.StructLiteral():
            struct_ref, struct_type = analyse(node.typ, env, non_generic)
            row_fields = {}
            literal_fields = []
            for name, obj in node.fields.items():
                field_value, field_type = analyse(obj, env, non_generic)
                row_fields[name] = field_type
                literal_fields.append(field_value)
            row = TypeRow(row_fields, TypeVariable())
            unify(row, struct_type)
            return tir.StructLiteral(literal_fields), row
        case ir.Ref():
            return lookup_ref(node, env, non_generic)
        case ir.Constant():
            typ = type_map[node.typ.value.value]
            if typ == None_:
                typ = Optional()
            return tir.Constant(node.value, typ=typ), typ
        case _:
            raise Exception(node)


def analyse_block(node, env, non_generic):
    if node in env:
        return env[node]
    block_type = TypeVariable()
    block = tir.Block(None, typ=block_type)
    instrs = []
    for i, instr in enumerate(node.instrs):
        instr, i_type = analyse(instr, env, non_generic)
        instrs.append(instr)
        if isinstance(instr, (tir.Branch, tir.CBranch)):
            unify(block_type, i_type)
        elif isinstance(instr, tir.Return):
            unify(block_type, i_type)
            # TODO: handle properly instead of asserting
            assert i == len(node.instrs) - 1, "Return not last instruction in block"
    block.instrs = instrs
    return block, block_type


def analyse_instruction(node, env, non_generic):
    tir_node = None
    match node:
        case ir.Assign(target, value):
            target, t_type = analyse(target, env, non_generic)
            value, v_type = analyse(value, env, non_generic)
            unify(t_type, v_type)
            tir_node = tir.Assign(target, value, typ=t_type), t_type
        case ir.Binary(op, lhs, rhs):
            target_type = instantiate(operator_table[op])
            args = []
            for arg in [lhs, rhs]:
                value, v_type = analyse(arg, env, non_generic)
                args.append(value)
                result_type = TypeVariable()
                unify(Function(v_type, result_type), target_type)
                target_type = result_type
            # TODO: should we convert this into a function call to the op
            tir_node = tir.Binary(op, *args, typ=result_type), result_type
        case ir.Unary(op, rhs):
            target_type = operator_table[op]
            arg, a_type = analyse(rhs, env, non_generic)
            result_type = TypeVariable()
            unify(Function(a_type, result_type), target_type)
            # TODO: should we convert this into a function call to the op
            tir_node = tir.Unary(op, arg, typ=result_type), result_type
        case ir.Branch(block):
            block, b_type = analyse(block, env, non_generic)
            tir_node = tir.Branch(block, typ=b_type), b_type
        case ir.CBranch(cond, t_block, f_block):
            cond, c_type = analyse(cond, env, non_generic)
            unify(c_type, Bool)
            t_block, tb_type = analyse(t_block, env, non_generic)
            f_block, fb_type = analyse(f_block, env, non_generic)
            unify(tb_type, fb_type)
            tir_node = tir.CBranch(cond, t_block, f_block, typ=tb_type), tb_type
        case ir.Call(target, args):
            ir_target = target
            target, target_type = analyse(target, env, non_generic)
            if isinstance((s := prune(target_type)), TypeRow):
                fields = {}
                field_types = {}
                args = [analyse(arg, env, non_generic) for arg in args]
                for i, field in enumerate(s.fields):
                    if isinstance(prune(s.fields[field]), Function):
                        continue
                    fields[field] = args[i][0]
                    field_types[field] = args[i][1]
                result = TypeRow(field_types, TypeVariable())
                unify(result, target_type)
                tir_node = tir.StructLiteral(list(fields.values()), typ=result), result
            else:
                tir_args = []
                if not args:
                    result_type = TypeVariable()
                    unify(Function(Void, result_type), target_type)
                for arg in args:
                    arg, a_type = analyse(arg, env, non_generic)
                    result_type = TypeVariable()
                    unify(Function(a_type, result_type), target_type)
                    tir_args.append(arg)
                    target_type = result_type
                tir_node = tir.Call(target, tir_args, typ=result_type), result_type
        case ir.Declare(ref):
            if isinstance(ref, ir.FunctionRef):
                tir_node, n_type = declare_function(ref, env, non_generic)
                n_type = generalise(n_type, env)
                tir_node.typ = generalise(tir_node.typ, env)
            elif isinstance(ref, ir.StructRef):
                tir_node, n_type = declare_struct(ref, env, non_generic)
                n_type = TypeScheme([], n_type)  # manually create non-general TypeScheme
                # TODO: copy-pasted code is STILL bad!
            else:
                tir_node, n_type = analyse(ref, env, non_generic)
                n_type = TypeScheme([], n_type)  # manually create non-general TypeScheme
            env[ref] = tir_node, n_type
            tir_node = tir.Declare(tir_node, typ=n_type), n_type
        case ir.DeclareMethods(target, instance_ref, block):
            target, t_type = analyse(target, env, non_generic)
            ref, i_type = analyse(instance_ref, env, non_generic)
            unify(i_type, t_type)
            temp_non_generic = non_generic.copy()
            temp_non_generic.add(t_type)
            temp_env = env.copy()
            temp_env[instance_ref] = ref, generalise(i_type, env)
            block, b_type = analyse(block, temp_env, temp_non_generic)
            method_types = {i.ref.name: instantiate(i.ref.typ) for i in block.instrs}
            method_row = TypeRow(method_types, TypeVariable())
            unify(t_type, method_row)
            tir_node = tir.DeclareMethods(target, block, typ=t_type), t_type
        case ir.Load(ref):
            ref, r_type = analyse(ref, env, non_generic)
            tir_node = tir.Load(ref, typ=r_type), r_type
        case ir.Return(value):
            value, v_type = analyse(value, env, non_generic)
            tir_node = tir.Return(value, typ=v_type), v_type
    return tir_node


def declare_function(ref, env, non_generic):
    params = []
    param_types = []
    for param in ref.params:
        tir_param, p_type = analyse(param, env, non_generic)
        if param.typ is not None:
            type_hint, th_type = analyse(param.typ, env, non_generic)
            unify(p_type, th_type)
        params.append(tir_param)
        param_types.append(p_type)
    if len(params) == 0:
        params = [tir.VoidDummy(typ=Void)]
        param_types = [Void]
    return_type = TypeVariable()  # TODO: annotated return type not checked here
    func_type = Function(param_types[-1], return_type)
    for param in param_types[-2::-1]:
        func_type = Function(param, func_type)
    func = tir.FunctionRef(ref.name, params=params, typ=func_type)
    if ref in env:
        assert False, "why are we here"
        unify(func_type, env[ref][1])
    temp_env = env.copy()
    temp_env[ref] = func, generalise(func_type, env)
    temp_non_generic = non_generic.copy()
    temp_non_generic.add(func_type)
    for ir_param, tir_param, p_type in zip(ref.params, params, param_types):
        temp_env[ir_param] = tir_param, TypeScheme([], p_type)
        temp_non_generic.add(p_type)
    block, b_type = analyse(ref.block, temp_env, temp_non_generic)
    unify(return_type, b_type)
    func.block = block
    return func, func_type


def declare_struct(ref, env, non_generic):
    fields = {
        name: analyse(field, env, non_generic)
        for name, field in ref.fields.items()
    }
    methods = {
        name: analyse(method, env, non_generic)
        for name, method in ref.methods.items()
    }
    row_inner_type = {k: v[1] for k, v in (fields | methods).items()}
    row = TypeRow(row_inner_type)
    struct_type = tir.Type(ref.name, typ=row)
    # TODO: feels wrong?
    #       maybe make an empty subclass just to have the named type
    return struct_type, row


def lookup_ref(node, env, non_generic):
    if node in env:
        tir_node, node_type = env[node]
        return tir_node, instantiate(node_type)
    elif isinstance(node, ir.FieldRef):
        parent, p_type = analyse(node.parent, env, non_generic)
        node_type = TypeVariable()
        unify(TypeRow({node.name: node_type}, TypeVariable()), p_type)
        if isinstance(prune(node_type), Function):
            tir_node = tir.MethodRef(node.name, parent, typ=node_type)
        else:
            tir_node = tir.FieldRef(node.name, parent, typ=node_type)
    else:
        node_type = TypeVariable()
        tir_node = tir.Ref(node.name, typ=node_type)
    return tir_node, node_type


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
        missing = [name for name in a.fields]
        raise InferenceError(f"Cannot unify EmptyRow and TypeRow, expected field(s) {missing}")
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


def ftv_typ(typ):
    typ = prune(typ)
    if isinstance(typ, TypeVariable):
        return {typ.name}
    if isinstance(typ, TypeConstructor):
        # Unwrap both levels of iterable
        return set().union(*map(ftv_typ, typ.types))
    if isinstance(typ, EmptyRow):
        return set()
    if isinstance(typ, TypeRow):
        # Unwrap both levels of iterable
        return set().union(*map(ftv_typ, typ.fields.values()), ftv_typ(typ.rest))
    raise InferenceError(f"Unknown type: {typ}")


def ftv_scheme(scheme):
    return ftv_typ(scheme.typ) - set(tyvar.name for tyvar in scheme.tyvars)


def ftv_env(env):
    return set().union(*(ftv_scheme(ref[1]) for ref in env.values()))


def generalise(typ, env):
    tyvars = ftv_typ(typ) - ftv_env(env)
    return TypeScheme([TypeVariable(name) for name in sorted(tyvars)], typ)


def substitute_typ(typ, subst):
    typ = prune(typ)
    if isinstance(typ, TypeVariable):
        return subst.get(typ.name, typ)
    if isinstance(typ, Function):
        return Function(*[substitute_typ(t, subst) for t in typ.types])
    if isinstance(typ, TypeConstructor):
        return TypeConstructor(
            typ.name, [substitute_typ(t, subst) for t in typ.types]
        )
    if isinstance(typ, EmptyRow):
        return typ
    if isinstance(typ, TypeRow):
        rest = substitute_typ(typ.rest, subst)
        # assert isinstance(rest, (TypeVariable, EmptyRow))
        # TODO this is based on scrapscript but doesn't seem to be correct?
        return TypeRow(
            {k: substitute_typ(v, subst) for k, v in typ.fields.items()}, rest
        )
    raise InferenceError(f"Unknown type: {typ}")


def instantiate(scheme):
    fresh = {tyvar.name: TypeVariable() for tyvar in scheme.tyvars}
    return substitute_typ(scheme.typ, fresh)


class InferenceError(Exception):
    def __init__(self, message):
        self.__message = message

    message = property(lambda self: self.__message)

    def __str__(self):
        return str(self.message)


def type_check(ir):
    program, p_type = analyse(ir, {})
    return program


def main():
    filename = sys.argv[1]
    with open(filename) as f:
        src = f.read()
    ir = cmd.translate(src, filename=filename, make_ir=True)
    program = type_check(ir)
    print("\n".join(f"{name}:\t{t}" for name, t in program.typ.fields.items()))
    printer = tir.IRPrinter()
    for dep in program.dependencies:
        print(printer._to_string(dep))
        print("---")
    print(printer.to_string(program))


if __name__ == "__main__":
    main()
