from dataclasses import dataclass
from fractions import Fraction
import logging

from .lexer import TokenType as T, tokenise
from .parser import Parser, parse
from .type_checker import TypeChecker
from . import ir_nodes as ir
from . import ast_nodes as ast
from . import type_defs as types
from . import builtin


@dataclass
class StaObject:
    value: object


@dataclass
class StaArray(StaObject):
    typ: types.ArrayType
    value: list[StaObject]
    length: int


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
    sig: ir.FunctionSignatureRef
    block: ir.Block = None


@dataclass
class StaMethod(StaFunction):
    target: StaObject = None
    # target will be set when the method is called


@dataclass
class StaStruct:
    typ: types.StructType
    name: str
    fields: dict[str, StaVariable]


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


#StaPrintFunc = StaBuiltinFunction(
#    builtin.names["print"],
#    "print",
#    [StaParameter(builtin.types["str"], ast.Identifier("string"))],
#    sta_print,
#)

#StaBuiltins = {
#    "print": StaPrintFunc,
#}


class Interpreter:
    def __init__(self):
        self.refs = {}
        self.entry = None

    def eval_node(self, node, **kwargs):
        match node:
            case ir.Ref():
                return self.eval_ref(node)
            case ir.Instruction():
                return self.eval_instr(node)
            case ir.Object():
                return self.eval_object(node)
            case _:
                assert False, f"Unreachable: {node}"

    def eval_ref(self, node):
        # using id() to get a unique hashable object for refs
        if id(node) not in self.refs:
            # make a new object for the ref
            match node:
                case ir.FunctionSignatureRef():
                    obj = StaFunction(node)
                case ir.StructTypeRef():
                    raise NotImplementedError
                case ir.FieldRef():
                    raise NotImplementedError
                case ir.Ref():
                    obj = StaVariable(node.name)
            return obj
        else:
            return self.refs[id(node)]
        raise NotImplementedError

    def eval_instr(self, node):
        match node:
            case ir.Declare(ref):
                var = self.eval_node(ref)
                self.refs[id(ref)] = var
            case ir.Assign(ref, value):
                var = self.eval_node(ref)
                val = self.eval_node(value)
                var.value = val
            case ir.Load(ref):
                var = self.eval_node(ref)
                return var.value
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
            case ir.DefFunc(target, block, scope):
                func = self.eval_node(target)
                self.refs[id(target)] = func
                if func.sig.name == "main":
                    self.entry = func
                func.block = block
            case ir.Binary():
                return self.eval_binary(node)
            case ir.Unary():
                return self.eval_unary(node)
            case _:
                assert False, f"Unexpected instruction {node}"

    def eval_object(self, node):
        match node:
            case ir.Block(instrs) | ir.Program(instrs):
                for instr in instrs:
                    self.eval_node(instr)
            case ir.Constant(value):
                return StaObject(value)
            case _:
                assert False

    def eval_binary(self, node):
        lhs = self.eval_node(node.lhs).value
        rhs = self.eval_node(node.rhs).value
        match node.op:
            case '+':
                return StaObject(lhs + rhs)
            case '-':
                return StaObject(lhs - rhs)
            case '*':
                return StaObject(lhs * rhs)
            case '/':
                return StaObject(lhs / rhs)
            case '==':
                return StaObject(lhs == rhs)
            case '!=':
                return StaObject(lhs != rhs)
            case '>':
                return StaObject(lhs > rhs)
            case '<':
                return StaObject(lhs < rhs)
            case '>=':
                return StaObject(lhs >= rhs)
            case '<=':
                return StaObject(lhs <= rhs)
            case _:
                assert False


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
