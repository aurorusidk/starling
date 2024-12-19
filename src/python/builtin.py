from .type_defs import TypeFlag
from . import type_defs
from . import ir_nodes as ir
from .scope import Scope


scope = Scope(None)

types = {
    "meta": type_defs.Type(0, TypeFlag.META, "meta"),
    "int": type_defs.Type(32, TypeFlag.SIGNED_INT, "int"),
    "float": type_defs.Type(64, TypeFlag.FLOAT, "float"),
    # TODO: frac is just the width of two ints for now
    "frac": type_defs.Type(64, TypeFlag.RATIONAL, "frac"),
    "char": type_defs.Type(8, TypeFlag.STRING, "char"),
    "bool": type_defs.Type(1, TypeFlag.BOOLEAN, "bool"),
}
for name, value in types.items():
    type_value = ir.Constant(value)
    ref = ir.ConstRef(name, value=type_value)
    scope.declare(name, ref)
    # meta must be the first type for this to work
    ref.typ = type_value.typ = scope.lookup("meta")

# TODO: bit width of a string
string_type = type_defs.Type(0, TypeFlag.STRING, "str")
types["str"] = string_type
string_type_ref = ir.SequenceType(
    name="str",
    elem_type=scope.lookup("char")
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
                name="arr<int[None]>",
                elem_type=int_type
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
