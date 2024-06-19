from collections import namedtuple
from enum import Enum, global_enum
import logging

from lexer import TokenType as T

NodeType = Enum("NodeType", [
    "PROGRAM", "FUNCTION", "TYPE",
    "BLOCK", "IF", "WHILE", "RETURN", "ASSIGNMENT",
    "BINARY_EXPR", "UNARY_EXPR", "PRIMARY", "CALL", "GROUP_EXPR",
])
# this may want to be changed to give each node type a static format
# rather than using the generic `children` list
Node = namedtuple("Node", ["typ", "children"])

# export members to global namespace
# when importing the types use NodeType
global_enum(NodeType)

BINARY_OP_PRECEDENCE = {
    T.PLUS: 10,
    T.MINUS: 10,
    T.STAR: 20,
    T.SLASH: 20,
    T.GREATER_THAN: 30,
    T.LESS_THAN: 30,
    T.GREATER_EQUALS: 30,
    T.LESS_EQUALS: 30,
    T.EQUALS_EQUALS: 30,
    T.BANG_EQUALS: 30,
}

TYPE_TOKENS = (
    T.INTEGER_TYPE, T.FLOAT_TYPE,
    T.STRING_TYPE, T.BOOL_TYPE
)


class Parser:
    def __init__(self):
        self.cur = 0
        self.tokens = []
        self.ast = None

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
        self.ast = self.parse_program()
        return self.ast

    def parse_program(self):
        declarations = []
        while self.cur < len(tokens):
            logging.debug(f"declrs: {declarations}")
            declarations.append(self.parse_declaration())
        return Node(PROGRAM, declarations)

    def parse_declaration(self):
        return self.parse_function()

    def parse_function(self):
        ftype = self.parse_type()
        fname = self.consume(T.IDENTIFIER)
        self.consume(T.LEFT_BRACKET)
        ptypes = []
        pnames = []
        while not self.consume(T.RIGHT_BRACKET):
            ptypes.append(self.parse_type())
            pnames.append(self.consume(T.IDENTIFIER))
            self.consume(T.COMMA)
        contents = self.parse_block()
        return Node(FUNCTION, [ftype, fname, ptypes, pnames, contents])

    def parse_type(self):
        tok = self.consume(*TYPE_TOKENS)
        if tok:
            return tok
        assert False, "Failed to parse type"

    def parse_block(self):
        statements = []
        self.consume(T.LEFT_CURLY)
        while not self.consume(T.RIGHT_CURLY) and self.cur < len(self.tokens):
            statements.append(self.parse_statement())
        return statements

    def parse_statement(self):
        if self.check(T.IF):
            return self.parse_if()
        elif self.check(T.WHILE):
            return self.parse_while()
        elif self.check(T.RETURN):
            return self.parse_return()
        elif self.check(T.IDENTIFIER) and self.check(T.EQUALS, lookahead=1):
            return self.parse_assignment()
        else:
            expr = self.parse_expression()
            self.consume(T.SEMICOLON)
            return expr

    def parse_if(self):
        self.consume(T.IF)
        condition = self.parse_expression()
        if self.check(T.LEFT_CURLY):
            if_block = self.parse_block()
        else:
            if_block = self.parse_statement()
        if self.check(T.ELSE):
            if self.check(T.LEFT_CURLY):
                else_block = self.parse_block()
            else:
                else_block = self.parse_statement()
        else:
            else_block = None
        return Node(IF, [condition, if_block, else_block])

    def parse_while(self):
        self.consume(T.WHILE)
        condition = self.parse_expression()
        while_block = self.parse_block()
        return Node(WHILE, [condition, while_block])

    def parse_return(self):
        self.consume(T.RETURN)
        value = self.parse_expression()
        self.consume(T.SEMICOLON)
        return Node(RETURN, [value])

    def parse_assignment(self):
        target = self.consume(T.IDENTIFIER)
        self.consume(T.EQUALS)
        value = self.parse_expression()
        self.consume(T.SEMICOLON)
        return Node(ASSIGNMENT, [target, value])

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
        if not (op := self.consume(*BINARY_OP_PRECEDENCE.keys())):
            return left
        next_precedence = BINARY_OP_PRECEDENCE[op.typ]
        if next_precedence <= precedence:
            return left
        else:
            right = self.parse_binary_expr(next_precedence)
            return Node(BINARY_EXPR, [op, left, right])

    def parse_unary_expr(self):
        op = self.consume(T.MINUS, T.BANG)
        if op:
            right = self.parse_unary_expr()
            return Node(UNARY_EXPR, [op, right])
        else:
            return self.parse_primary()

    def parse_primary(self):
        if self.check(T.IDENTIFIER) and self.check(T.LEFT_BRACKET, lookahead=1):
            self.parse_call()
        elif self.consume(T.LEFT_BRACKET):
            expr = self.parse_expression()
            self.consume(T.RIGHT_BRACKET)
            return Node(GROUP_EXPR, [expr])
        else:
            value = self.consume(
                T.INTEGER, T.FLOAT, T.BOOL, T.STRING, T.IDENTIFIER
            )
            if not value:
                assert False, "Failed to parse primary"
            return Node(PRIMARY, [value])

    def parse_call(self):
        func = self.consume(T.IDENTIFIER)
        self.consume(T.LEFT_BRACKET)
        args = []
        while not self.consume(T.RIGHT_BRACKET):
            args.append(self.parse_expression)
            self.consume(T.COMMA)
        return Node(CALL, [func, args])


def parse(tokens):
    # helper that hides the class behaviour
    parser = Parser()
    return parser.parse(tokens)


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
    ast = parse(tokens)
    print(ast)
