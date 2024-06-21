from collections import namedtuple
from dataclasses import dataclass
from enum import Enum
import logging

from lexer import TokenType as T, tokenise
from parser import NodeType as N, Parser, parse

# move these to classes if additional behaviour is needed
StarlingParameter = namedtuple("Parameter", ["name", "typ"])
StarlingVariable = namedtuple("Variable", ["name", "value"])
StarlingType = Enum("StarlingType", [
    "INTEGER", "FLOAT", "STRING", "BOOL",
])

@dataclass
class StarlingFunction:
    name: str
    typ: StarlingType
    params: list[StarlingParameter]
    block: tuple # node


class StarlingBuiltinFunction(StarlingFunction):
    pass


@dataclass
class StarlingObject:
    typ: StarlingType
    value: object


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


def starling_print(obj):
    print(starling_str(obj).value)

StarlingPrintFunc = StarlingBuiltinFunction(
    "print", None, [StarlingParameter("obj", StarlingType)], starling_print
)

def starling_str(obj):
    return StarlingObject(StarlingType.STRING, str(obj.value))

StarlingStrFunc = StarlingBuiltinFunction(
    "to_str", StarlingType.STRING,
    [StarlingParameter("obj", StarlingType)],
    starling_str
)


StarlingBuiltins = {
    "print": StarlingPrintFunc,
    "to_str": StarlingStrFunc,
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
                return StarlingType.INTEGER
            case T.FLOAT_TYPE:
                return StarlingType.FLOAT
            case T.STRING_TYPE:
                return StarlingType.STRING
            case T.BOOL_TYPE:
                return StarlingType.BOOL
            case _:
                assert False, f"Unimplemented type: {value.typ}"

    def eval_block(self, *stmts, local_vars):
        logging.debug(f"outer scope: {self.name_map}")
        outer_scope = self.name_map
        self.name_map |= local_vars
        logging.debug(f"inner scope: {self.name_map}")
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
        assert type(left) == type(right), "Type coercion not implemented"
        match op.typ:
            case T.PLUS:
                return self.eval_add(left, right)
            case T.MINUS:
                return self.eval_sub(left, right)
            case T.STAR:
                return self.eval_mul(left, right)
            case T.SLASH:
                return self.eval_div(left, right)
            case _:
                assert False, f"Unimplemented operator: {op.typ}"

    def eval_add(self, left, right):
        return type(left)(left.value + right.value)

    def eval_sub(self, left, right):
        if isinstance(left, StarlingString):
            raise StarlingTypeError("Subtraction not supported on type str")
        return type(left)(left.value - right.value)

    def eval_mul(self, left, right):
        if not isinstance(left, (StarlingInteger, StarlingFloat)):
            raise StarlingTypeError(
                f"Multiplication not supported on type {type(left).name}"
            )
        return type(left)(left.value * right.value)

    def eval_div(self, left, right):
        if not isinstance(left, (StarlingInteger, StarlingFloat)):
            raise StarlingTypeError(
                f"Division not supported on type {type(left).name}"
            )
        return type(left)(left.value / right.value)

    def eval_unary_expr(self, op, right):
        right = self.eval_node(right)
        match op.typ:
            case T.BANG:
                return self.eval_not(right)
            case T.MINUS:
                return self.eval_neg(right)
            case _:
                assert False, f"Unimplemented operator: {op.typ}"

    def eval_not(self, right):
        return type(right)(not right.value)

    def eval_neg(self, right):
        if not isinstance(right, (StarlingInteger, StarlingFloat)):
            raise StarlingTypeError(
                f"Negation not supported on type {type(right).name}"
            )
        return type(right)(-right.value)

    def eval_primary(self, value):
        match value.typ:
            case T.INTEGER:
                return StarlingObject(StarlingType.INTEGER, int(value.lexeme))
            case T.FLOAT:
                return StarlingObject(StarlingType.FLOAT, float(value.lexeme))
            case T.STRING:
                return StarlingObject(StarlingType.STRING, str(value.lexeme))
            case T.BOOL:
                return StarlingObject(StarlingType.BOOL, bool(value.lexeme))
            case T.IDENTIFIER:
                if value.lexeme not in self.name_map:
                    raise StarlingNameError(f"Name {value.lexeme} not defined")
                return self.name_map[value.lexeme]

    def eval_call(self, callee, args):
        logging.debug("evaluating call")
        fname = callee.lexeme
        func = self.name_map.get(fname)
        if not isinstance(func, StarlingFunction):
            raise StarlingTypeError(f"{fname} is not a function")
        if len(func.params) != len(args):
            raise StarlingTypeError(
                f"{fname} takes {len(func.params)} " \
                f"argument{'s' if len(func.params) != 1 else ''} " \
                f"but {len(args)} provided"
            )
        local_vars = {}
        for arg, param in zip(args, func.params):
            logging.debug(f"{param.typ}")
            value = self.eval_node(arg)
            if value.typ != param.typ and not isinstance(value.typ, param.typ):
                raise StarlingTypeError(
                    f"Expected type {param.typ} " \
                    f"for parameter '{param.name}' " \
                    f"but got {value.typ}"
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
        try:
            starling_print(interpreter.eval_node(ast))
        except StarlingException as e:
            print(f"{e.__class__.__name__}:", str(e))


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
