import unittest
from src.python.lexer import Token, TokenType as T
from src.python import lexer
from src.python.cmd import translate


start_pos = lexer.Pos(1, 1)


class TestLexer(unittest.TestCase):
    def test_valid_kw(self):
        tests = {
            "true": [Token(T.BOOLEAN, "true", start_pos)],
            "false": [Token(T.BOOLEAN, "false", start_pos)],
            "if": [Token(T.IF, "if", start_pos)],
            "else": [Token(T.ELSE, "else", start_pos)],
            "while": [Token(T.WHILE, "while", start_pos)],
            "return": [Token(T.RETURN, "return", start_pos)],
            "var": [Token(T.VAR, "var", start_pos)],
            "const": [Token(T.CONST, "const", start_pos)],
            "fn": [Token(T.FUNC, "fn", start_pos)],
            "struct": [Token(T.STRUCT, "struct", start_pos)],
            "interface": [Token(T.INTERFACE, "interface", start_pos)],
            "impl": [Token(T.IMPL, "impl", start_pos)],
            "arr": [Token(T.ARR, "arr", start_pos)],
            "vec": [Token(T.VEC, "vec", start_pos)],
        }

        for test, expected in tests.items():
            with self.subTest(test=test):
                self.assertEqual(translate(test, tokenise=True), expected)

        for keyword in lexer.KEYWORDS:
            with self.subTest(test=keyword):
                self.assertIn(keyword, tests)

    def test_uppercase_kw(self):
        tests = {
            "True": [Token(T.IDENTIFIER, "True", start_pos)],
            "False": [Token(T.IDENTIFIER, "False", start_pos)],
            "IF": [Token(T.IDENTIFIER, "IF", start_pos)],
            "fN": [Token(T.IDENTIFIER, "fN", start_pos)],
            "strUct": [Token(T.IDENTIFIER, "strUct", start_pos)],
        }

        for test, expected in tests.items():
            with self.subTest(test=test):
                self.assertEqual(translate(test, tokenise=True), expected)

    def test_identifier_kw(self):
        tests = {
            "structure": [Token(T.IDENTIFIER, "structure", start_pos)],
            "string": [Token(T.IDENTIFIER, "string", start_pos)],
            "func": [Token(T.IDENTIFIER, "func", start_pos)],
            "variable": [Token(T.IDENTIFIER, "variable", start_pos)],
            "implement": [Token(T.IDENTIFIER, "implement", start_pos)]
        }

        for test, expected in tests.items():
            with self.subTest(test=test):
                self.assertEqual(translate(test, tokenise=True), expected)

    def test_valid_mg(self):
        tests = {
            "<": [Token(T.LESS_THAN, "<", start_pos)],
            ">": [Token(T.GREATER_THAN, ">", start_pos)],
            "=": [Token(T.EQUALS, "=", start_pos)],
            "*": [Token(T.STAR, "*", start_pos)],
            "/": [Token(T.SLASH, "/", start_pos)],
            "+": [Token(T.PLUS, "+", start_pos)],
            "-": [Token(T.MINUS, "-", start_pos)],
            "!": [Token(T.BANG, "!", start_pos)],
            ";": [Token(T.SEMICOLON, ";", start_pos)],
            ":": [Token(T.COLON, ":", start_pos)],
            ",": [Token(T.COMMA, ",", start_pos)],
            ".": [Token(T.DOT, ".", start_pos)],
            "(": [Token(T.LEFT_BRACKET, "(", start_pos)],
            ")": [Token(T.RIGHT_BRACKET, ")", start_pos)],
            "{": [Token(T.LEFT_CURLY, "{", start_pos)],
            "}": [Token(T.RIGHT_CURLY, "}", start_pos)],
            "[": [Token(T.LEFT_SQUARE, "[", start_pos)],
            "]": [Token(T.RIGHT_SQUARE, "]", start_pos)],
        }

        for test, expected in tests.items():
            with self.subTest(test=test):
                self.assertEqual(translate(test, tokenise=True), expected)

        for monograph in lexer.MONOGRAPHS:
            with self.subTest(test=monograph):
                self.assertIn(monograph, tests)

    def test_invalid_mg(self):
        tests = [
            "@",
            "$",
            "£",
            "¬",
        ]

        for test in tests:
            with self.subTest(test=test):
                self.assertRaises(AssertionError, lexer.tokenise, test)

    def test_valid_dg(self):
        tests = {
            "==": [Token(T.EQUALS_EQUALS, "==", start_pos)],
            "!=": [Token(T.BANG_EQUALS, "!=", start_pos)],
            "<=": [Token(T.LESS_EQUALS, "<=", start_pos)],
            ">=": [Token(T.GREATER_EQUALS, ">=", start_pos)],
            "::": [Token(T.DOUBLE_COLON, "::", start_pos)],
        }

        for test, expected in tests.items():
            with self.subTest(test=test):
                self.assertEqual(translate(test, tokenise=True), expected)

        for digraph in lexer.DIGRAPHS:
            with self.subTest(test=digraph):
                self.assertIn(digraph, tests)

    def test_invalid_dg(self):
        second_pos = lexer.Pos(1, 2)
        tests = {
            "<>": [
                Token(T.LESS_THAN, "<", start_pos),
                Token(T.GREATER_THAN, ">", second_pos)
            ],
            "++": [
                Token(T.PLUS, "+", start_pos),
                Token(T.PLUS, "+", second_pos)
            ],
            "*=": [
                Token(T.STAR, "*", start_pos),
                Token(T.EQUALS, "=", second_pos)
            ],
        }

        for test, expected in tests.items():
            with self.subTest(test=test):
                self.assertEqual(translate(test, tokenise=True), expected)

    def test_no_space_g(self):
        tests = {
            "1+2": [
                Token(T.INTEGER, "1", start_pos),
                Token(T.PLUS, "+", lexer.Pos(1, 2)),
                Token(T.INTEGER, "2", lexer.Pos(1, 3))
            ],
            "x=9": [
                Token(T.IDENTIFIER, "x", start_pos),
                Token(T.EQUALS, "=", lexer.Pos(1, 2)),
                Token(T.INTEGER, "9", lexer.Pos(1, 3))
            ],
            "test==true": [
                Token(T.IDENTIFIER, "test", start_pos),
                Token(T.EQUALS_EQUALS, "==", lexer.Pos(1, 5)),
                Token(T.BOOLEAN, "true", lexer.Pos(1, 7))
            ],
        }

        for test, expected in tests.items():
            with self.subTest(test=test):
                self.assertEqual(translate(test, tokenise=True), expected)

    def test_ignore_whitespace(self):
        tests = {
            "1       +  2      ": [
                Token(T.INTEGER, "1", lexer.Pos(1, 1)),
                Token(T.PLUS, "+", lexer.Pos(1, 9)),
                Token(T.INTEGER, "2", lexer.Pos(1, 12))
            ],
            "    x   =9    ": [
                Token(T.IDENTIFIER, "x", lexer.Pos(1, 5)),
                Token(T.EQUALS, "=", lexer.Pos(1, 9)),
                Token(T.INTEGER, "9", lexer.Pos(1, 10))
            ],
            "   test     ==     true    ": [
                Token(T.IDENTIFIER, "test", lexer.Pos(1, 4)),
                Token(T.EQUALS_EQUALS, "==", lexer.Pos(1, 13)),
                Token(T.BOOLEAN, "true", lexer.Pos(1, 20))
            ],
            "\t \t \t \t \t \t \t \t \t \t \t \t": [],
            "\t       \t x\t \t =\t     \n        \t 25.7\t      \t": [
                Token(T.IDENTIFIER, "x", lexer.Pos(1, 11)),
                Token(T.EQUALS, "=", lexer.Pos(1, 16)),
                Token(T.FLOAT, "25.7", lexer.Pos(2, 11))
            ],
        }

        for test, expected in tests.items():
            with self.subTest(test=test):
                self.assertEqual(translate(test, tokenise=True), expected)


if __name__ == "__main__":
    unittest.main()
