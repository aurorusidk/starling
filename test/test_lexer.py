import unittest
from src.python.lexer import Token, TokenType as T
from src.python import lexer


class TestLexer(unittest.TestCase):
    def test_valid_kw(self):
        tests = {
            "true": [Token(T.BOOLEAN, "true")],
            "false": [Token(T.BOOLEAN, "false")],
            "if": [Token(T.IF, "if")],
            "else": [Token(T.ELSE, "else")],
            "while": [Token(T.WHILE, "while")],
            "return": [Token(T.RETURN, "return")],
            "var": [Token(T.VAR, "var")],
            "fn": [Token(T.FUNC, "fn")],
            "struct": [Token(T.STRUCT, "struct")],
        }

        for test, expected in tests.items():
            self.assertEqual(lexer.tokenise(test), expected)

        for keyword in lexer.KEYWORDS:
            self.assertIn(keyword, tests)

    def test_uppercase_kw(self):
        tests = {
            "True": [Token(T.IDENTIFIER, "True")],
            "False": [Token(T.IDENTIFIER, "False")],
            "IF": [Token(T.IDENTIFIER, "IF")],
            "fN": [Token(T.IDENTIFIER, "fN")],
            "strUct": [Token(T.IDENTIFIER, "strUct")],
        }

        for test, expected in tests.items():
            self.assertEqual(lexer.tokenise(test), expected)

    def test_identifier_kw(self):
        tests = {
            "structure": [Token(T.IDENTIFIER, "structure")],
            "string": [Token(T.IDENTIFIER, "string")],
            "func": [Token(T.IDENTIFIER, "func")],
            "variable": [Token(T.IDENTIFIER, "variable")],
        }

        for test, expected in tests.items():
            self.assertEqual(lexer.tokenise(test), expected)

    def test_valid_mg(self):
        tests = {
            "<": [Token(T.LESS_THAN, "<")],
            ">": [Token(T.GREATER_THAN, ">")],
            "=": [Token(T.EQUALS, "=")],
            "*": [Token(T.STAR, "*")],
            "/": [Token(T.SLASH, "/")],
            "+": [Token(T.PLUS, "+")],
            "-": [Token(T.MINUS, "-")],
            "!": [Token(T.BANG, "!")],
            ";": [Token(T.SEMICOLON, ";")],
            ":": [Token(T.COLON, ":")],
            ",": [Token(T.COMMA, ",")],
            ".": [Token(T.DOT, ".")],
            "(": [Token(T.LEFT_BRACKET, "(")],
            ")": [Token(T.RIGHT_BRACKET, ")")],
            "{": [Token(T.LEFT_CURLY, "{")],
            "}": [Token(T.RIGHT_CURLY, "}")],
            "[": [Token(T.LEFT_SQUARE, "[")],
            "]": [Token(T.RIGHT_SQUARE, "]")],
        }

        for test, expected in tests.items():
            self.assertEqual(lexer.tokenise(test), expected)

        for monograph in lexer.MONOGRAPHS:
            self.assertIn(monograph, tests)

    def test_invalid_mg(self):
        tests = [
            "@",
            "$",
            "£",
            "¬",
        ]

        for test in tests:
            self.assertRaises(AssertionError, lexer.tokenise, test)

    def test_valid_dg(self):
        tests = {
            "==": [Token(T.EQUALS_EQUALS, "==")],
            "!=": [Token(T.BANG_EQUALS, "!=")],
            "<=": [Token(T.LESS_EQUALS, "<=")],
            ">=": [Token(T.GREATER_EQUALS, ">=")],
        }

        for test, expected in tests.items():
            self.assertEqual(lexer.tokenise(test), expected)

        for digraph in lexer.DIGRAPHS:
            self.assertIn(digraph, tests)

    def test_invalid_dg(self):
        tests = {
            "<>": [Token(T.LESS_THAN, "<"), Token(T.GREATER_THAN, ">")],
            "::": [Token(T.COLON, ":"), Token(T.COLON, ":")],
            "++": [Token(T.PLUS, "+"), Token(T.PLUS, "+")],
            "*=": [Token(T.STAR, "*"), Token(T.EQUALS, "=")],
        }

        for test, expected in tests.items():
            self.assertEqual(lexer.tokenise(test), expected)

    def test_no_space_g(self):
        tests = {
            "1+2": [
                Token(T.INTEGER, "1"),
                Token(T.PLUS, "+"),
                Token(T.INTEGER, "2")
            ],
            "x=9": [
                Token(T.IDENTIFIER, "x"),
                Token(T.EQUALS, "="),
                Token(T.INTEGER, "9")
            ],
            "test==true": [
                Token(T.IDENTIFIER, "test"),
                Token(T.EQUALS_EQUALS, "=="),
                Token(T.BOOLEAN, "true")
            ],
        }

        for test, expected in tests.items():
            self.assertEqual(lexer.tokenise(test), expected)

    def test_ignore_whitespace(self):
        tests = {
            "1       +  2      ": [
                Token(T.INTEGER, "1"),
                Token(T.PLUS, "+"),
                Token(T.INTEGER, "2")
            ],
            "    x   =9    ": [
                Token(T.IDENTIFIER, "x"),
                Token(T.EQUALS, "="),
                Token(T.INTEGER, "9")
            ],
            "   test     ==     true    ": [
                Token(T.IDENTIFIER, "test"),
                Token(T.EQUALS_EQUALS, "=="),
                Token(T.BOOLEAN, "true")
            ],
            "\t \t \t \t \t \t \t \t \t \t \t \t": [],
            "\t       \t x\t \t =\t     \n        \t 25.7\t      \t": [
                Token(T.IDENTIFIER, "x"),
                Token(T.EQUALS, "="),
                Token(T.FLOAT, "25.7")
            ],
        }

        for test, expected in tests.items():
            self.assertEqual(lexer.tokenise(test), expected)


if __name__ == "__main__":
    unittest.main()
