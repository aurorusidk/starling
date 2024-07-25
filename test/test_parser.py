import unittest
from src.python.lexer import tokenise, Token, TokenType as T
from src.python.parser import Parser
import src.python.ast_nodes as ast


class TestParser(unittest.TestCase):
    def test_valid_declr(self):
        tests = {
            "fn test(x int, y int) int {}": ast.FunctionDeclr(
                ast.FunctionSignature(
                    ast.Identifier("test"),
                    ast.TypeName(ast.Identifier("int")),
                    [
                        ast.FieldDeclr(
                            ast.Identifier("x"),
                            ast.TypeName(ast.Identifier("int")),
                        ),
                        ast.FieldDeclr(
                            ast.Identifier("y"),
                            ast.TypeName(ast.Identifier("int")),
                        ),
                    ],
                ),
                ast.Block([]),
            ),

            "struct test {x int; y int;}": ast.StructDeclr(
                ast.Identifier("test"),
                [
                    ast.FieldDeclr(
                        ast.Identifier("x"),
                        ast.TypeName(ast.Identifier("int")),
                    ),
                    ast.FieldDeclr(
                        ast.Identifier("y"),
                        ast.TypeName(ast.Identifier("int")),
                    ),
                ],
            ),

            "var test int = x;": ast.VariableDeclr(
                ast.Identifier("test"),
                ast.TypeName(ast.Identifier("int")),
                ast.Identifier("x"),
            ),
        }

        p = Parser(None)
        for test, expected in tests.items():
            p.cur = 0
            p.tokens = tokenise(test)
            self.assertEqual(p.parse_declaration(), expected)

    @unittest.expectedFailure
    def test_invalid_declr(self):
        # TODO: implement correct parser errors, so test works correctly
        tests = [
            "func test(x int, y int) int {}",
            "struct test {x int, y int}"
            "struct test (x int; y int;)",
            "var test == x;",
            "var test = x",
        ]

        p = Parser(None)
        for test in tests:
            p.cur = 0
            p.tokens = tokenise(test)
            self.assertRaises(AssertionError, p.parse_declaration)

    def test_valid_stmt(self):
        # skips declr and expr stmts; blocks are implicitly tested throughout
        # TODO: should test more variations
        tests = {
            "if test {} else {}": ast.IfStmt(
                ast.Identifier("test"),
                ast.Block([]),
                ast.Block([]),
            ),

            "while test {}": ast.WhileStmt(
                ast.Identifier("test"),
                ast.Block([]),
            ),

            "return test;": ast.ReturnStmt(
                ast.Identifier("test"),
            ),

            "test = x;": ast.AssignmentStmt(
                ast.Identifier("test"),
                ast.Identifier("x"),
            ),
        }

        p = Parser(None)
        for test, expected in tests.items():
            p.cur = 0
            p.tokens = tokenise(test)
            self.assertEqual(p.parse_statement(), expected)

    @unittest.expectedFailure
    def test_invalid_stmt(self):
        # TODO: add more variations
        tests = [
            "if test () else ()",
            "whiletest {}",
            "return test",
            "test == x;"
        ]

        p = Parser(None)
        for test in tests:
            p.cur = 0
            p.tokens = tokenise(test)
            self.assertRaises(AssertionError, p.parse_statement)

    def test_valid_expr(self):
        tests = {
            "1": ast.Literal(Token(T.INTEGER, "1")),
            "true": ast.Literal(Token(T.BOOLEAN, "true")),
            "test": ast.Identifier("test"),
            "[x:y]": ast.RangeExpr(
                ast.Identifier("x"),
                ast.Identifier("y"),
            ),
            "(test)": ast.GroupExpr(ast.Identifier("test")),
            "test(x, y)": ast.CallExpr(
                ast.Identifier("test"),
                [
                    ast.Identifier("x"),
                    ast.Identifier("y"),
                ],
            ),
            "test[x]": ast.IndexExpr(
                ast.Identifier("test"),
                ast.Identifier("x"),
            ),
            "test.x": ast.SelectorExpr(
                ast.Identifier("test"),
                ast.Identifier("x"),
            ),
            "!test": ast.UnaryExpr(
                Token(T.BANG, "!"),
                ast.Identifier("test"),
            ),
            "x + y": ast.BinaryExpr(
                Token(T.PLUS, "+"),
                ast.Identifier("x"),
                ast.Identifier("y"),
            ),
        }

        p = Parser(None)
        for test, expected in tests.items():
            p.cur = 0
            p.tokens = tokenise(test)
            self.assertEqual(p.parse_expression(), expected)

    @unittest.expectedFailure
    def test_invalid_expr(self):
        tests = [
            ":",
            "() + 1",
            "while",
            "[var:y]",
            "(:)",
            "test(x, var)",
            "test[fn]",
            "test.var",
            "!if",
            "var + x",
        ]

        p = Parser(None)
        for test in tests:
            p.cur = 0
            p.tokens = tokenise(test)
            self.assertRaises(AssertionError, p.parse_expression)

    def test_binop_precs(self):
        tests = {
            "a * b - c / d": ast.BinaryExpr(
                Token(T.MINUS, "-"),
                ast.BinaryExpr(
                    Token(T.STAR, "*"),
                    ast.Identifier("a"),
                    ast.Identifier("b"),
                ),
                ast.BinaryExpr(
                    Token(T.SLASH, "/"),
                    ast.Identifier("c"),
                    ast.Identifier("d"),
                ),
            ),
            "a * b != c - d / e": ast.BinaryExpr(
                Token(T.BANG_EQUALS, "!="),
                ast.BinaryExpr(
                    Token(T.STAR, "*"),
                    ast.Identifier("a"),
                    ast.Identifier("b"),
                ),
                ast.BinaryExpr(
                    Token(T.MINUS, "-"),
                    ast.Identifier("c"),
                    ast.BinaryExpr(
                        Token(T.SLASH, "/"),
                        ast.Identifier("d"),
                        ast.Identifier("e"),
                    ),
                ),
            ),
        }

        p = Parser(None)
        for test, expected in tests.items():
            p.cur = 0
            p.tokens = tokenise(test)
            self.assertEqual(p.parse_expression(), expected)
