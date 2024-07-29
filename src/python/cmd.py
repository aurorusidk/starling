import llvmlite.binding as llvm
from ctypes import CFUNCTYPE, c_int

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
    compiler.build_node(ast)

    llvm.initialize()
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()
    target = llvm.Target.from_default_triple()
    target_machine = target.create_target_machine()
    backing_mod = llvm.parse_assembly("")
    engine = llvm.create_mcjit_compiler(backing_mod, target_machine)

    print(compiler.module)
    mod = llvm.parse_assembly(str(compiler.module))
    mod.verify()
    engine.add_module(mod)
    engine.finalize_object()
    engine.run_static_constructors()

    func_ptr = engine.get_function_address("main")
    cfunc = CFUNCTYPE(c_int)(func_ptr)
    res = cfunc()
    print("program exited with code:", res)
