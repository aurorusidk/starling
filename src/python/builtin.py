from type_defs import BasicType, BasicTypeKind, BasicTypeFlag


types = (
        BasicType(BasicTypeKind.INT, BasicTypeFlag.INTEGER, "int"),
        BasicType(BasicTypeKind.FLOAT, BasicTypeFlag.FLOAT, "float"),
        BasicType(BasicTypeKind.FRAC, BasicTypeFlag.RATIONAL, "frac"),
        BasicType(BasicTypeKind.STR, BasicTypeFlag.STRING, "str"),
        BasicType(BasicTypeKind.BOOL, BasicTypeFlag.BOOLEAN, "bool"),
)

# TODO: builtin name definitions (vars and funcs)

