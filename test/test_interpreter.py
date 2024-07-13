import unittest
from src.python.lexer import tokenise
from src.python.parser import parse
from src.python.type_checker import TypeChecker
from src.python.interpreter import Interpreter, StaObject, StaFunction, StaFunctionReturn
from src.python import ast_nodes as ast
from src.python import builtin
from src.python import type_defs as types


class TestInterpreter(unittest.TestCase):
    def test_expr_eval(self):
        tests = {
            "1 + 1": StaObject(builtin.types["int"], 2),
        }

        for test, expected in tests.items():
            test = "fn test() {return " + test + ";}"
            tokens = tokenise(test)
            ast = parse(tokens)
            tc = TypeChecker(ast)
            tc.check(ast)
            interpreter = Interpreter()
            interpreter.eval_node(ast)
            try:
                f = interpreter.scope.lookup("test")
                interpreter.eval_node(f.block)
            except StaFunctionReturn as result:
                self.assertEqual(result.value, expected)
            else:
                assert False

    def test_stmt_eval(self):
        tests = {
            "if true {return 1;}": StaObject(builtin.types["int"], 1),
        }

        for test, expected in tests.items():
            test = "fn test() {" + test + "}"
            tokens = tokenise(test)
            ast = parse(tokens)
            tc = TypeChecker(ast)
            tc.check(ast)
            interpreter = Interpreter()
            interpreter.eval_node(ast)
            try:
                f = interpreter.scope.lookup("test")
                interpreter.eval_node(f.block)
            except StaFunctionReturn as result:
                self.assertEqual(result.value, expected)
            else:
                assert False

    def test_declr_eval(self):
        tests = {
            "fn test() int {}": StaFunction(
                types.FunctionType(builtin.types["int"], []),
                "test",
                [],
                ast.Block([]),
            ),
        }

        for test, expected in tests.items():
            tokens = tokenise(test)
            tree = parse(tokens)
            tc = TypeChecker(tree)
            tc.check(tree)
            interpreter = Interpreter()
            interpreter.eval_node(tree)
            self.assertEqual(interpreter.scope.lookup("test"), expected)
