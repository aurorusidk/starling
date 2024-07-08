import unittest
from src.python.lexer import tokenise, Token, TokenType as T
#run with: python -m unittest .\test\test_lexer.py

class TestLexer(unittest.TestCase):
    #keyword testing
    def test_valid_kw(self):
        tests = {
            "true": [Token(T.BOOL, "true")],
            "false": [Token(T.BOOL, "false")],
            "if": [Token(T.IF, "if")],
            "else": [Token(T.ELSE, "else")],
            "while": [Token(T.WHILE, "while")],
            "return": [Token(T.RETURN, "return")],
            "var": [Token(T.VAR, "var")],
            "fn": [Token(T.FUNC, "fn")],
            "struct": [Token(T.STRUCT, "struct")]
        }

        for test, expected in tests.items():
            self.assertEqual(tokenise(test), expected)

    def test_uppercase_kw(self):
        tests ={
            "True": [Token(T.IDENTIFIER, "True")],
            "False": [Token(T.IDENTIFIER, "False")],
            "IF": [Token(T.IDENTIFIER, "IF")],
            "fN": [Token(T.IDENTIFIER, "fN")],
            "strUct": [Token(T.IDENTIFIER, "strUct")]
        }

        for test, expected in tests.items():
            self.assertEqual(tokenise(test), expected)

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
        tests = [
            "@",
            "$",
            "£",
            "¬"
        ]

        for test in tests:
            with self.assertRaises(AssertionError):
                tokenise(test)

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
        # no need to check for invalid chars
        # only checking sequences of valid chars that don't form digraphs
        tests = {
            "<>": [Token(T.LESS_THAN, "<"), Token(T.GREATER_THAN, ">")],
            "::": [Token(T.COLON, ":"), Token(T.COLON, ":")],
            "++": [Token(T.PLUS, "+"), Token(T.PLUS, "+")],
            "*=": [Token(T.STAR, "*"), Token(T.EQUALS, "=")]
        }

        for test, expected in tests.items():
            self.assertEqual(tokenise(test), expected)

    def test_no_space_g(self):
        pass

    #misc
    def test_ignore_whitespace(self):
        pass

if __name__ == "__main__":
    unittest.main()
