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
        pass

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