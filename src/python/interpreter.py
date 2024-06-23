from collections import namedtuple
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
import logging
from typing import Union

from lexer import TokenType as T, tokenise
from parser import NodeType as N, Parser, parse

# move these to classes if additional behaviour is needed
StaParameter = namedtuple("Parameter", ["name", "typ"])
StaVariable = namedtuple("Variable", ["name", "value"])
StaPrimitiveType = Enum("StaPrimitiveType", [
    "INTEGER", "FLOAT", "RATIONAL", "STRING", "BOOL",
])


@dataclass
class StaType:
    base_type: Union[StaPrimitiveType, "StaType"]

    def __repr__(self):
        return repr(self.base_type)


# define primitive types as objects
sta_integer_type = StaType(StaPrimitiveType.INTEGER)
sta_float_type = StaType(StaPrimitiveType.FLOAT)
sta_rational_type = StaType(StaPrimitiveType.RATIONAL)
sta_string_type = StaType(StaPrimitiveType.STRING)
sta_bool_type = StaType(StaPrimitiveType)


@dataclass
class StaArrayType(StaType):
    length: int


@dataclass
class StaObject:
    typ: StaType
    value: object


@dataclass
class StaArray(StaObject):
    typ: StaArrayType
    value: list[StaObject]
    length: int


@dataclass
class StaFunction:
    name: str
    typ: StaType
    params: list[StaParameter]
    block: tuple # node


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


def sta_print(obj):
    print(sta_str(obj).value)

StaPrintFunc = StaBuiltinFunction(
    "print", None, [StaParameter("obj", StaType)], sta_print
)

def sta_str(obj):
    return StaObject(sta_string_type, str(obj.value))

StaStrFunc = StaBuiltinFunction(
    "to_str", sta_string_type,
    [StaParameter("obj", StaType)],
    sta_str
)


StaBuiltins = {
    "print": StaPrintFunc,
    "to_str": StaStrFunc,
}


class Interpreter:
    def __init__(self):
        self.name_map = StaBuiltins

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
            params.append(StaParameter(pname, self.eval_node(ptype)))
        ftype = self.eval_node(ftype)
        func = StaFunction(fname, ftype, params, block)
        self.name_map[fname] = func

    def eval_variable_declr(self, typ, name, value):
        name = name
        value = self.eval_node(value)
        if typ is not None and value.typ != (t := self.eval_node(typ)):
            raise StaTypeError(
                f"Cannot assign value of type {value.typ}"\
                f"to variable with type {t}"
            )
        var = StaVariable(name, value)
        self.name_map[name] = value

    def eval_type(self, value):
        match value.typ:
            case T.INTEGER_TYPE:
                return sta_integer_type
            case T.FLOAT_TYPE:
                return sta_float_type
            case T.RATIONAL_TYPE:
                return sta_rational_type
            case T.STRING_TYPE:
                return sta_string_type
            case T.BOOL_TYPE:
                return sta_bool_type
            case _:
                assert False, f"Unimplemented type: {value.typ}"

    def eval_array_type(self, length, typ):
        length = self.eval_node(length)
        if length.typ != sta_integer_type:
            raise StaTypeError("Array length must be an integer")
        typ = self.eval_node(typ)
        return StaArrayType(typ, length.value)

    def eval_block(self, *stmts, local_vars=None):
        logging.debug(f"outer scope: {self.name_map}")
        outer_scope = self.name_map
        if local_vars is not None:
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
        raise StaFunctionReturn(value)

    def eval_assignment(self, target, value):
        target = self.eval_node(target)
        value = self.eval_node(value)
        target.value = value

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
        return StaObject(left.typ, left.value + right.value)

    def eval_sub(self, left, right):
        if left.typ == sta_string_type:
            raise StaTypeError(f"Subtraction not supported on type {left.typ}")
        return StaObject(left.typ, left.value - right.value)

    def eval_mul(self, left, right):
        if left.typ in (sta_string_type, sta_bool_type):
            raise StaTypeError(
                f"Multiplication not supported on type {left.typ}"
            )
        return StaObject(left.typ, left.value * right.value)

    def eval_div(self, left, right):
        if left.typ in (sta_string_type, sta_bool_type):
            raise StaTypeError(
                f"Division not supported on type {left.typ}"
            )
        return StaObject(left.typ, left.value / right.value)

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
        return StaObject(sta_bool_type, not right.value)

    def eval_neg(self, right):
        if not right.typ in (sta_integer_type, sta_float_type):
            raise StaTypeError(
                f"Negation not supported on type {right.typ}"
            )
        return StaObject(right.typ, -right.value)

    def eval_selector(self, target, name):
        target = self.eval_node(target)
        # access name in target
        assert False, "Selectors not implemented"

    def eval_index(self, target, index):
        target = self.eval_node(target)
        index = self.eval_node(index)
        if index.typ != sta_integer_type:
            raise StaTypeError(
                f"Array indices must be integers, not {index.typ}"
            )
        if not isinstance(target, StaArray):
            raise StaTypeError(f"Cannot index into {target.typ} object")
        if index.value < 0 or index.value >= target.typ.length:
            raise StaValueError("Index out of bounds")
        return target.value[index.value]

    def eval_call(self, callee, args):
        logging.debug("evaluating call")
        func = self.eval_node(callee)
        if not isinstance(func, StaFunction):
            raise StaTypeError(f"{callee} is not a function")
        if len(func.params) != len(args):
            raise StaTypeError(
                f"{callee} takes {len(func.params)} " \
                f"argument{'s' if len(func.params) != 1 else ''} " \
                f"but {len(args)} provided"
            )
        local_vars = {}
        for arg, param in zip(args, func.params):
            logging.debug(f"{param.typ}")
            value = self.eval_node(arg)
            if value.typ != param.typ and not isinstance(value.typ, param.typ):
                raise StaTypeError(
                    f"Expected type {param.typ} " \
                    f"for parameter '{param.name}' " \
                    f"but got {value.typ}"
                )
            local_vars[param.name] = value
        logging.debug(f"{func.block}")
        if isinstance(func, StaBuiltinFunction):
            logging.debug(f"calling builtin {callee}")
            return func.block(**local_vars)
        try:
            self.eval_node(func.block, local_vars=local_vars)
        except StaFunctionReturn as res:
            return res.value

    def eval_primary(self, value):
        match value.typ:
            case T.INTEGER:
                return StaObject(sta_integer_type, int(value.lexeme))
            case T.FLOAT:
                return StaObject(sta_float_type, float(value.lexeme))
            case T.RATIONAL:
                return StaObject(
                    sta_rational_type,
                    Fraction(value.lexeme.replace('//', '/'))
                )
            case T.STRING:
                return StaObject(sta_string_type, str(value.lexeme))
            case T.BOOL:
                return StaObject(sta_bool_type, bool(value.lexeme))
            case T.IDENTIFIER:
                if value.lexeme not in self.name_map:
                    raise StaNameError(f"Name {value.lexeme} not defined")
                return self.name_map[value.lexeme]

    def eval_group_expr(self, expr):
        return self.eval_node(expr)

    def eval_range_expr(self, start, end):
        start = self.eval_node(start)
        end = self.eval_node(end)
        if start.typ != sta_integer_type or end.typ != sta_integer_type:
            raise StaTypeError(f"Range bounds must be integers")
        length = end.value - start.value
        return StaArray(
            StaArrayType(sta_integer_type, length),
            [
                StaObject(sta_integer_type, i)
                for i in range(start.value, end.value)
            ],
            length
        )

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
        print(repr_ast(ast))
        interpreter.eval_node(ast)
        # define entry point
        if "main" in interpreter.name_map:
            try:
                interpreter.eval_node(interpreter.name_map["main"].block)
            except StaFunctionReturn as res:
                print(f"program returned with value {res.value}")
    repl(interpreter)


if __name__ == "__main__":
    import sys
    from parser import repr_ast

    logging.basicConfig(format="%(levelname)s: %(message)s")
    logging.getLogger().setLevel(logging.DEBUG)

    if len(sys.argv) == 2:
        src_file = sys.argv[1]
        main(src_file)
    else:
        main()
