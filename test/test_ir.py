import unittest
from src.python.lexer import tokenise
from src.python.parser import Parser
from src.python.ir import IRNoder
from src.python import builtin
from src.python import type_defs as types
from src.python.cmd import translate


class TestIR(unittest.TestCase):
    def test_globals(self):
        tests = {}  # include main function, struct, function declr, interfaces(when done)

        for test in tests:
            translate(test, {"make_ir": True})

    def test_valid_ref(self):
        tests = {}

    def test_invalid_ref(self):
        tests = {}

    def test_valid_instr(self):
        tests = {}

    def test_invalid_instr(self):
        tests = {}

    def test_valid_object(self):
        tests = {}

    def test_invalid_object(self):
        tests = {}
