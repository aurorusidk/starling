import logging

from .lexer import TokenType as T
from . import ast_nodes as ast


BINARY_OP_PRECEDENCE = {
    T.GREATER_THAN: 10,
    T.LESS_THAN: 10,
    T.GREATER_EQUALS: 10,
    T.LESS_EQUALS: 10,
    T.EQUALS_EQUALS: 10,
    T.BANG_EQUALS: 10,
    T.PLUS: 20,
    T.MINUS: 20,
    T.STAR: 30,
    T.SLASH: 30,
}


class Parser:
    def __init__(self, tokens):
        self.cur = 0
        self.tokens = tokens
        self.root = None

    def check(self, *token_types, lookahead=0):
        cur = self.cur + lookahead
        if cur >= len(self.tokens):
            return None
        logging.debug(f"checking: {token_types}")
        logging.debug(f"cur tok: {self.tokens[cur]}")
        if any(self.tokens[cur].typ == t for t in token_types):
            logging.debug("check passed")
            return self.tokens[cur]

    def consume(self, *token_types):
        result = self.check(*token_types)
        if result is not None:
            self.cur += 1
        return result

    def parse(self, tokens):
        # reinit
        self.cur = 0
        self.tokens = tokens
        self.root = self.parse_program()
        return self.root

    def parse_program(self):
        declarations = []
        while self.cur < len(self.tokens):
            logging.debug(f"declrs: {declarations}")
            declarations.append(self.parse_declaration())
        return ast.Program(declarations)

    def parse_declaration(self):
        if self.check(T.FUNC):
            return self.parse_function()
        elif self.check(T.STRUCT):
            return self.parse_struct()
        elif self.check(T.VAR):
            return self.parse_variable_declr()
        else:
            assert False, "Failed to parse declaration"

    def parse_function(self):
        self.consume(T.FUNC)
        fname = self.parse_identifier()
        self.consume(T.LEFT_BRACKET)

        params = []
        while not self.consume(T.RIGHT_BRACKET):
            pname = self.parse_identifier()
            ptype = None
            if not self.check(T.COMMA, T.RIGHT_BRACKET):
                ptype = self.parse_type()
            params.append(ast.Parameter(pname, ptype))
            self.consume(T.COMMA)

        ftype = None
        if not self.check(T.LEFT_CURLY):
            ftype = self.parse_type()
        contents = self.parse_block()
        return ast.FunctionDeclr(fname, ftype, params, contents)

    def parse_struct(self):
        self.consume(T.STRUCT)
        name = self.parse_identifier()
        fields = []
        self.consume(T.LEFT_CURLY)
        while not self.consume(T.RIGHT_CURLY):
            fields.append(self.parse_field_declr())
            self.consume(T.COMMA)
        return ast.StructDeclr(name, fields)

    def parse_field_declr(self):
        name = self.parse_identifier()
        typ = self.parse_type()
        return ast.FieldDeclr(name, typ)

    def parse_variable_declr(self):
        self.consume(T.VAR)
        name = self.parse_identifier()
        typ = None
        if not self.check(T.EQUALS, T.SEMICOLON):
            typ = self.parse_type()
        value = None
        if self.consume(T.EQUALS):
            value = self.parse_expression()
        self.consume(T.SEMICOLON)
        return ast.VariableDeclr(name, typ, value)

    def parse_type(self):
        if self.check(T.IDENTIFIER):
            return ast.TypeName(self.parse_identifier())
        elif self.check(T.LEFT_SQUARE):
            return self.parse_array_type()
        assert False, "Failed to parse type"

    def parse_array_type(self):
        self.consume(T.LEFT_SQUARE)
        length = self.parse_expression()
        self.consume(T.RIGHT_SQUARE)
        typ = self.parse_type()
        return ast.ArrayType(length, typ)

    def parse_block(self):
        statements = []
        self.consume(T.LEFT_CURLY)
        while not self.consume(T.RIGHT_CURLY) and self.cur < len(self.tokens):
            statements.append(self.parse_statement())
        return ast.Block(statements)

    def parse_statement(self):
        if self.check(T.FUNC, T.VAR):
            return ast.DeclrStmt(self.parse_declaration())
        elif self.check(T.IF):
            return self.parse_if()
        elif self.check(T.WHILE):
            return self.parse_while()
        elif self.check(T.RETURN):
            return self.parse_return()

        expr = self.parse_expression()
        if self.consume(T.SEMICOLON):
            return ast.ExprStmt(expr)
        elif self.check(T.EQUALS):
            return self.parse_assignment(expr)
        else:
            assert False, "Failed to parse statement"

    def parse_if(self):
        self.consume(T.IF)
        condition = self.parse_expression()
        if self.check(T.LEFT_CURLY):
            if_block = self.parse_block()
        else:
            if_block = self.parse_statement()
        if self.consume(T.ELSE):
            if self.check(T.LEFT_CURLY):
                else_block = self.parse_block()
            else:
                else_block = self.parse_statement()
        else:
            else_block = None
        return ast.IfStmt(condition, if_block, else_block)

    def parse_while(self):
        self.consume(T.WHILE)
        condition = self.parse_expression()
        while_block = self.parse_block()
        return ast.WhileStmt(condition, while_block)

    def parse_return(self):
        self.consume(T.RETURN)
        value = None
        if not self.check(T.SEMICOLON):
            value = self.parse_expression()
        self.consume(T.SEMICOLON)
        return ast.ReturnStmt(value)

    def parse_assignment(self, target):
        self.consume(T.EQUALS)
        value = self.parse_expression()
        self.consume(T.SEMICOLON)
        return ast.AssignmentStmt(target, value)

    def parse_expression(self):
        return self.parse_binary_expr()

    def parse_binary_expr(self, precedence=0):
        logging.debug(f"current prec: {precedence}")
        left = self.parse_unary_expr()
        logging.debug(f"{left}")
        while True:
            node = self.parse_binop_increasing_prec(left, precedence)
            if node == left:
                break
            left = node
        return left

    def parse_binop_increasing_prec(self, left, precedence):
        logging.debug(f"binop: {precedence}: {left}")
        if not (op := self.check(*BINARY_OP_PRECEDENCE.keys())):
            return left
        next_precedence = BINARY_OP_PRECEDENCE[op.typ]
        if next_precedence <= precedence:
            return left
        else:
            # skip the op we already found
            self.cur += 1
            right = self.parse_binary_expr(next_precedence)
            return ast.BinaryExpr(op, left, right)

    def parse_unary_expr(self):
        op = self.consume(T.MINUS, T.BANG)
        if op:
            right = self.parse_unary_expr()
            return ast.UnaryExpr(op, right)
        else:
            return self.parse_primary_expr()

    def parse_primary_expr(self):
        expr = self.parse_primary()
        while self.check(T.DOT, T.LEFT_SQUARE, T.LEFT_BRACKET):
            if self.check(T.DOT):
                expr = self.parse_selector(expr)
            elif self.check(T.LEFT_SQUARE):
                expr = self.parse_index(expr)
            elif self.check(T.LEFT_BRACKET):
                expr = self.parse_call_arguments(expr)
            else:
                assert False, "Unreachable"
        return expr

    def parse_selector(self, target):
        self.consume(T.DOT)
        name = self.parse_identifier()
        return ast.SelectorExpr(target, name)

    def parse_index(self, target):
        self.consume(T.LEFT_SQUARE)
        value = self.parse_expression()
        self.consume(T.RIGHT_SQUARE)
        return ast.IndexExpr(target, value)

    def parse_call_arguments(self, target):
        self.consume(T.LEFT_BRACKET)
        args = []
        while not self.consume(T.RIGHT_BRACKET):
            args.append(self.parse_expression())
            self.consume(T.COMMA)
        return ast.CallExpr(target, args)

    def parse_primary(self):
        if self.consume(T.LEFT_BRACKET):
            expr = self.parse_expression()
            self.consume(T.RIGHT_BRACKET)
            return ast.GroupExpr(expr)
        elif self.consume(T.LEFT_SQUARE):
            start = self.parse_expression()
            self.consume(T.COLON)
            end = self.parse_expression()
            self.consume(T.RIGHT_SQUARE)
            return ast.RangeExpr(start, end)
        elif self.check(T.IDENTIFIER):
            return self.parse_identifier()
        else:
            value = self.consume(
                T.INTEGER, T.FLOAT, T.RATIONAL, T.BOOLEAN, T.STRING,
            )
            if not value:
                assert False, "Failed to parse primary"
            return ast.Literal(value)

    def parse_identifier(self):
        tok = self.consume(T.IDENTIFIER)
        return ast.Identifier(tok.lexeme)


def parse(tokens):
    # helper that hides the class behaviour
    return Parser(tokens).parse_program()


def repr_children(children, indent=1):
    # recursive string representation for the node's children
    out = "[\n"
    for child in children:
        out += "|   " * indent
        if hasattr(child, "children"):
            out += child.typ.name + ": "
            out += repr_children(child.children, indent+1)
        elif isinstance(child, list):
            out += repr_children(child, indent+1)
        else:
            out += repr(child)
        out += "\n"
    out += "|   " * (indent - 1) + "]"
    return out


def repr_ast(ast):
    # more readable representation of the nodes
    out = ast.typ.name + ": "
    out += repr_children(ast.children)
    return out


if __name__ == "__main__":
    import sys
    from lexer import tokenise

    logging.basicConfig(format="%(levelname)s: %(message)s")
    logging.getLogger().setLevel(logging.DEBUG)
    if len(sys.argv) == 2:
        src_file = sys.argv[1]
    else:
        src_file = "input.txt"
    with open(src_file) as f:
        src = f.read()
    tokens = tokenise(src)
    print(tokens)
    tree = parse(tokens)
    print(tree)
