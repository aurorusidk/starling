import logging

from .lexer import TokenType as T
from . import ast_nodes as ast
from . import builtin
from . import type_defs as types


class Scope:
    def __init__(self, parent):
        self.parent = parent
        self.children = []
        self.name_map = {}

    def strict_lookup(self, name):
        return self.name_map.get(name)

    def lookup(self, name):
        s = self
        while not (val := s.strict_lookup(name)):
            s = s.parent
            if not s:
                return None
        return val

    def declare(self, name: ast.Identifier, typ):
        self.name_map[name.value] = typ


unary_op_preds = {
    T.MINUS: types.is_numeric,
    T.BANG: types.is_bool,
}

binary_op_preds = {
    T.PLUS: lambda t: types.is_numeric(t) or types.is_string(t),
    T.MINUS: types.is_numeric,
    T.STAR: types.is_numeric,
    T.SLASH: types.is_numeric,
}


def is_comparison_op(op):
    return op.typ in (
        T.GREATER_THAN, T.LESS_THAN, T.GREATER_EQUALS, T.LESS_EQUALS,
        T.EQUALS_EQUALS, T.BANG_EQUALS,
    )


class TypeChecker:
    def __init__(self, root, error_handler=None):
        self.scope = Scope(None)
        self.scope.name_map = builtin.types | builtin.names
        self.root = root
        # used to infer return types
        self.function = None
        self.error_handler = error_handler

    def error(self, msg):
        if self.error_handler is None:
            assert False, msg

        self.error_handler(msg)

    def new_scope(self):
        new_scope = Scope(self.scope)
        self.scope.children.append(new_scope)
        self.scope = new_scope

    def exit_scope(self):
        self.scope = self.scope.parent

    def match_types(self, lhs, rhs):
        if types.is_basic(lhs):
            return lhs == rhs \
                or types.is_numeric(lhs) and types.is_numeric(rhs)
        else:
            assert False, f"Unimplemented: cannot match types {lhs}, {rhs}"

    def get_binary_numeric(self, lhs, rhs):
        if builtin.types["float"] in (lhs.typ, rhs.typ):
            return builtin.types["float"]
        elif builtin.types["frac"] in (lhs.typ, rhs.typ):
            return builtin.types["frac"]
        elif builtin.types["int"] in (lhs.typ, rhs.typ):
            return builtin.types["int"]
        else:
            assert False, f"Unimplemented: cannot get numeric" \
                f"from {lhs.typ}, {rhs.typ}"

    def check(self, node):
        match node:
            case ast.Expr():
                self.check_expr(node)
            case ast.Type():
                self.check_type(node)
            case ast.Stmt():
                self.check_stmt(node)
            case ast.Declr():
                self.check_declr(node)
            case ast.Program(declrs):
                for declr in declrs:
                    self.check(declr)
            case _:
                assert False, f"Unexpected node {node}"

    def check_expr(self, node):
        match node:
            case ast.Literal(tok):
                match tok.typ:
                    case T.INTEGER:
                        node.typ = builtin.types["int"]
                    case T.FLOAT:
                        node.typ = builtin.types["float"]
                    case T.RATIONAL:
                        node.typ = builtin.types["frac"]
                    case T.STRING:
                        node.typ = builtin.types["str"]
                    case T.BOOLEAN:
                        node.typ = builtin.types["bool"]
                    case _:
                        assert False, f"Unknown literal type {tok.typ}"

            case ast.Identifier(name):
                # lookup the name
                node.typ = self.scope.lookup(name)
                if node.typ is None:
                    self.error(f"Undefined name {name}")

            case ast.RangeExpr(start, end):
                self.check_expr(start)
                self.check_expr(end)
                if start.typ != end.typ != builtin.types["int"]:
                    self.error("Invalid range expr")
                node.typ = types.ArrayType(builtin.types["int"], None)
                # TODO: add length eval for consts

            case ast.GroupExpr(expr):
                self.check_expr(expr)
                node.typ = expr.typ

            case ast.CallExpr(target, args):
                self.check(target)
                if isinstance(target.typ, types.FunctionType):
                    for i, arg in enumerate(args):
                        self.check_expr(arg)
                        if target.typ.param_types[i] is None:
                            target.typ.param_types[i] = arg.typ
                        elif arg.typ != target.typ.param_types[i]:
                            self.error("Types do not match")
                    if target.typ.return_type is not None:
                        node.typ = target.typ.return_type
                elif isinstance(target.typ, types.StructType):
                    if len(target.typ.fields) != len(args):
                        self.error("Incorrect number of field arguments")
                    for ftype, arg in zip(target.typ.fields.values(), args):
                        self.check_expr(arg)
                        if arg.typ != ftype:
                            self.error(
                                "Argument type does not match field type"
                            )
                    node.typ = target.typ

            case ast.IndexExpr(target, index):
                self.check(target)
                self.check(index)
                assert index.typ == builtin.types["int"]
                if target.typ == builtin.types["str"]:
                    node.typ = target.typ
                elif types.is_iterable(target.typ):
                    node.typ = target.typ.elem_type
                else:
                    self.error("Item cannot be indexed")
                # TODO: add map case once implemented

            case ast.SelectorExpr(target, name):
                self.check(target)
                method = target.typ.methods.get(name.value)
                field = None
                if isinstance(target.typ, types.StructType):
                    field = target.typ.fields.get(name.value)

                if method is not None:
                    if field is not None:
                        self.error("Conflicting name between method and field")
                    node.typ = method.checked_type
                elif field is not None:
                    node.typ = field
                else:
                    self.error(f"Could not resolve name {name.value} in {target.typ}")

            case ast.UnaryExpr():
                self.check_unary(node)

            case ast.BinaryExpr():
                self.check_binary(node)

            case _:
                self.error(f"Unreachable: could not match expr {node}")

    def check_unary(self, node):
        self.check(node.rhs)

        pred = unary_op_preds[node.op.typ]
        if not pred(node.rhs.typ):
            self.error(f"Unsupported op {node.op.typ} on {node.rhs.typ}")

        # none of the operations change the type of the operand
        node.typ = node.rhs.typ

    def check_binary(self, node):
        self.check(node.lhs)
        self.check(node.rhs)

        # for now all ops require matching types
        if not self.match_types(node.lhs.typ, node.rhs.typ):
            self.error(f"Mismatched types {node.lhs.typ} and {node.rhs.typ}")

        if is_comparison_op(node.op):
            node.typ = builtin.types["bool"]
            # TODO: more specific comparison checking (e.g., ordered types)
            # self.check_comparison(node)
            return

        pred = binary_op_preds[node.op.typ]
        if not pred(node.lhs.typ):
            self.error(f"Unsupported op {node.op.typ} on {node.lhs.typ}")

        if node.op.typ == T.SLASH:
            node.typ = builtin.types["float"]
        elif types.is_numeric(node.lhs.typ):
            node.typ = self.get_binary_numeric(node.lhs, node.rhs)
        else:
            node.typ = node.lhs.typ
        logging.debug(node)

    def check_type(self, node):
        match node:
            case ast.TypeName(value):
                typ = self.scope.lookup(value.value)
                if not isinstance(typ, types.Type):
                    self.error(f"{value.value} is not a valid type")
                return typ

            case ast.ArrayType(length, elem_type):
                # TODO: check if length is a constant
                self.check_expr(length)
                if length.typ != builtin.types["int"]:
                    self.error("Array length must be a integer")
                return types.ArrayType(None, self.check_type(elem_type))

            case _:
                assert False, f"Unreachable: could not match type {node}"

    def check_stmt(self, node):
        match node:
            case ast.Block(stmts):
                for stmt in stmts:
                    self.check_stmt(stmt)
            case ast.DeclrStmt(declr):
                self.check_declr(declr)
            case ast.ExprStmt(expr):
                self.check_expr(expr)
            case ast.IfStmt(condition, if_block, else_block):
                self.check_expr(condition)
                # TODO: maybe skip this check to have 'truthy'/'falsy'
                assert condition.typ == builtin.types["bool"]

                self.check_stmt(if_block)
                if else_block is not None:
                    self.check_stmt(else_block)

            case ast.WhileStmt(condition, block):
                self.check_expr(condition)
                # TODO: maybe skip this check to have 'truthy'/'falsy'
                assert condition.typ == builtin.types["bool"]

                self.check_stmt(block)

            case ast.ReturnStmt(value):
                self.check(value)
                if self.function is None:
                    self.error("Return statement outside a function")
                if self.function.return_type is None:
                    self.function.return_type = value.typ
                elif self.function.return_type != value.typ:
                    self.error(
                        f"Return value with type {value.typ} "
                        f"does not match function return type "
                        f"{self.function.return_type}"
                    )
                # TODO: log the return statements
                #       to check if a value is ever returned

            case ast.AssignmentStmt(target, value):
                self.check_expr(target)
                self.check_expr(value)
                # TODO: if both are numeric the target should be coerced
                #       for explicitly typed targets probably not?
                if target.typ != value.typ:
                    self.error(f"Cannot assign {value} to {target}")

            case _:
                assert False, f"Unreachable: could not match stmt {node}"

    def check_function_signature(self, node):
        param_types = []
        for param in node.params:
            typ = None
            logging.debug(param)
            if param.typ is not None:
                typ = self.check_type(param.typ)
                param_types.append(typ)

        return_type = None
        if node.return_type is not None:
            return_type = self.check_type(node.return_type)
        return types.FunctionType(return_type, param_types)

    def check_declr(self, node):
        match node:
            case ast.FunctionDeclr(signature, block):
                # TODO: inference on parameters needs to be done from CallExprs
                #       we need to defer checking until the type is concrete
                ftype = self.check_function_signature(signature)
                self.scope.declare(signature.name, ftype)

                # TODO: defer this section until all declarations are checked
                #       so functions can be used before they are declared
                self.new_scope()
                for param, ptype in zip(signature.params, ftype.param_types):
                    self.scope.declare(param.name, ptype)
                prev_function = self.function
                self.function = ftype
                self.check(block)
                self.function = prev_function
                self.exit_scope()
                node.checked_type = ftype

            case ast.StructDeclr(name, fields):
                members = {}
                for field in fields:
                    members[field.name.value] = self.check_type(field.typ)
                struct = types.StructType(name.value, members)
                self.scope.declare(name, struct)
                node.checked_type = struct

            case ast.InterfaceDeclr(name, methods):
                members = {}
                for method in methods:
                    mname = method.name.value
                    members[mname] = self.check_function_signature(method)
                interface = types.Interface(name.value, members)
                self.scope.declare(name, interface)
                node.checked_type = interface
                logging.debug(interface)

            case ast.ImplDeclr(target, interface, methods):
                target = self.check_type(target)
                if interface is not None:
                    interface = self.scope.lookup(interface.value)
                    assert isinstance(interface, types.Interface), \
                        "Cannot implement non-interface"

                self.new_scope()
                self.scope.declare(ast.Identifier("self"), target)
                for method in methods:
                    # TODO: ensure only interface methods can be defined
                    self.check_declr(method)
                    target.methods[method.signature.name.value] = method
                self.exit_scope()

            case ast.VariableDeclr(name, typ, value):
                if value is not None:
                    self.check_expr(value)

                if typ is not None:
                    typ = self.check_type(typ)
                    if value is not None:
                        if value.typ != typ:
                            self.error(
                                f"Cannot assign value with type {value.typ} "
                                f"to variable {name.value} with type {typ}"
                            )
                    self.scope.declare(name, typ)
                    node.checked_type = typ
                else:
                    if value is None:
                        self.scope.declare(name, None)
                    else:
                        self.scope.declare(name, value.typ)
                        node.checked_type = value.typ

            case _:
                assert False, f"Unreachable: could not match declr {node}"


if __name__ == "__main__":
    import lexer
    import parser

    logging.basicConfig(format="%(levelname)s: %(message)s")
    logging.getLogger().setLevel(logging.DEBUG)
    with open("input.txt") as f:
        src = f.read()
    toks = lexer.tokenise(src)
    tree = parser.parse(toks)
    tc = TypeChecker(tree)
    tc.check(tree)
