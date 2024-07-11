import unittest
from src.python.lexer import tokenise
from src.python.parser import Parser
from src.python.type_checker import TypeChecker
from src.python import builtin
from src.python import type_defs as types


class TestTypeChecker(unittest.TestCase):
    def test_valid_expr_check(self):
        names = {
            "x": builtin.types["int"],
            "test": types.FunctionType(
                builtin.types["frac"],
                [
                    builtin.types["float"],
                ]
            ),
        }

        tests = {
            "1 + 1": builtin.types["int"],
            "1 + 1//2": builtin.types["frac"],
            "1 + 1.5": builtin.types["float"],
            "\"a\" + \"b\"": builtin.types["str"],
            "3 / 2": builtin.types["float"], # TODO: in tc should this be rational?
            "x + 1": builtin.types["int"],
            "x * 0.5": builtin.types["float"],
            "!true": builtin.types["bool"],
            "[1:10][0]": builtin.types["int"],
            "[0:x + 1][x]": builtin.types["int"],
            "test(1.5)": builtin.types["frac"],
            "test(x + 0.5)": builtin.types["frac"],
        }

        for test, expected in tests.items():
            tokens = tokenise(test)
            ast = Parser(tokens).parse_expression()
            tc = TypeChecker(ast)
            tc.scope.name_map |= names
            tc.check(tc.root)
            self.assertEqual(tc.root.typ, expected)


    def test_invalid_expr_check(self):
        names = {
            "x": builtin.types["int"],
            "test": types.FunctionType(
                builtin.types["frac"],
                [
                    builtin.types["float"],
                ]
            ),
        }

        tests = [
            "1 + \"a\"",
            "\"a\" * \"b\"",
            "true / false",
            "x - \"a\"",
            "test(x)",
            "test(1.5)[x]",
            "[1:10][1.5]",
            "[0:4.5]",
            "!1.5",
            "-\"a\"",
        ]

        for test in tests:
            tokens = tokenise(test)
            ast = Parser(tokens).parse_expression()
            tc = TypeChecker(ast)
            tc.scope.name_map |= names
            self.assertRaises(AssertionError, tc.check, tc.root)

    def test_valid_inference(self):
        pass

    def test_invalid_inference(self):
        pass
