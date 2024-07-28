# this shadows a python module name but it hopefully doesn't matter
from .lexer import tokenise
from .parser import parse
from .type_checker import TypeChecker
from .interpreter import Interpreter, StaFunctionReturn
from .compiler import Compiler


def exec_file(path):
    with open(path) as f:
        src = f.read()
    tokens = tokenise(src)
    ast = parse(tokens)
    tc = TypeChecker(ast)
    tc.check(tc.root)
    interpreter = Interpreter()
    interpreter.eval_node(ast)
    # define entry point
    if (fn := interpreter.scope.lookup("main")):
        try:
            interpreter.eval_node(fn.block)
        except StaFunctionReturn as res:
            print(f"program returned with value {res.value}")

def compile_file(path):
    with open(path) as f:
        src = f.read()
    tokens = tokenise(src)
    ast = parse(tokens)
    tc = TypeChecker(ast)
    tc.check(tc.root)
    compiler = Compiler()
    compiler.compile(ast)
    # TODO: build the ir
