from type_defs import BaseType, BaseTypeKind, BaseTypeFlag


types = (
        BaseType(BaseTypeKind.INT, BaseTypeFlag.INTEGER, "int"),
        BaseType(BaseTypeKind.FLOAT, BaseTypeFlag.FLOAT, "float"),
        BaseType(BaseTypeKind.FRAC, BaseTypeFlag.RATIONAL, "frac"),
        BaseType(BaseTypeKind.STR, BaseTypeFlag.STRING, "str"),
        BaseType(BaseTypeKind.BOOL, BaseTypeFlag.BOOLEAN, "bool"),
)

# TODO: builtin name definitions (vars and funcs)

