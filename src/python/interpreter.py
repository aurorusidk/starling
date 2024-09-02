from dataclasses import dataclass
import logging

from .lexer import tokenise
from .parser import Parser, parse
from .type_checker import TypeChecker
from . import ir_nodes as ir
from . import type_defs as types
from . import builtin


@dataclass
class StaObject:
    typ: types.Type
    value: object


@dataclass
class StaArray(StaObject):
    value: list[StaObject]


@dataclass
class StaVector(StaObject):
    value: list[StaObject]


@dataclass
class StaVariable:
    name: str
    value: StaObject = None


@dataclass
class StaParameter:
    typ: types.Type
    name: str


@dataclass
class StaFunction:
    sig: ir.FunctionSigRef
    params: list[ir.Ref]
    block: ir.Block


@dataclass
class StaMethod(StaFunction):
    target: StaObject = None
    # target will be set when the method is called


@dataclass
class StaStruct(StaObject):
    value: dict[str, StaVariable]


class StaBuiltinFunction(StaFunction):
    pass


class StaException(Exception):
    pass


class StaInternalException(StaException):
    pass


class StaFunctionReturn(StaInternalException):
    def __init__(self, value):
        self.value = value
        super().__init__()


class StaTypeError(StaException):
    pass


class StaNameError(StaException):
    pass


class StaValueError(StaException):
    pass


def sta_print(string):
    print(string.value)


# StaPrintFunc = StaBuiltinFunction(
#     builtin.names["print"],
#     "print",
#     [StaParameter(builtin.types["str"], ast.Identifier("string"))],
#     sta_print,
# )

# StaBuiltins = {
#     "print": StaPrintFunc,
# }


class Interpreter:
    def __init__(self, entry_name="main"):
        self.refs = {}
        self.entry_name = entry_name
        self.entry = None

    def eval_node(self, node, **kwargs):
        match node:
            case ir.Type():
                return self.eval_type(node)
            case ir.Ref():
                return self.eval_ref(node)
            case ir.Instruction():
                return self.eval_instr(node)
            case ir.Object():
                return self.eval_object(node)
            case _:
                assert False, f"Unreachable: {node}"

    def eval_type(self, node):
        return node.checked

    def eval_ref(self, node):
        # using id() to get a unique hashable object for refs
        if id(node) not in self.refs:
            # make a new object for the ref
            match node:
                case ir.FunctionRef():
                    if node.builtin:
                        obj = StaBuiltinFunction(node.typ, node.params, node.block)
                    else:
                        obj = StaFunction(node.typ, node.params, node.block)
                    if obj.sig.name == self.entry_name:
                        self.entry = obj
                case ir.StructRef():
                    return
                case ir.FieldRef():
                    if isinstance(node.typ, ir.FunctionSigRef):
                        obj = self.eval_node(node.method)
                    else:
                        struct = self.eval_node(node.parent).value
                        obj = struct.value[node.name]
                    self.refs[id(node)] = obj
                case ir.IndexRef():
                    sequence = self.eval_node(node.parent).value
                    index = self.eval_node(node.index).value
                    assert index >= 0 and index < len(sequence.value), \
                        f"Index {index} out of bounds for {node.parent.name}"
                    obj = sequence.value[index]
                case ir.Ref():
                    obj = StaVariable(node.name)
            return obj
        else:
            return self.refs[id(node)]

    def eval_instr(self, node):
        match node:
            case ir.Declare(ref):
                var = self.eval_node(ref)
                self.refs[id(ref)] = var
            case ir.DeclareMethods(typ, block):
                self.eval_node(block)
            case ir.Assign(ref, value):
                var = self.eval_node(ref)
                val = self.eval_node(value)
                var.value = val
            case ir.Load(ref):
                var = self.eval_node(ref)
                return var.value
            case ir.Call(ref, args):
                func = self.eval_node(ref)
                for param_ref, arg in zip(func.params, args):
                    param = self.eval_node(param_ref)
                    self.refs[id(param_ref)] = param
                    param.value = self.eval_node(arg)
                try:
                    if isinstance(func, StaBuiltinFunction):
                        self.call_builtin(func)
                    else:
                        self.eval_node(func.block)
                except StaFunctionReturn as res:
                    return res.value
            case ir.Return(value):
                val = self.eval_node(value)
                raise StaFunctionReturn(val)
            case ir.Branch(block):
                self.eval_node(block)
            case ir.CBranch(condition, t_block, f_block):
                cond = self.eval_node(condition)
                if cond.value:
                    self.eval_node(t_block)
                else:
                    self.eval_node(f_block)
            case ir.Binary():
                return self.eval_binary(node)
            case ir.Unary():
                return self.eval_unary(node)
            case _:
                assert False, f"Unexpected instruction {type(node)}"

    def eval_object(self, node):
        match node:
            case ir.Block(instrs):
                for instr in instrs:
                    self.eval_node(instr)
            case ir.Program(block):
                self.eval_node(block)
            case ir.Constant(value):
                return StaObject(self.eval_node(node.typ), value)
            case ir.Sequence(elements):
                elems = [self.eval_node(element) for element in elements]
                if isinstance(node.typ.checked, types.VectorType):
                    return StaVector(node.typ.checked, elems)
                else:
                    return StaArray(node.typ.checked, elems)
            case ir.StructLiteral(fields):
                vars = {}
                for name, value in fields.items():
                    vars[name] = StaVariable(name, self.eval_node(value))
                return StaStruct(self.eval_node(node.typ), vars)
            case _:
                assert False

    def eval_binary(self, node):
        lhs = self.eval_node(node.lhs).value
        rhs = self.eval_node(node.rhs).value
        match node.op:
            case '+':
                value = lhs + rhs
            case '-':
                value = lhs - rhs
            case '*':
                value = lhs * rhs
            case '/':
                value = lhs / rhs
            case '==':
                value = lhs == rhs
            case '!=':
                value = lhs != rhs
            case '>':
                value = lhs > rhs
            case '<':
                value = lhs < rhs
            case '>=':
                value = lhs >= rhs
            case '<=':
                value = lhs <= rhs
            case _:
                assert False
        return StaObject(self.eval_node(node.typ), value)

    def eval_unary(self, node):
        rhs = self.eval_node(node.rhs).value
        match node.op:
            case '-':
                value = -rhs
            case '!':
                value = not rhs
            case _:
                assert False
        return StaObject(self.eval_node(node.typ), value)

    def call_builtin(self, func):
        match func.sig.name:
            case "range_constructor@builtin":
                start = self.refs[id(func.params[0])].value.value
                end = self.refs[id(func.params[1])].value.value
                assert start < end, f"Range end {end} must be greater than start {start}"
                elements = [StaObject(builtin.scope.lookup("int"), i) for i in range(start, end)]
                raise StaFunctionReturn(
                    StaArray(types.ArrayType(builtin.scope.lookup("int"), end-start), elements)
                )
            case _:
                assert False, f"Unknown builtin function {func.sig.name}"


def repl(interpreter=None):
    if interpreter is None:
        interpreter = Interpreter()
    while (i := input(">")) != "exit()":
        tokens = tokenise(i)
        ast = Parser(tokens).parse_expression()
        try:
            result = interpreter.eval_node(ast)
        except StaException as e:
            print(f"{e.__class__.__name__}:", str(e))
        if result:
            sta_print(result)


def main(src_file=None):
    interpreter = Interpreter()
    if src_file is not None:
        with open(src_file) as f:
            src = f.read()
        tokens = tokenise(src)
        print(tokens)
        ast = parse(tokens)
        tc = TypeChecker(ast)
        tc.check(ast)
        interpreter.eval_node(ast)
        # define entry point
        if (f := interpreter.scope.lookup("main")):
            try:
                interpreter.eval_node(f.block)
            except StaFunctionReturn as res:
                print(f"program returned with value {res.value}")
    repl(interpreter)


if __name__ == "__main__":
    import sys

    logging.basicConfig(format="%(levelname)s: %(message)s")
    logging.getLogger().setLevel(logging.DEBUG)

    if len(sys.argv) == 2:
        src_file = sys.argv[1]
        main(src_file)
    else:
        main()
