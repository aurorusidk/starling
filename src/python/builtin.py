from .type_defs import BasicType, BasicTypeKind, BasicTypeFlag
from . import type_defs
from . import ir_nodes as ir
from .scope import Scope


types = {
    "int": BasicType(BasicTypeKind.INT, BasicTypeFlag.INTEGER, "int"),
    "float": BasicType(BasicTypeKind.FLOAT, BasicTypeFlag.FLOAT, "float"),
    "frac": BasicType(BasicTypeKind.FRAC, BasicTypeFlag.RATIONAL, "frac"),
    "str": BasicType(BasicTypeKind.STR, BasicTypeFlag.STRING, "str"),
    "bool": BasicType(BasicTypeKind.BOOL, BasicTypeFlag.BOOLEAN, "bool"),
}

# TODO: builtin name definitions (vars and funcs)
names = {
    "range_constructor@builtin": ir.FunctionSigRef(
        "range_constructor@builtin",
        type_defs.FunctionType(
            type_defs.ArrayType(types["int"], None),
            [types["int"], types["int"]]
        ),
        {"start": types["int"], "end": types["int"]},
        ir.Type(
            "arr[int,None]",
            hint=type_defs.ArrayType(types["int"], None),
            checked=type_defs.ArrayType(types["int"], None)
        )
    ),
}

scope = Scope(None)
for name, value in types.items():
    ref = ir.Type(name, value, checked=value)
    scope.declare(name, ref)
for name, value in names.items():
    scope.declare(name, value)
