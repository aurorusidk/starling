import unittest
from fractions import Fraction

from src.python.lexer import tokenise, Token, TokenType as T
from src.python.parser import parse
from src.python.type_checker import TypeChecker
from src.python.interpreter import (
    Interpreter,
    StaObject, StaVariable, StaArray,
    StaStruct, StaParameter, StaFunction, StaFunctionReturn,
)
from src.python import ast_nodes as ast
from src.python import builtin
from src.python import type_defs as types


class TestInterpreter(unittest.TestCase):
    def test_expr_eval(self):
        tc_names = {
            "test_struct": types.StructType(
                "test_struct",
                {
                    "x": builtin.types["int"],
                    "y": builtin.types["str"],
                },
            ),
            "test_func": types.FunctionType(
                builtin.types["float"],
                [
                    builtin.types["int"],
                ],
            ),
        }
        names = {
            "test_struct": StaStruct(
                tc_names["test_struct"],
                "test_struct",
                {
                    "x": StaVariable(
                        "x", StaObject(builtin.types["int"], 5)
                    ),
                    "y": StaVariable(
                        "y", StaObject(builtin.types["str"], "test")
                    ),
                },
            ),
            # this is pretty awful since we have to manually specify the ast
            # and add the type information
            "test_func": StaFunction(
                tc_names["test_func"],
                "test_func",
                [
                    StaParameter(builtin.types["int"], ast.Identifier("x")),
                ],
                ast.Block([
                    ast.ReturnStmt(
                        ast.BinaryExpr(
                            Token(T.SLASH, "/"),
                            ast.Identifier("x", typ=builtin.types["int"]),
                            ast.Literal(
                                Token(T.INTEGER, "2"),
                                typ=builtin.types["int"]
                            ),
                            typ=builtin.types["float"],
                        ),
                    ),
                ]),
            ),
        }

        tests = {
            "true": StaObject(builtin.types["bool"], True),
            "false": StaObject(builtin.types["bool"], False),
            "2": StaObject(builtin.types["int"], 2),
            "3//2": StaObject(builtin.types["frac"], Fraction(3, 2)),
            "1.5": StaObject(builtin.types["float"], 1.5),
            "\"a\"": StaObject(builtin.types["str"], "a"),
            "!true": StaObject(builtin.types["bool"], False),
            "-1": StaObject(builtin.types["int"], -1),
            "-1//2": StaObject(builtin.types["frac"], Fraction(-1, 2)),
            "1 + 1": StaObject(builtin.types["int"], 2),
            "2 - 1": StaObject(builtin.types["int"], 1),
            "3 * 2": StaObject(builtin.types["int"], 6),
            "3 / 2": StaObject(builtin.types["float"], 1.5),
            # TODO: add more binary expr checks here for different data types
            "[1:4]": StaArray(
                types.ArrayType(builtin.types["int"], 3),
                [
                    StaObject(builtin.types["int"], 1),
                    StaObject(builtin.types["int"], 2),
                    StaObject(builtin.types["int"], 3),
                ],
                3
            ),
            "[1:10][5]": StaObject(builtin.types["int"], 6),
            "test_struct.x": StaObject(builtin.types["int"], 5),
            "test_struct.y": StaObject(builtin.types["str"], "test"),
            "test_func(5)": StaObject(builtin.types["float"], 2.5),
        }

        for test, expected in tests.items():
            test = "fn test() {return " + test + ";}"
            tokens = tokenise(test)
            tree = parse(tokens)
            tc = TypeChecker(tree)
            tc.scope.name_map |= tc_names
            tc.check(tree)
            interpreter = Interpreter()
            interpreter.scope.name_map |= names
            interpreter.eval_node(tree)
            try:
                f = interpreter.scope.lookup("test")
                interpreter.eval_node(f.block)
            except StaFunctionReturn as result:
                self.assertEqual(result.value, expected)
            else:
                assert False

    def test_stmt_eval(self):
        tc_names = {
            "x": builtin.types["int"],
        }
        names = {
            "x": StaVariable("x", StaObject(builtin.types["int"], 1)),
        }

        tests = {
            "if true {return 1;} else {return 0;}": StaObject(
                builtin.types["int"], 1
            ),
            "if false {return 1;} else {return 0;}": StaObject(
                builtin.types["int"], 0
            ),
            "while x < 10 {x = x * 2} return x;": StaObject(
                builtin.types["int"], 16
            ),
            "x = 10; return x;": StaObject(
                builtin.types["int"], 10
            ),
        }

        for test, expected in tests.items():
            test = "fn test() {" + test + "}"
            tokens = tokenise(test)
            tree = parse(tokens)
            tc = TypeChecker(tree)
            tc.scope.name_map |= tc_names
            tc.check(tree)
            interpreter = Interpreter()
            interpreter.scope.name_map |= names
            interpreter.eval_node(tree)
            try:
                f = interpreter.scope.lookup("test")
                interpreter.eval_node(f.block)
            except StaFunctionReturn as result:
                self.assertEqual(result.value, expected)
            else:
                assert False

    def test_declr_eval(self):
        tests = {
            "fn test() int {}": StaFunction(
                types.FunctionType(builtin.types["int"], []),
                "test",
                [],
                ast.Block([]),
            ),
            "struct test {x int, y str}": types.StructType(
                "test",
                {
                    "x": builtin.types["int"],
                    "y": builtin.types["str"],
                },
            ),
            "var test float = 3.14": StaVariable(
                "test",
                StaObject(builtin.types["float"], 3.14),
            ),
        }

        for test, expected in tests.items():
            tokens = tokenise(test)
            tree = parse(tokens)
            tc = TypeChecker(tree)
            tc.check(tree)
            interpreter = Interpreter()
            interpreter.eval_node(tree)
            self.assertEqual(interpreter.scope.lookup("test"), expected)
