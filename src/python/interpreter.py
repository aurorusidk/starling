from dataclasses import dataclass
from fractions import Fraction
import logging

from .lexer import TokenType as T, tokenise
from .parser import Parser, parse
from .type_checker import Scope, TypeChecker
from . import ast_nodes as ast
from . import type_defs as types
from . import builtin


@dataclass
class StaObject:
    typ: types.Type
    value: object


@dataclass
class StaArray(StaObject):
    typ: types.ArrayType
    value: list[StaObject]
    length: int


@dataclass
class StaVariable:
    name: str
    value: StaObject


@dataclass
class StaParameter:
    typ: types.Type
    name: str


@dataclass
class StaFunction:
    typ: types.FunctionType
    name: str
    params: list[StaParameter]
    block: ast.Block


@dataclass
class StaMethod(StaFunction):
    target: StaObject


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


StaPrintFunc = StaBuiltinFunction(
    builtin.names["print"],
    "print",
    [StaParameter(builtin.types["str"], ast.Identifier("string"))],
    sta_print,
)

StaBuiltins = {
    "print": StaPrintFunc,
}


class Interpreter:
    def __init__(self):
        self.scope = Scope(None)
        self.scope.name_map = StaBuiltins

    def eval_node(self, node, **kwargs):
        match node:
            case ast.Literal(tok):
                return self.eval_literal(tok, node.typ)
            case ast.Identifier(name):
                return self.eval_identifier(name)
            case ast.RangeExpr(start, end):
                return self.eval_range_expr(start, end)
            case ast.GroupExpr(expr):
                return self.eval_group_expr(expr)
            case ast.CallExpr(target, args):
                return self.eval_call_expr(target, args)
            case ast.IndexExpr(target, index):
                return self.eval_index_expr(target, index)
            case ast.SelectorExpr(target, name):
                return self.eval_selector_expr(target, name)
            case ast.UnaryExpr(op, rhs):
                return self.eval_unary_expr(op, rhs)
            case ast.BinaryExpr(op, lhs, rhs):
                return self.eval_binary_expr(op, lhs, rhs)

            case ast.TypeName(name):
                return self.eval_type(name)
            case ast.ArrayType(length, elem_type):
                return self.eval_array_type(length, elem_type)

            case ast.Block(stmts):
                return self.eval_block(stmts)
            case ast.DeclrStmt(declr):
                return self.eval_node(declr)
            case ast.ExprStmt(expr):
                return self.eval_node(expr)
            case ast.IfStmt(condition, if_block, else_block):
                return self.eval_if_stmt(condition, if_block, else_block)
            case ast.WhileStmt(condition, block):
                return self.eval_while_stmt(condition, block)
            case ast.ReturnStmt(value):
                return self.eval_return_stmt(value)
            case ast.AssignmentStmt(target, value):
                return self.eval_assignment_stmt(target, value)

            case ast.FunctionDeclr(signature, block):
                return self.eval_function_declr(
                    signature, node.checked_type, block
                )
            case ast.StructDeclr(name, fields):
                return self.eval_struct_declr(name, node.checked_type, fields)
            case ast.InterfaceDeclr(name, methods):
                return self.eval_interface_declr(
                    name, node.checked_type, methods
                )
            case ast.ImplDeclr(target, interface, methods):
                return self.eval_impl_declr(
                    target, interface, node.checked_type, methods
                )
            case ast.VariableDeclr(name, _, value):
                return self.eval_variable_declr(name, node.checked_type, value)

            case ast.Program(declrs):
                return self.eval_program(declrs)

            case _:
                assert False, f"Unreachable: {node}"

    def eval_program(self, declrs):
        logging.debug(f"{declrs}")
        for declr in declrs:
            self.eval_node(declr)

    def eval_function_inst(self, signature, ftype, block, is_method=False):
        logging.debug(f"{signature}")

        if is_method:
            return StaMethod(
                ftype, signature.name.value, signature.params, block,
                target=None # target will be set later
            )
        else:
            return StaFunction(
                ftype, signature.name.value, signature.params, block
            )

    def eval_function_declr(self, signature, ftype, block):
        # Verify that the signature's param types are correct based on the FunctionType
        for param, typ in zip(signature.params, ftype.param_types):
            param.typ = typ

        func = self.eval_function_inst(signature, ftype, block)
        self.scope.declare(signature.name, func)

    def eval_struct_declr(self, name, typ, members):
        logging.debug(f"{name}, {members}")
        self.scope.declare(name, typ)

    def eval_interface_declr(self, name, typ, methods):
        logging.debug(f"{name}, {methods}")
        self.scope.declare(name, typ)

    def eval_impl_declr(self, target, interface, typ, methods):
        logging.debug(f"{target}<{interface}>, {methods}")

        target_type = self.scope.lookup(target.value.value)
        assert isinstance(target_type, types.Type), \
            f"No type with name {target.value} in scope"

        if interface is not None:
            interface = self.scope.lookup(interface.value)

            for signature in interface:
                assert signature in [method.signature for method in methods], \
                    f"No definition for method {signature} on type {target}"

        for method in methods:
            if interface is not None:
                assert method.signature in interface, \
                    f"No method {method.signature} on interface {interface}"

            # create a FunctionType based on the method signature
            ftype = types.FunctionType(
                        method.signature.return_type,
                        [param.typ for param in method.signature.params]
                    )
            method_obj = self.eval_function_inst(
                method.signature, ftype, method.block, is_method=True
            )
            target_type.methods[method.signature.name.value] = method_obj

    def eval_variable_declr(self, name, typ, value):
        if value is not None:
            value = self.eval_node(value)
        var = StaVariable(name.value, value)
        self.scope.declare(name, var)

    def eval_type(self, name):
        typ = builtin.types.get(name.value)
        assert typ is not None, f"Unimplemented type: {name.value}"
        return typ

    def eval_array_type(self, length, elem_type):
        length = self.eval_node(length)
        typ = self.eval_node(elem_type)
        return types.ArrayType(typ, length.value)

    def eval_block(self, stmts):
        for stmt in stmts:
            self.eval_node(stmt)

    def eval_if_stmt(self, condition, if_block, else_block):
        if self.eval_node(condition).value:
            self.eval_node(if_block)
        elif else_block is not None:
            self.eval_node(else_block)

    def eval_while_stmt(self, condition, while_block):
        while self.eval_node(condition).value:
            self.eval_node(while_block)

    def eval_return_stmt(self, value):
        value = self.eval_node(value)
        raise StaFunctionReturn(value)

    def eval_assignment_stmt(self, target, value):
        target = self.eval_node(target)
        value = self.eval_node(value)
        target.value = value.value

    def eval_binary_expr(self, op, left, right):
        left = self.eval_node(left)
        right = self.eval_node(right)
        assert left.typ == right.typ, "Type coercion not implemented"
        match op.typ:
            case T.PLUS:
                return self.eval_add(left, right)
            case T.MINUS:
                return self.eval_sub(left, right)
            case T.STAR:
                return self.eval_mul(left, right)
            case T.SLASH:
                return self.eval_div(left, right)
            case T.EQUALS_EQUALS:
                return self.eval_equal(left, right)
            case T.BANG_EQUALS:
                return self.eval_not_equal(left, right)
            case T.LESS_THAN:
                return self.eval_less_than(left, right)
            case T.GREATER_THAN:
                return self.eval_greater_than(left, right)
            case T.LESS_EQUALS:
                return self.eval_less_than_equal(left, right)
            case T.GREATER_EQUALS:
                return self.eval_greater_than_equal(left, right)
            case _:
                assert False, f"Unimplemented operator: {op.typ}"

    def eval_add(self, left, right):
        return StaObject(left.typ, left.value + right.value)

    def eval_sub(self, left, right):
        return StaObject(left.typ, left.value - right.value)

    def eval_mul(self, left, right):
        return StaObject(left.typ, left.value * right.value)

    def eval_div(self, left, right):
        return StaObject(builtin.types["float"], left.value / right.value)

    def eval_equal(self, left, right):
        return StaObject(builtin.types["bool"], left.value == right.value)

    def eval_not_equal(self, left, right):
        return StaObject(builtin.types["bool"], left.value != right.value)

    def eval_less_than(self, left, right):
        return StaObject(builtin.types["bool"], left.value < right.value)

    def eval_greater_than(self, left, right):
        return StaObject(builtin.types["bool"], left.value > right.value)

    def eval_less_than_equal(self, left, right):
        return StaObject(builtin.types["bool"], left.value <= right.value)

    def eval_greater_than_equal(self, left, right):
        return StaObject(builtin.types["bool"], left.value >= right.value)

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
        return StaObject(right.typ, not right.value)

    def eval_neg(self, right):
        return StaObject(right.typ, -right.value)

    def eval_selector_expr(self, target, name):
        logging.debug(f"{target}.{name}")
        target = self.eval_node(target)
        if name.value in target.fields.keys():
            return target.fields[name.value].value
        if name.value in target.typ.methods.keys():
            method = target.typ.methods[name.value]
            method.target = target
            return method
        assert False, f"No valid selector {name} for {target}"

    def eval_index_expr(self, target, index):
        target = self.eval_node(target)
        index = self.eval_node(index)
        if index.value < 0 or index.value >= target.typ.length:
            raise StaValueError("Index out of bounds")
        return target.value[index.value]

    def eval_call_expr(self, callee, args):
        logging.debug("evaluating call")
        target = self.eval_node(callee)
        if isinstance(target, StaFunction):
            self.scope = Scope(self.scope)
            if isinstance(target, StaMethod):
                self.scope.declare(ast.Identifier("self"), target.target)
            for arg, param in zip(args, target.params):
                logging.debug(f"{param.typ}")
                value = self.eval_node(arg)
                self.scope.declare(param.name, value)
            logging.debug(f"{target.block}")
            if isinstance(target, StaBuiltinFunction):
                logging.debug(f"calling builtin {callee}")
                value = target.block(**self.scope.name_map)
                return value
            try:
                self.eval_node(target.block)
            except StaFunctionReturn as res:
                return res.value
        elif isinstance(target, types.StructType):
            fields = {}
            for i, arg in enumerate(args):
                value = self.eval_node(arg)
                name = list(target.fields.keys())[i]
                field = StaVariable(name, value)
                fields[name] = field
            return StaStruct(target, target.name, fields)

    def eval_literal(self, value, typ):
        if typ == builtin.types["int"]:
            value = int(value.lexeme)
        elif typ == builtin.types["float"]:
            value = float(value.lexeme)
        elif typ == builtin.types["frac"]:
            value = Fraction(value.lexeme.replace('//', '/'))
        elif typ == builtin.types["str"]:
            value = str(value.lexeme[1:-1])
        elif typ == builtin.types["bool"]:
            value = value.lexeme == "true"
        else:
            assert False, f"Unreachable: {typ}"
        return StaObject(typ, value)

    def eval_identifier(self, name):
        obj = self.scope.lookup(name)
        if isinstance(obj, StaVariable):
            return obj.value
        return obj

    def eval_group_expr(self, expr):
        return self.eval_node(expr)

    def eval_range_expr(self, start, end):
        start = self.eval_node(start)
        end = self.eval_node(end)
        length = end.value - start.value
        return StaArray(
            types.ArrayType(builtin.types["int"], length),
            [
                StaObject(builtin.types["int"], i)
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
