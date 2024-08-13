import unittest
import src.python.ir_nodes as ir
from src.python import type_defs as types
from src.python.cmd import translate
import src.python.builtin as builtin


class TestIR(unittest.TestCase):
    def test_globals(self):
        tests = {
                """
                fn main() {
                }
                """:
                "\n0001:\n DEFINE main() 0002\n0002:\n [empty]"
                }

        for test, expected in tests.items():
            self.assertEqual(str(translate(test, make_ir=True, test=True)), expected)

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
