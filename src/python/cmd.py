# this shadows a python module name but it hopefully doesn't matter
import logging
from .lexer import tokenise
from .parser import Parser
from .ir import IRNoder
from .ir_nodes import IRPrinter, counter
from .type_checker import TypeChecker
from .interpreter import Interpreter, StaFunctionReturn
from .compiler import Compiler, execute_ir
from .control_flows import ControlFlows, create_flows


def translate(src, **flags):
    tokens = tokenise(src)
    if flags.get("tokenise"):
        return tokens
    if flags.get("parse") and flags.get("test"):
        parser = Parser(tokens, (lambda err: logging.error(err)))
    else:
        parser = Parser(tokens)
    ast = parser.parse_program()
    if flags.get("parse"):
        return ast

    noder = IRNoder()
    block = noder.block
    iir = noder.make(ast)
    if flags.get("cf_show") or (flags.get("cf_path") is not None):
        process_cf(block, flags.get("cf_path"), flags.get("cf_show"), flags.get("test"))
    printer = IRPrinter(test=flags.get("test"))
    if flags.get("make_ir"):
        printer.show_types = False
        iir_string = printer.to_string(iir)
        return iir_string
    tc = TypeChecker()
    tc.check(iir)
    if flags.get("typecheck"):
        iir_string = printer.to_string(iir)
        return iir_string

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


def process_cf(block, path, show, test):
    if test:
        flows = create_flows(block, counter())
    else:
        flows = create_flows(block)
    cf = ControlFlows(flows)
    cf.draw_flow(show)
    if path is not None:
        cf.save_flow(path)
