import unittest
from src.python.lexer import tokenise
from src.python.parser import Parser
from src.python.type_checker import TypeChecker
from src.python.interpreter import Interpreter, StaObject
from src.python import builtin
from src.python import type_defs as types


class TestInterpreter(unittest.TestCase):
    def test_expr_eval(self):
        pass

    def test_stmt_eval(self):
        pass

    def test_declr_eval(self):
        pass

