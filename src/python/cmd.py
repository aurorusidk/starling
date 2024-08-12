# this shadows a python module name but it hopefully doesn't matter
from .lexer import tokenise
from .parser import parse
from .ir import IRNoder
from .ir_nodes import IRPrinter
from .type_checker import TypeChecker
from .interpreter import Interpreter, StaFunctionReturn
from .compiler import Compiler, execute_ir
from .control_flows import ControlFlows, create_flows


def translate(src, cfpath, **flags):
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
    if flags.get("make_ir"):
        print(IRPrinter().to_string(iir))
        return iir
    tc = TypeChecker()
    tc.check(iir)
    if flags.get("typecheck"):
        print(IRPrinter().to_string(iir))
        if flags.get("cf_diagram"):
            flows = create_flows(block)
            cf = ControlFlows(flows)
            cf.draw_flow()
            if cfpath is not None:
                cf.save_flow(cfpath)
        return iir
    return iir


def exec_file(path, cfpath, **flags):
    with open(path) as f:
        src = f.read()
    iir = translate(src, cfpath)
    interpreter = Interpreter()
    interpreter.eval_node(iir)
    # define entry point
    if (fn := interpreter.scope.lookup("main")):
        try:
            interpreter.eval_node(fn.block)
        except StaFunctionReturn as res:
            print(f"program returned with value {res.value}")


def compile_file(path, cfpath, **flags):
    with open(path) as f:
        src = f.read()
    iir = translate(src, cfpath)
    compiler = Compiler()
    compiler.build_node(iir)
    print(compiler.module)
    res = execute_ir(str(compiler.module))
    print("program exited with code:", res)
