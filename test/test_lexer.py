import unittest
from src.python.lexer import *


class TestLexer(unittest.TestCase):
    def test_valid_kw(self):
        tests = {
            "true": [Token(BOOLEAN, "true")],
            "false": [Token(BOOLEAN, "false")],
            "if": [Token(IF, "if")],
            "else": [Token(ELSE, "else")],
            "while": [Token(WHILE, "while")],
            "return": [Token(RETURN, "return")],
            "var": [Token(VAR, "var")],
            "fn": [Token(FUNC, "fn")],
            "struct": [Token(STRUCT, "struct")],
        }

        for test, expected in tests.items():
            self.assertEqual(tokenise(test), expected)

        for keyword in KEYWORDS:
            self.assertIn(keyword, tests)

    def test_uppercase_kw(self):
        tests = {
            "True": [Token(IDENTIFIER, "True")],
            "False": [Token(IDENTIFIER, "False")],
            "IF": [Token(IDENTIFIER, "IF")],
            "fN": [Token(IDENTIFIER, "fN")],
            "strUct": [Token(IDENTIFIER, "strUct")],
        }

        for test, expected in tests.items():
            self.assertEqual(tokenise(test), expected)

    def test_identifier_kw(self):
        tests = {
            "structure": [Token(IDENTIFIER, "structure")],
            "string": [Token(IDENTIFIER, "string")],
            "func": [Token(IDENTIFIER, "func")],
            "variable": [Token(IDENTIFIER, "variable")],
        }

        for test, expected in tests.items():
            self.assertEqual(tokenise(test), expected)

    def test_valid_mg(self):
        tests = {
            "<": [Token(LESS_THAN, "<")],
            ">": [Token(GREATER_THAN, ">")],
            "=": [Token(EQUALS, "=")],
            "*": [Token(STAR, "*")],
            "/": [Token(SLASH, "/")],
            "+": [Token(PLUS, "+")],
            "-": [Token(MINUS, "-")],
            "!": [Token(BANG, "!")],
            ";": [Token(SEMICOLON, ";")],
            ":": [Token(COLON, ":")],
            ",": [Token(COMMA, ",")],
            ".": [Token(DOT, ".")],
            "(": [Token(LEFT_BRACKET, "(")],
            ")": [Token(RIGHT_BRACKET, ")")],
            "{": [Token(LEFT_CURLY, "{")],
            "}": [Token(RIGHT_CURLY, "}")],
            "[": [Token(LEFT_SQUARE, "[")],
            "]": [Token(RIGHT_SQUARE, "]")],
        }

        for test, expected in tests.items():
            self.assertEqual(tokenise(test), expected)

        for monograph in MONOGRAPHS:
            self.assertIn(monograph, tests)

    def test_invalid_mg(self):
        tests = [
            "@",
            "$",
            "£",
            "¬",
        ]

        for test in tests:
            self.assertRaises(AssertionError, tokenise, test)

    def test_valid_dg(self):
        tests = {
            "==": [Token(EQUALS_EQUALS, "==")],
            "!=": [Token(BANG_EQUALS, "!=")],
            "<=": [Token(LESS_EQUALS, "<=")],
            ">=": [Token(GREATER_EQUALS, ">=")],
        }
        
        for test, expected in tests.items():
            self.assertEqual(tokenise(test), expected)

        for digraph in DIGRAPHS:
            self.assertIn(digraph, tests)

    def test_invalid_dg(self):
        tests = {
            "<>": [Token(LESS_THAN, "<"), Token(GREATER_THAN, ">")],
            "::": [Token(COLON, ":"), Token(COLON, ":")],
            "++": [Token(PLUS, "+"), Token(PLUS, "+")],
            "*=": [Token(STAR, "*"), Token(EQUALS, "=")],
        }

        for test, expected in tests.items():
            self.assertEqual(tokenise(test), expected)

    def test_no_space_g(self):
        tests = {
            "1+2": [Token(INTEGER, "1"), Token(PLUS, "+"), Token(INTEGER, "2")],
            "x=9": [Token(IDENTIFIER, "x"), Token(EQUALS, "="), Token(INTEGER, "9")],
            "test==true": [Token(IDENTIFIER, "test"), Token(EQUALS_EQUALS, "=="), Token(BOOLEAN, "true")],
        }

        for test, expected in tests.items():
            self.assertEqual(tokenise(test), expected)

    def test_ignore_whitespace(self):
        tests = {
            "1       +  2      ": [Token(INTEGER, "1"), Token(PLUS, "+"), Token(INTEGER, "2")],
            "    x   =9    ": [Token(IDENTIFIER, "x"), Token(EQUALS, "="), Token(INTEGER, "9")],
            "   test     ==     true    ": [Token(IDENTIFIER, "test"), Token(EQUALS_EQUALS, "=="), Token(BOOLEAN, "true")],
            "\t \t \t \t \t \t \t \t \t \t \t \t": [],
            "\t       \t x\t \t =\t     \n        \t 25.7\t      \t": [Token(IDENTIFIER, "x"), Token(EQUALS, "="), Token(FLOAT, "25.7")],
        }

        for test, expected in tests.items():
            self.assertEqual(tokenise(test), expected)

if __name__ == "__main__":
    unittest.main()
