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

    def test_valid_stmt(self):
        pass

    def test_valid_expr(self):
        pass

    def test_binop_precs(self):
        # make sure that operator precedences are respected
        pass

    # testing for errors in parsing
    # ensure every error condition is tested for
    
