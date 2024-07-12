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

    def test_valid_stmt_check(self):
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
            "if x == 1 {} else {}",
            "while x > 0 {}",
            "return 1//2;",
            "x = 1;"
        ]

        for test in tests:
            tokens = tokenise(test)
            ast = Parser(tokens).parse_statement()
            tc = TypeChecker(ast)
            tc.scope.name_map |= names
            tc.function = names["test"]
            tc.check(tc.root)


    def test_invalid_stmt_check(self):
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
            "if x {} else {}",
            "if 1 {}",
            "while x {}",
            "return 1.5;",
            "return x;",
            "x = 1//2",
            "x = \"test\"",
        ]

        for test in tests:
            tokens = tokenise(test)
            ast = Parser(tokens).parse_statement()
            tc = TypeChecker(ast)
            tc.scope.name_map |= names
            tc.function = names["test"]
            self.assertRaises(AssertionError, tc.check, tc.root)

    def test_valid_declr_check(self):
        tests = {
            "fn test(x float) frac {}": types.FunctionType(
                builtin.types["frac"],
                [
                    builtin.types["float"],
                ]
            ),
            "struct test {x int, y str}": types.StructType(
                "test",
                {
                    "x": builtin.types["int"],
                    "y": builtin.types["str"],
                }
            ),
            "var test int = 1;": builtin.types["int"],
        }

        for test, expected, in tests.items():
            tokens = tokenise(test)
            ast = Parser(tokens).parse_declaration()
            tc = TypeChecker(ast)
            tc.check(tc.root)
            self.assertEqual(ast.checked_type, expected)

    def test_invalid_declr_check(self):
        tests = [
            # TODO: are there any other possible errors here?
            "var test str = 1.5;"
        ]

        for test in tests:
            tokens = tokenise(test)
            ast = Parser(tokens).parse_declaration()
            tc = TypeChecker(ast)
            self.assertRaises(AssertionError, tc.check, tc.root)

    def test_valid_inference(self):
        pass

    def test_invalid_inference(self):
        pass