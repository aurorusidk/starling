import logging
import unittest
from src.python.lexer import tokenise, Token, TokenType as T, Pos
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

    def test_invalid_stmt(self):
        # TODO: add more variations
        tests = [
            "if test () else ()",
            "whiletest {}",
            "return test",
        ]

        p = Parser(None)
        for test in tests:
            p.cur = 0
            p.tokens = tokenise(test)
            self.assertRaises(AssertionError, p.parse_statement)

    def test_valid_expr(self):
        tests = {
            "1": ast.Literal(Token(T.INTEGER, "1", Pos(1, 1))),
            "true": ast.Literal(Token(T.BOOLEAN, "true", Pos(1, 1))),
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
                Token(T.BANG, "!", Pos(1, 1)),
                ast.Identifier("test"),
            ),
            "x + y": ast.BinaryExpr(
                Token(T.PLUS, "+", Pos(1, 3)),
                ast.Identifier("x"),
                ast.Identifier("y"),
            ),
        }

        p = Parser(None)
        for test, expected in tests.items():
            p.cur = 0
            p.tokens = tokenise(test)
            self.assertEqual(p.parse_expression(), expected)

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
                Token(T.MINUS, "-", Pos(1, 7)),
                ast.BinaryExpr(
                    Token(T.STAR, "*", Pos(1, 3)),
                    ast.Identifier("a"),
                    ast.Identifier("b"),
                ),
                ast.BinaryExpr(
                    Token(T.SLASH, "/", Pos(1, 11)),
                    ast.Identifier("c"),
                    ast.Identifier("d"),
                ),
            ),
            "a * b != c - d / e": ast.BinaryExpr(
                Token(T.BANG_EQUALS, "!=", Pos(1, 7)),
                ast.BinaryExpr(
                    Token(T.STAR, "*", Pos(1, 3)),
                    ast.Identifier("a"),
                    ast.Identifier("b"),
                ),
                ast.BinaryExpr(
                    Token(T.MINUS, "-", Pos(1, 12)),
                    ast.Identifier("c"),
                    ast.BinaryExpr(
                        Token(T.SLASH, "/", Pos(1, 16)),
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

    def test_error_reporting(self):
        tests = [
            # Tests given as a tuple:
                # A string for the code
                # A tuple for the expected logs, as regexes
                
            ("""fn test() {
                    var a int = 1;
                    var b int == 2;
                    var c str = 3;
                }""",
                (
                    "expected(.+)TokenType.SEMICOLON",
                    "Failed to parse primary"
                )
            )
        ]

        p = Parser(None, (lambda err: logging.error(err)))
        for test in tests:
            p.cur = 0
            p.tokens = tokenise(test[0])
            with self.assertLogs(level=logging.ERROR) as cm:
                p.parse_program()

                # Check that the right number of errors were logged
                self.assertEqual(len(cm.output), len(test[1]))

                for log, expected in zip(cm.output, test[1]):
                    self.assertRegex(log, expected)
