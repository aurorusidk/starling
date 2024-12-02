import logging

from .lexer import tokenise
from .parser import Parser
from .ir import IRNoder
from .ir_nodes import IRPrinter, counter
from .type_checker import TypeChecker
from .interpreter import Interpreter, StaFunctionReturn
from .compiler import Compiler, execute_module
from .control_flows import ControlFlows, create_flows


def translate(src, **flags):
    error_handler = flags.get("error_handler")
    tokens = tokenise(src, error_handler)
    if flags.get("tokenise"):
        return tokens

    parser = Parser(tokens, error_handler)
    ast = parser.parse_program()
    if flags.get("parse"):
        return ast

    noder = IRNoder(error_handler)
    block = noder.block
    iir = noder.make(ast)
    if flags.get("cf_show") or (flags.get("cf_path") is not None):
        process_cf(block, flags.get("cf_path"), flags.get("cf_show"), flags.get("test"))
    printer = IRPrinter(test=flags.get("test"))
    if flags.get("make_ir"):
        printer.show_types = False
        iir_string = printer.to_string(iir)
        return iir_string

    tc = TypeChecker(error_handler)
    tc.check(iir)
    if flags.get("typecheck"):
        iir_string = printer.to_string(iir)
        return iir_string

    return iir


def exec_src(src, **flags):
    iir = translate(src, **flags)
    interpreter = Interpreter(entry_name=flags.get("entry_name", "main"))
    interpreter.eval_node(iir)
    # define entry point
    if (fn := interpreter.entry):
        try:
            interpreter.eval_node(fn.block)
        except StaFunctionReturn as res:
            return res.value


def compile_src(src, **flags):
    iir = translate(src, **flags)
    compiler = Compiler()
    compiler.build(iir)
    logging.debug(compiler.module)
    return compiler.module


def compile_and_run_src(src, **flags):
    mod = compile_src(src, **flags)
    res = execute_module(mod, entry=flags.get("entry_name", "main"))
    return res


def process_cf(block, path, show, test):
    if test:
        flows = create_flows(block, counter())
    else:
        flows = create_flows(block)
    cf = ControlFlows(flows)
    cf.draw_flow(show)
    if path is not None:
        cf.save_flow(path)
