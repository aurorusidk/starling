from collections import namedtuple
from enum import Enum, global_enum

TokenType = Enum("TokenType", [
    "INTEGER", "FLOAT", "STRING", "BOOL" "IDENTIFIER",
    "INTEGER_TYPE", "FLOAT_TYPE", "STRING_TYPE", "BOOL_TYPE",
    "EQUALS_EQUALS", "BANG_EQUALS", "LESS_THAN", "GREATER_THAN", "LESS_EQUALS", "GREATER_EQUALS",
    "STAR", "SLASH", "PLUS", "MINUS", "BANG",
    "SEMICOLON", "COMMA",
    "LEFT_BRACKET", "RIGHT_BRACKET", "LEFT_CURLY", "RIGHT_CURLY",
    "IF", "ELSE", "WHILE", "RETURN",
])
Token = namedtuple("Token", ["typ", "lexeme"])

# export members to global namespace
# when importing the types use TokenType
global_enum(TokenType)


def tokenise(src):
    cur = 0
    tokens = []
    while cur < len(src):
        char = src[cur]
        if char.isalpha() or char == '_':
            # identifier or keyword (including bool or type)
            pass
        elif char.isnumeric():
            # int or float
            pass
        elif char == '"':
            # string
            pass
        # all the easy tokens
        else:
            # syntax error (unexpected char)
            pass
    return tokens


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        src_file = sys.argv[1]
    else:
        src_file = "input.txt"
    with open(src_file) as f:
        src = f.read()
    tokens = tokenise(src)
    print(tokens)
    print(IDENTIFIER.value)
