import unittest
from src.python import lexer
from src.python.parser import parse, Parser
import src.python.ast_nodes as ast


class TestParser(unittest.TestCase):
    # basic testing for each node
    def test_valid_declr(self):
        tests = {
            "fn test(x int, y int) int {}": ast.FunctionDeclr(
                ast.Identifier("test"),
                ast.TypeName(ast.Identifier("int")),
                [
                    ast.Parameter(
                        ast.Identifier("x"),
                        ast.TypeName(ast.Identifier("int")),
                    ),
                    ast.Parameter(
                        ast.Identifier("y"),
                        ast.TypeName(ast.Identifier("int")),
                    ),
                ],
                ast.Block([]),
            ),

            "struct test {x int, y int}": ast.StructDeclr(
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
            p.tokens = lexer.tokenise(test)
            self.assertEqual(p.parse_declaration(), expected)

    @unittest.expectedFailure
    def test_invalid_declr(self):
        #TODO: implement correct parser errors, so test works correctly
        tests = [
            "func test(x int, y int) int {}",
            "struct test (x int, y int)",
            "var test == x;",
            "var test = x",
        ]

        p = Parser(None)
        for test in tests:
            p.cur = 0
            p.tokens = lexer.tokenise(test)
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
            p.tokens = lexer.tokenise(test)
            self.assertEqual(p.parse_statement(), expected)

    def test_invalid_stmt(self):
        pass

    def test_valid_expr(self):
        tests = {
            "1": ast.Literal(lexer.Token(lexer.INTEGER, "1")),
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
                lexer.Token(lexer.BANG, "!"),
                ast.Identifier("test"),
            ),
            "x + y": ast.BinaryExpr(
                lexer.Token(lexer.PLUS, "+"),
                ast.Identifier("x"),
                ast.Identifier("y"),
            ),
        }

        p = Parser(None)
        for test, expected in tests.items():
            p.cur = 0
            p.tokens = lexer.tokenise(test)
            self.assertEqual(p.parse_expression(), expected)

    def test_invalid_expr(self):
        pass

    def test_binop_precs(self):
        # make sure that operator precedences are respected
        tests = {
            "a * b - c / d": ast.BinaryExpr(
                lexer.Token(lexer.MINUS, "-"),
                ast.BinaryExpr(
                    lexer.Token(lexer.STAR, "*"),
                    ast.Identifier("a"),
                    ast.Identifier("b"),
                ),
                ast.BinaryExpr(
                    lexer.Token(lexer.SLASH, "/"),
                    ast.Identifier("c"),
                    ast.Identifier("d"),
                ),
            ),
            "a * b != c - d / e": ast.BinaryExpr(
                lexer.Token(lexer.BANG_EQUALS, "!="),
                ast.BinaryExpr(
                    lexer.Token(lexer.STAR, "*"),
                    ast.Identifier("a"),
                    ast.Identifier("b"),
                ),
                ast.BinaryExpr(
                    lexer.Token(lexer.MINUS, "-"),
                    ast.Identifier("c"),
                    ast.BinaryExpr(
                        lexer.Token(lexer.SLASH, "/"),
                        ast.Identifier("d"),
                        ast.Identifier("e"),
                    ),
                ),
            ),
        }

        p = Parser(None)
        for test, expected in tests.items():
            p.cur = 0
            p.tokens = lexer.tokenise(test)
            self.assertEqual(p.parse_expression(), expected)

    # testing for errors in parsing
    # ensure every error condition is tested for
    
