import logging
import unittest
from src.python.lexer import Token, TokenType as T, Pos
import src.python.ast_nodes as ast
from src.python.cmd import translate


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

        for test, expected in tests.items():
            with self.subTest(test=test):
                self.assertEqual(translate(test, parse=True), ast.Program([expected]))

    def test_invalid_declr(self):
        # TODO: implement correct parser errors, so test works correctly
        tests = [
            "func test(x int, y int) int {}",
            "struct test {x int, y int}"
            "struct test (x int; y int;)",
            "var test == x;",
            "var test = x",
        ]

        for test in tests:
            with self.subTest(test=test):
                self.assertRaises(AssertionError, translate, test, parse=True)

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

        for test_contents, expected_contents in tests.items():
            test = "fn main() {" + test_contents + "}"
            expected = ast.Program(
                [
                    ast.FunctionDeclr(
                        ast.FunctionSignature(
                            ast.Identifier("main"),
                            None,
                            []
                        ),
                        ast.Block([expected_contents])
                    )
                ])

            with self.subTest(test=test):
                self.assertEqual(translate(test, parse=True), expected)

    def test_invalid_stmt(self):
        # TODO: add more variations
        tests = [
            "if test () else ()",
            "whiletest {}",
            "return test",
        ]

        for test in tests:
            with self.subTest(test=test):
                self.assertRaises(AssertionError, translate, test, parse=True)

    def test_valid_expr(self):
        tests = {
            "1": ast.Literal(Token(T.INTEGER, "1", Pos(1, 21))),
            "true": ast.Literal(Token(T.BOOLEAN, "true", Pos(1, 21))),
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
                Token(T.BANG, "!", Pos(1, 21)),
                ast.Identifier("test"),
            ),
            "x + y": ast.BinaryExpr(
                Token(T.PLUS, "+", Pos(1, 23)),
                ast.Identifier("x"),
                ast.Identifier("y"),
            ),
        }

        for test_contents, expected_contents in tests.items():
            test = "fn main() { var a = " + test_contents + ";}"
            expected = ast.Program(
                [
                    ast.FunctionDeclr(
                        ast.FunctionSignature(
                            ast.Identifier("main"),
                            None,
                            []
                        ),
                        ast.Block(
                            [
                                ast.DeclrStmt(
                                    ast.VariableDeclr(
                                        ast.Identifier("a"),
                                        None,
                                        expected_contents
                                    )
                                )
                            ]
                        )
                    )
                ])

            with self.subTest(test=test):
                self.assertEqual(translate(test, parse=True), expected)

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

        for test in tests:
            with self.subTest(test=test):
                self.assertRaises(AssertionError, translate, test, parse=True)

    def test_binop_precs(self):
        tests = {
            "a * b - c / d": ast.BinaryExpr(
                Token(T.MINUS, "-", Pos(1, 27)),
                ast.BinaryExpr(
                    Token(T.STAR, "*", Pos(1, 23)),
                    ast.Identifier("a"),
                    ast.Identifier("b"),
                ),
                ast.BinaryExpr(
                    Token(T.SLASH, "/", Pos(1, 31)),
                    ast.Identifier("c"),
                    ast.Identifier("d"),
                ),
            ),
            "a * b != c - d / e": ast.BinaryExpr(
                Token(T.BANG_EQUALS, "!=", Pos(1, 27)),
                ast.BinaryExpr(
                    Token(T.STAR, "*", Pos(1, 23)),
                    ast.Identifier("a"),
                    ast.Identifier("b"),
                ),
                ast.BinaryExpr(
                    Token(T.MINUS, "-", Pos(1, 32)),
                    ast.Identifier("c"),
                    ast.BinaryExpr(
                        Token(T.SLASH, "/", Pos(1, 36)),
                        ast.Identifier("d"),
                        ast.Identifier("e"),
                    ),
                ),
            ),
        }

        for test_contents, expected_contents in tests.items():
            test = "fn main() { var a = " + test_contents + ";}"
            expected = ast.Program(
                [
                    ast.FunctionDeclr(
                        ast.FunctionSignature(
                            ast.Identifier("main"),
                            None,
                            []
                        ),
                        ast.Block(
                            [
                                ast.DeclrStmt(
                                    ast.VariableDeclr(
                                        ast.Identifier("a"),
                                        None,
                                        expected_contents
                                    )
                                )
                            ]
                        )
                    )
                ])

            with self.subTest(test=test):
                self.assertEqual(translate(test, parse=True), expected)

    def test_error_reporting(self):
        tests = [
            # Tests given as a tuple:
            #   A string for the code
            #   A tuple for the expected logs, as regexes

            (
                """fn test() {
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

        for test in tests:
            with self.subTest(test=test):
                with self.assertLogs(level=logging.ERROR) as cm:
                    translate(test[0], parse=True, test=True)

                    # Check that the right number of errors were logged
                    self.assertEqual(len(cm.output), len(test[1]))

                    for log, expected in zip(cm.output, test[1]):
                        self.assertRegex(log, expected)
