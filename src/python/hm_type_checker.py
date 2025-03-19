import sys

from . import builtin
from . import cmd
from . import ir_nodes as ir


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


Void = TypeConstructor("void", [])
Integer = TypeConstructor("int", [])
Float = TypeConstructor("float", [])
Rational = TypeConstructor("frac", [])
Char = TypeConstructor("char", [])
Bool = TypeConstructor("bool", [])

Any = TypeVariable()

type_map = {
    builtin.types["int"]: Integer,
    builtin.types["float"]: Float,
    builtin.types["frac"]: Rational,
    builtin.types["char"]: Char,
    builtin.types["bool"]: Bool,
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
        case ir.Program(block):
            for instr in block.instrs:
                instr_type = analyse(instr, env, non_generic)
                print(instr_type)  # TODO: this is debug, remove later
            return analyse(block, env, non_generic)
            # TODO: make Program type correct (and useful for imports!!)
        case ir.Block():
            return analyse_block(node, env, non_generic)
        case ir.Instruction():
            return analyse_instruction(node, env, non_generic)
        case ir.Ref():
            return analyse_ref(node, env, non_generic)
        case ir.Constant():
            return type_map[node.typ.value.value]
        case _:
            raise Exception(node)


def analyse_block(node, env, non_generic):
    if node in env:
        return env[node]
    block_type = TypeVariable()
    env[node] = block_type
    for i, instr in enumerate(node.instrs):
        instr_type = analyse(instr, env, non_generic)
        if isinstance(instr, (ir.Branch, ir.CBranch)):
            unify(block_type, instr_type)
        elif isinstance(instr, ir.Return):
            unify(block_type, instr_type)
            # TODO: handle properly instead of asserting
            assert i == len(node.instrs) - 1, "Return not last instruction in block"
    return block_type


def analyse_instruction(node, env, non_generic):
    match node:
        case ir.Assign(target, value):
            target_type = analyse(target, env, non_generic)
            value_type = analyse(value, env, non_generic)
            unify(target_type, value_type)
            return target_type
        case ir.Binary(op, lhs, rhs):
            target_type = operator_table[op]
            for arg in [lhs, rhs]:
                arg_type = analyse(arg, env, non_generic)
                result_type = TypeVariable()
                unify(Function(arg_type, result_type), target_type)
                target_type = result_type
            return result_type
        case ir.Unary(op, rhs):
            target_type = operator_table[op]
            arg_type = analyse(rhs, env, non_generic)
            result_type = TypeVariable()
            unify(Function(arg_type, result_type), target_type)
            return result_type
        case ir.Branch(block):
            return analyse(block, env, non_generic)
        case ir.CBranch(_, t_block, f_block):
            t_block_type = analyse(t_block, env, non_generic)
            f_block_type = analyse(f_block, env, non_generic)
            unify(t_block_type, f_block_type)
            return t_block_type
        case ir.Call(target, args):
            target_type = analyse(target, env, non_generic)
            for arg in args:
                arg_type = analyse(arg, env, non_generic)
                result_type = TypeVariable()
                unify(Function(arg_type, result_type), target_type)
                target_type = result_type
            return result_type
        case ir.Declare(ref):
            if isinstance(ref, ir.FunctionRef):
                return declare_function(ref, env, non_generic)
            else:
                return analyse(ref, env, non_generic)
        case ir.Load(ref):
            return analyse(ref, env, non_generic)
        case ir.Return(value):
            return analyse(value, env, non_generic)


def declare_function(ref, env, non_generic):
    args = [analyse(param, env, non_generic) for param in ref.params]
    if len(args) == 0:
        args = [Void]
    return_type = TypeVariable()  # TODO: annotated return type not checked here
    func_type = Function(args[-1], return_type)
    for arg in args[-2::-1]:
        func_type = Function(arg, func_type)
    env[ref] = func_type
    temp_env = env.copy()
    temp_non_generic = non_generic.copy()
    temp_non_generic.add(func_type)
    for param, arg in zip(ref.params, args):
        temp_env[param] = arg
        temp_non_generic.add(arg)
    block_type = analyse(ref.block, temp_env, temp_non_generic)
    unify(return_type, block_type)
    return func_type


def analyse_ref(node, env, non_generic):
    if node in env:
        node_type = env[node]
    else:
        node_type = TypeVariable()
        env[node] = node_type
    return node_type


def unify(t1, t2):
    a = prune(t1)
    b = prune(t2)
    if isinstance(a, TypeVariable):
        if a != b:
            if occurs_in_type(a, b):
                raise InferenceError("Recursive unification")
            a.forwarded = b
    elif isinstance(a, TypeConstructor) and isinstance(b, TypeVariable):
        unify(b, a)
    elif isinstance(a, TypeConstructor) and isinstance(b, TypeConstructor):
        if a.name != b.name or len(a.types) != len(b.types):
            raise InferenceError(f"Type mismatch: {str(a)} != {str(b)}")
        for p, q in zip(a.types, b.types):
            unify(p, q)
    else:
        assert False, "Not unified"


def prune(t):
    if isinstance(t, TypeVariable):
        if t.forwarded is not None:
            t.forwarded = prune(t.forwarded)
            return t.forwarded
    return t


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
    ir = cmd.translate(src, make_ir=True)
    checked = analyse(ir, {})
    print(checked)


if __name__ == "__main__":
    main()
