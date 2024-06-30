from dataclasses import dataclass
import logging

from lexer import TokenType as T
import ast_nodes as ast
import builtin
import type_defs as types


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
    def __init__(self, root):
        self.scope = Scope(None)
        self.root = root

    def new_scope(self):
        new_scope = Scope(self.scope)
        self.scope.children.append(new_scope)
        self.scope = new_scope

    def exit_scope(self):
        self.scope = self.scope.parent

    def match_types(self, lhs, rhs):
        if types.is_basic(lhs):
            return lhs == rhs or types.is_numeric(lhs) and types.is_numeric(rhs)
        else:
            assert False, f"Unimplemented: cannot match types {type1}, {type2}"

    def get_binary_numeric(self, lhs, rhs):
        if builtin.types["float"] in (lhs.typ, rhs.typ):
            return builtin.types["float"]
        elif builtin.types["frac"] in (lhs.typ, rhs.typ):
            return builtin.types["frac"]
        elif builtin.types["int"] in (lhs.typ, rhs.typ):
            return builtin.types["int"]
        else:
            assert False, f"Unimplemented: cannot get numeric from {lhs.typ}, {rhs.typ}"

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

            case ast.RangeExpr(start, end):
                self.check_expr(start)
                self.check_expr(end)
                if start.typ != end.typ != builtin.types["int"]:
                    assert False, "Invalid range expr"
                # TODO: how should ranges be typed?
                assert False, "Unimplemented: range expressions"

            case ast.GroupExpr(expr):
                self.check_expr(expr)
                node.typ = expr.typ

            case ast.CallExpr(target, args):
                target = self.check(target)
                args = [self.check_expr(arg) for arg in args]
                # TODO: check args against signature in target

            case ast.IndexExpr(target, index):
                self.check(target)
                self.check(index)
                # TODO: there are a few cases here: strings, arrays, vecs, maps
                assert False, "Unimplemented: index expressions"

            case ast.SelectorExpr(target, name):
                self.check(target)
                # TODO: there are no valid targets yet?
                assert False, "Unimplemented: selector expressions"
            case ast.UnaryExpr(op, rhs):
                assert False, "Unimplemented: unary expressions"
                pass
            case ast.BinaryExpr():
                self.check_binary(node)
            case _:
                assert False, f"Unreachable: could not match expr {node}"

    def check_binary(self, node):
        self.check(node.lhs)
        self.check(node.rhs)

        # for now all ops require matching types
        assert self.match_types(node.lhs.typ, node.rhs.typ)

        if is_comparison_op(node.op):
            node.typ = builtin.types["bool"]
            # TODO: more specific comparison checking (e.g., ordered types)
            self.check_comparison(node)

        pred = binary_op_preds.get(node.op.typ)
        if not pred(node.lhs.typ):
            assert False, f"Unsupported op {node.op.typ} on {lhs.typ}"

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
                return builtin.types[value.value]
            case ast.ArrayType(length, elem_t):
                pass
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

                self.check_block(if_block)
                self.check_block(else_block)

            case ast.WhileStmt(condition, block):
                self.check_expr(condition)
                # TODO: maybe skip this check to have 'truthy'/'falsy'
                assert condition.typ == builtin.types["bool"]

                self.check_block(block)

            case ast.ReturnStmt(value):
                self.check(value)
                # TODO: compare the value with the return type of the current function

            case ast.AssignmentStmt(target, value):
                self.check_expr(target)
                self.check_expr(value)
                # TODO: if both are numeric the target should be coerced
                assert target.typ == value.typ, f"Cannot assign {value} to {target}"

            case _:
                assert False, f"Unreachable: could not match stmt {node}"

    def check_declr(self, node):
        match node:
            case ast.FunctionDeclr(name, return_t, params, block):
                # TODO: allow for type inference
                param_types = []
                for param in params:
                    param_types.append(self.check_type(param.type))

                return_type = self.check_type(return_t)
                ftype = types.FunctionType(return_type, param_types)

                self.scope.declare(name, ftype)

                self.new_scope()
                self.check(block)
                self.exit_scope()

            case ast.VariableDeclr(name, typ, value):
                self.check_expr(value)
                # TODO: vars with no initialiser should use the declared type
                if typ is not None:
                    assert value.typ == self.check_type(typ), f"Cannot assign value with type {value.typ} " \
                            f"to variable {name.value}"
                self.scope.declare(name, value.typ)

            case _:
                assert False, f"Unreachable: could not match declr {node}"


if __name__ == "__main__":
    import lexer, parser

    logging.basicConfig(format="%(levelname)s: %(message)s")
    logging.getLogger().setLevel(logging.DEBUG)
    with open("input.txt") as f:
        src = f.read()
    toks = lexer.tokenise(src)
    tree = parser.parse(toks)
    tc = TypeChecker(tree)
    tc.check(tree)
