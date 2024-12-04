from .type_defs import BasicType, BasicTypeKind, BasicTypeFlag
from . import type_defs
from . import ir_nodes as ir
from .scope import Scope


scope = Scope(None)

types = {
    "int": BasicType(BasicTypeKind.INT, BasicTypeFlag.INTEGER, "int"),
    "float": BasicType(BasicTypeKind.FLOAT, BasicTypeFlag.FLOAT, "float"),
    "frac": BasicType(BasicTypeKind.FRAC, BasicTypeFlag.RATIONAL, "frac"),
    "char": BasicType(BasicTypeKind.CHAR, BasicTypeFlag.STRING, "char"),
    "bool": BasicType(BasicTypeKind.BOOL, BasicTypeFlag.BOOLEAN, "bool"),
}
for name, value in types.items():
    ref = ir.Type(name, raw_type=value)
    scope.declare(name, ref)

string_type = type_defs.BasicType(BasicTypeKind.STR, BasicTypeFlag.STRING, "str")
types["str"] = string_type
string_type_ref = ir.SequenceType(
    name="str",
    elem_type=scope.lookup("char"),
    raw_type=string_type
)
scope.declare("str", string_type_ref)

int_type = scope.lookup("int")
names = {
    "range_constructor@builtin": ir.FunctionRef(
        "range_constructor@builtin",
        typ=ir.FunctionSigRef(
            "range_constructor@builtin",
            {"start": int_type, "end": int_type},
            ir.SequenceType(
                name="arr[int,None]",
                elem_type=int_type,
                raw_type=type_defs.ArrayType(types["int"], None),
            ),
            raw_type=type_defs.FunctionType(
                type_defs.ArrayType(types["int"], None),
                [types["int"], types["int"]]
            ),
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
