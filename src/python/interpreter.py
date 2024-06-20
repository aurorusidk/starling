from collections import namedtuple
import logging

from lexer import TokenType as T, tokenise
from parser import NodeType as N, Parser, parse

# move these to classes if additional behaviour is needed
StarlingParameter = namedtuple("Parameter", ["name", "typ"])
StarlingVariable = namedtuple("Variable", ["name", "value"])


class StarlingFunction:
    def __init__(self, name, typ, params, block):
        self.name = name
        self.typ = typ
        self.params = params
        self.block = block

class StarlingBuiltinFunction(StarlingFunction):
    pass


class StarlingType:
    pass


class StarlingInteger(StarlingType):
    typ = "int"
    def __init__(self, value):
        self.value = int(value)


class StarlingFloat(StarlingType):
    typ = "float"
    def __init__(self, value):
        self.value = float(value)


class StarlingString(StarlingType):
    typ = "str"
    def __init__(self, value):
        self.value = str(value)


class StarlingBool(StarlingType):
    typ = "bool"
    def __init__(self, value):
        self.value = str(value)


class StarlingException(Exception):
    pass


class StarlingInternalException(StarlingException):
    pass


class StarlingFunctionReturn(StarlingInternalException):
    def __init__(self, value):
        self.value = value
        super().__init__()


class StarlingTypeError(StarlingException):
    pass


class StarlingNameError(StarlingException):
    pass


def StarlingPrint(string):
    print(string.value)

StarlingPrintFunc = StarlingBuiltinFunction(
    "print", None, [StarlingParameter("string", StarlingString)], StarlingPrint
)

StarlingBuiltins = {
    "print": StarlingPrintFunc
}


class Interpreter:
    def __init__(self):
        self.name_map = StarlingBuiltins

    def eval_node(self, node, **kwargs):
        method = getattr(self, f"eval_{node.typ.name.lower()}")
        return method(*node.children, **kwargs)

    def eval_program(self, *declrs):
        logging.debug(f"{declrs}")
        for declr in declrs:
            self.eval_node(declr)

    def eval_function(self, ftype, fname, ptypes, pnames, block):
        logging.debug(f"{fname}, {ftype}")
        params = []
        for pname, ptype in zip(pnames, ptypes):
            params.append(StarlingParameter(pname, self.eval_node(ptype)))
        ftype = self.eval_node(ftype)
        func = StarlingFunction(fname, ftype, params, block)
        self.name_map[fname] = func

    def eval_type(self, value):
        match value.typ:
            case T.INTEGER_TYPE:
                return StarlingInteger
            case T.FLOAT_TYPE:
                return StarlingFloat
            case T.STRING_TYPE:
                return StarlingString
            case T.BOOL_TYPE:
                return StarlingBool
            case _:
                assert False, f"Unimplemented type: {value.typ}"

    def eval_block(self, *stmts, **local_vars):
        outer_scope = self.name_map
        for stmt in stmts:
            self.eval_node(stmt)
        self.name_map = outer_scope

    def eval_if(self, condition, if_block, else_block):
        if self.eval_node(condition):
            self.eval_node(if_block)
        elif else_block is not None:
            self.eval_node(else_block)

    def eval_while(self, condition, while_block):
        while self.eval_node(condition):
            self.eval_node(while_block)

    def eval_return(self, value):
        value = self.eval_node(value)
        raise StarlingFunctionReturn(value)

    def eval_assignment(self, name, value):
        name = name.lexeme
        value = self.eval_node(value)
        var = StarlingVariable(name, value)
        self.name_map[name] = value

    def eval_binary_expr(self, op, left, right):
        left = self.eval_node(left)
        right = self.eval_node(right)
        match op.typ:
            case T.PLUS:
                return left + right
            case _:
                assert False, f"Unimplemented operator: {op.typ}"

    def eval_unary_expr(self, op, right):
        right = self.eval_node(right)
        match op.typ:
            case _:
                assert False, f"Unimplemented operator: {op.typ}"

    def eval_primary(self, value):
        match value.typ:
            case T.INTEGER:
                return StarlingInteger(value.lexeme)
            case T.FLOAT:
                return StarlingFloat(value.lexeme)
            case T.STRING:
                return StarlingString(value.lexeme[1:-1])
            case T.BOOL:
                return StarlingBool(value.lexeme)
            case T.IDENTIFIER:
                if value.value not in self.name_map:
                    raise StarlingNameError(f"Name {value.value} not defined")
                return self.name_map[value.value]

    def eval_call(self, callee, args):
        logging.debug("evaluating call")
        fname = callee.lexeme
        func = self.name_map.get(fname)
        if not isinstance(func, StarlingFunction):
            raise StarlingTypeError(f"{fname} is not a function")
        if len(func.params) != len(args):
            raise StarlingTypeError(
                f"{fname} takes {len(func.params)} but {len(args)} provided"
            )
        local_vars = {}
        for arg, param in zip(args, func.params):
            logging.debug(f"{param.typ}")
            value = self.eval_node(arg)
            if not isinstance(value, param.typ):
                raise StarlingTypeError(
                    f"Expected type {ptype} for parameter {param.name} \
                    but got {value.typ}"
                )
            local_vars[param.name] = value
        logging.debug(f"{func.block}")
        if isinstance(func, StarlingBuiltinFunction):
            logging.debug(f"calling builtin {fname}")
            return func.block(**local_vars)
        try:
            self.eval_node(func.block, local_vars=local_vars)
        except StarlingFunctionReturn as res:
            return res.value

    def eval_group_expr(self, expr):
        return self.eval_node(expr)


def repl(ast):
    interpreter = Interpreter()
    interpreter.eval_node(ast)
    while (i := input(">")) != "exit()":
        tokens = tokenise(i)
        ast = Parser(tokens).parse_expression()
        print(interpreter.eval_node(ast))


if __name__ == "__main__":
    import sys
    from parser import repr_ast

    logging.basicConfig(format="%(levelname)s: %(message)s")
    logging.getLogger().setLevel(logging.DEBUG)
    if len(sys.argv) == 2:
        src_file = sys.argv[1]
    else:
        src_file = "input.txt"
    with open(src_file) as f:
        src = f.read()
    tokens = tokenise(src)
    print(tokens)
    ast = parse(tokens)
    print(repr_ast(ast))
    repl(ast)
