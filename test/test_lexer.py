import unittest
from src.python.lexer import tokenise, Token, TokenType as T
#run with: python -m unittest .\test\test_lexer.py

class TestLexer(unittest.TestCase):
    #keyword testing
    def test_valid_kw(self):
        pass

    def test_uppercase_kw(self):
        pass

    def test_identifier_kw(self):
        pass

    #graph testing
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
            "]": [Token(T.RIGHT_SQUARE, "]")]
        }
        for test, expected in tests.items():
            self.assertEqual(tokenise(test), expected)

    def test_invalid_mg(self):
        pass

    def test_valid_dg(self):
        tests = {
            "==": [Token(T.EQUALS_EQUALS, "==")],
            "!=": [Token(T.BANG_EQUALS, "!=")],
            "<=": [Token(T.LESS_EQUALS, "<=")],
            ">=": [Token(T.GREATER_EQUALS, ">=")]
        }
        for test, expected in tests.items():
            self.assertEqual(tokenise(test), expected)

    def test_invalid_dg(self):
        pass

    def test_no_space_g(self):
        pass

    #misc
    def test_ignore_whitespace(self):
        pass

if __name__ == "__main__":
    unittest.main()