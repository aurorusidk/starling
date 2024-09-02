from .type_defs import BasicType, BasicTypeKind, BasicTypeFlag
from . import type_defs
from . import ir_nodes as ir
from .scope import Scope


scope = Scope(None)

types = {
    "int": BasicType(BasicTypeKind.INT, BasicTypeFlag.INTEGER, "int"),
    "float": BasicType(BasicTypeKind.FLOAT, BasicTypeFlag.FLOAT, "float"),
    "frac": BasicType(BasicTypeKind.FRAC, BasicTypeFlag.RATIONAL, "frac"),
    "str": BasicType(BasicTypeKind.STR, BasicTypeFlag.STRING, "str"),
    "bool": BasicType(BasicTypeKind.BOOL, BasicTypeFlag.BOOLEAN, "bool"),
}
for name, value in types.items():
    ref = ir.Type(name, value, checked=value)
    scope.declare(name, ref)

int_type = scope.lookup("int")
names = {
    "range_constructor@builtin": ir.FunctionRef(
        "range_constructor@builtin",
        typ=ir.FunctionSigRef(
            "range_constructor@builtin",
            type_defs.FunctionType(
                type_defs.ArrayType(types["int"], None),
                [types["int"], types["int"]]
            ),
            {"start": int_type, "end": int_type},
            ir.SequenceType(
                name="arr[int,None]",
                elem_type=int_type,
                hint=type_defs.ArrayType(types["int"], None),
                checked=type_defs.ArrayType(types["int"], None),
            )
        ),
        params=[
            ir.Ref("start", typ=int_type),
            ir.Ref("end", typ=int_type),
        ],
        builtin=True
    ),
}
for name, value in names.items():
    scope.declare(name, value)
