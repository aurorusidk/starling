import unittest
from src.python.lexer import tokenise
from src.python.parser import Parser
from src.python.type_checker import TypeChecker
from src.python import builtin
from src.python import type_defs as types


class TestTypeChecker(unittest.TestCase):
    def test_valid_check(self):
        tests = {
            "1 + 1": builtin.types["int"],
            "1 + 1//2": builtin.types["frac"],
            "1 + 1.5": builtin.types["float"],
            "\"a\" + \"b\"": builtin.types["str"],
            "3 / 2": builtin.types["float"], # TODO: in tc should this be rational?
            "!true": builtin.types["bool"],
            "[1:10][0]": builtin.types["int"],
            # cannot implement any tests that require names with this method...
        }

        for test, expected in tests.items():
            tokens = tokenise(test)
            ast = Parser(tokens).parse_expression()
            tc = TypeChecker(ast)
            tc.check(tc.root)
            self.assertEqual(tc.root.typ, expected)


    def test_invalid_check(self):
        pass

    def test_valid_inference(self):
        pass

    def test_invalid_inference(self):
        pass
