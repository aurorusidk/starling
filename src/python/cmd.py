# this shadows a python module name but it hopefully doesn't matter
from .lexer import tokenise
from .parser import parse
from .ir import IRNoder
from .ir_nodes import IRPrinter
from .type_checker import TypeChecker
from .interpreter import Interpreter, StaFunctionReturn
from .compiler import Compiler, execute_ir
from .control_flows import ControlFlows, create_flows


def translate(src, **flags):
    tokens = tokenise(src)
    if flags.get("tokenise"):
        print(tokens)
        return tokens
    ast = parse(tokens)
    if flags.get("parse"):
        print(ast)
        return ast
    noder = IRNoder()
    block = noder.block
    iir = noder.make(ast)
    if flags.get("cf_show") or (flags.get("cf_path") is not None):
        process_cf(block, flags.get("cf_path"), flags.get("cf_show"))
    if flags.get("make_ir"):
        printer = IRPrinter()
        if flags.get("test"):
            printer.is_test()
            # print(printer.to_string(iir))
            return printer.to_string(iir)
        print(printer.to_string(iir))
        return iir
    tc = TypeChecker()
    tc.check(iir)
    if flags.get("typecheck"):
        print(IRPrinter().to_string(iir))
        return iir
    return iir


def exec_file(path, **flags):
    with open(path) as f:
        src = f.read()
    iir = translate(src, **flags)
    interpreter = Interpreter()
    interpreter.eval_node(iir)
    # define entry point
    if (fn := interpreter.entry):
        try:
            interpreter.eval_node(fn.block)
        except StaFunctionReturn as res:
            print(f"program returned with value {res.value}")


def compile_file(path, **flags):
    with open(path) as f:
        src = f.read()
    iir = translate(src, **flags)
    compiler = Compiler()
    compiler.build_node(iir)
    print(compiler.module)
    res = execute_ir(str(compiler.module))
    print("program exited with code:", res)


def process_cf(block, path, show):
    flows = create_flows(block)
    cf = ControlFlows(flows)
    cf.draw_flow(show)
    if path is not None:
        cf.save_flow(path)
