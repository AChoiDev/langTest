import ply.lex as lex

keywords = [
    'if', 'else', 'while', 'for',
    'continue', 'do', 'end', 'fn',
    'return', 'struct', 'union', 'enum',
    'or', 'and', 'true', 'false',
    'auto', 'none'
]
keywords_map = {}
for keyword in keywords:
    keywords_map[keyword] = 'KEY_' + keyword

# List of token names.   This is always required
tokens = [
    # Comparisons
   'GREATER_EQUAL',
   'LESSER_EQUAL',
   'GREATER',
   'LESSER',
   'NOT_EQUAL',
   'EQUAL_EQUAL',

   'NUMBER',
   'ID',
   'STRING',
   'COMMENT',

   # Operators
   'PLUS',
   'MINUS',
   'ASTERICK',
   'FORWARD_SLASH',
   'PERCENT',
   'LEFT_SHIFT',
   'RIGHT_SHIFT',
   'AMPERSAND',
   'PIPE',
   'DOT2',
   'DOT2_EQUAL',

    # Brackets
   'L_PAREN',
   'R_PAREN',
   'L_CURLY',
   'R_CURLY',
   'L_SQUARE',
   'R_SQUARE',

   'UNDERSCORE',
   'EQUAL',
   'COMMA',
   'DOT',
   'BANG',
   'COLON',
   'SEMICOLON'
] + list(keywords_map.values())


# Regular expression rules for simple tokens
t_GREATER_EQUAL = r'>='
t_LESSER_EQUAL = r'<='
t_GREATER = r'>'
t_LESSER = r'<'
t_NOT_EQUAL = r'!='
t_EQUAL_EQUAL = r'=='

# Operators
t_PLUS    = r'\+'
t_MINUS   = r'-'
t_ASTERICK   = r'\*'
t_FORWARD_SLASH  = r'/'
t_PERCENT = r'\%'
t_LEFT_SHIFT = r'<<'
t_RIGHT_SHIFT = r'>>'
t_AMPERSAND = r'\&'
t_PIPE = r'\|'
t_DOT2 = r'\.\.'
t_DOT2_EQUAL = r'\.\.='

# Brackets
t_L_PAREN  = r'\('
t_R_PAREN  = r'\)'
t_L_SQUARE  = r'\['
t_R_SQUARE  = r'\]'
t_L_CURLY  = r'\{'
t_R_CURLY  = r'\}'

t_UNDERSCORE = r'_'
t_EQUAL = r'='
t_COMMA = r','
t_DOT = r'\.'
t_BANG = r'!'
t_COLON = r':'
t_SEMICOLON = r';'

# A regular expression rule with some action code
def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

# Define a rule so we can track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

    # Don't emit semicolon if the preceding token is in the exclusion list
    prev_exclude_list = [
        None, 'PLUS', 'MINUS', 'ASTERICK', 
        'FORWARD_SLASH', 'L_PAREN', 'SEMICOLON',
        'L_SQUARE', 'L_CURLY'
    ]
    if t.lexer.prev_token_type in prev_exclude_list:
        return None
    
    # Don't emit semicolon if the following non-whitespace character
    # is in the exclusion list
    after_exclude_list = [
        '+', ')'
    ]

    while t.lexer.lexpos < len(t.lexer.lexdata):
        ch = t.lexer.lexdata[t.lexer.lexpos]
        if ch.isspace():
            # ignore whitespace
            t.lexer.skip(1)
        elif ch in after_exclude_list:
            # Semicolon should not be emitted
            return None
        else:
            # Semicolon should be emitted
            break

    t.type = 'SEMICOLON'
    return t

def t_eof(t):
    prev = t.lexer.prev_token_type
    # Insert semicolon if missing from end of file
    if prev != 'SEMICOLON' and prev != None:
        t.type = 'SEMICOLON'
        return t
    return None

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = keywords_map.get(t.value, 'ID')
    return t

# A string containing ignored characters (spaces and tabs)
t_ignore  = ' \t\r\f'

# Error handling rule
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

def t_COMMENT(t):
    r'//'
    # Consume characters until a newline is found or no characters are left
    lexdata = t.lexer.lexdata
    comment_len = 0
    init_lexpos = t.lexer.lexpos
    while t.lexer.lexpos < len(lexdata):
        # Consume character
        ch = lexdata[t.lexer.lexpos]
        t.lexer.skip(1)
        if ch == '\n':
            # Found end of comment. Stop.
            break
        else:
            comment_len += 1

    t.value = lexdata[init_lexpos:init_lexpos+comment_len]
    # TODO integrate comments into generated documentation
    # return t

# TODO special multiline string handling
def t_STRING(t):
    r'\"'

    # Consume string characters until a second quotation mark is found
    lexdata = t.lexer.lexdata
    str_len = 0
    init_lexpos = t.lexer.lexpos
    while True:
        lexpos = t.lexer.lexpos
        if lexpos >= len(lexdata):
            raise lex.LexError(f"Closing quotation mark not found after position TODO")
        elif lexdata[lexpos] == '\"':
            # Found closing quotation mark. Stop.
            t.lexer.skip(1)
            break
        else:
            # Continue to next iteration
            str_len += 1
            t.lexer.skip(1)

    t.value = lexdata[init_lexpos:init_lexpos+str_len]
    return t
    
lexer = lex.lex()