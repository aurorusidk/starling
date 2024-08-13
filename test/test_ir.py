import unittest
import src.python.ir_nodes as ir
from src.python import type_defs as types
from src.python.cmd import translate
import src.python.builtin as builtin


class TestIR(unittest.TestCase):
    def test_globals(self):
        # TODO: add testing for interfaces
        tests = {
            """
            """:
            ir.Program(
                ir.Block(
                    []
                )
            ),
            """fn main() {
            }
            """:
            ir.Program(
                ir.Block(
                    [
                        ir.DefFunc(
                            ir.FunctionSignatureRef("main", types.FunctionType(None, []), [], []),
                            (block := ir.Block([]))
                        )
                    ],
                    deps=[block]
                )
            ),
            """
            fn main() {
            }
            fn test() {
            }
            """:
            ir.Program(
                ir.Block(
                    [
                        ir.DefFunc(
                            ir.FunctionSignatureRef("main", types.FunctionType(None, []), [], []),
                            (block1 := ir.Block([]))
                        ),
                        ir.DefFunc(
                            ir.FunctionSignatureRef("test", types.FunctionType(None, []), [], []),
                            (block2 := ir.Block([]))
                        )
                    ],
                    deps=[block1, block2]
                )
            ),
            """
            struct test {
                a int; b int;
            }
            """:
            ir.Program(
                ir.Block(
                    [
                        ir.Declare(
                            ir.StructTypeRef("test", types.StructType(
                                [builtin.types["int"],
                                 builtin.types["int"]
                                 ]), ["a", "b"])
                        )
                    ],
                    deps=[]
                )
            ),
        }

        for test, expected in tests.items():
            print(translate(test, **{"make_ir": True}))
            print(expected)
            self.assertEqual(translate(test, **{"make_ir": True}), expected)

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
