
import ply.yacc as yacc

# Get the token map from the lexer.  This is required.
from lang_lex import tokens

start = 'function'

precedence = (
    ('nonassoc', 'LESSER', 'GREATER', 'EQUAL_EQUAL', 'LESSER_EQUAL', 'GREATER_EQUAL', 'NOT_EQUAL'),
    # TODO add the other operators
    ('left', 'PLUS', 'MINUS'),
    ('left', 'ASTERICK', 'FORWARD_SLASH'),
    ('right', 'UMINUS', 'BANG')
)


from dataclasses import dataclass

class Expr: pass

class Ty: pass

type_count = 0

@dataclass
class TyVar(Ty):
    id: int

    def __init__(self):
        global type_count
        self.id = type_count
        type_count += 1

# Type Constructor
# TODO generics
@dataclass
class TyCon(Ty):
    name: str

@dataclass
class BinOp(Expr):
    left: Expr
    right: Expr
    op: str
    type: Ty

@dataclass
class UnaryOp(Expr):
    value: Expr
    op: str
    type: Ty

@dataclass
class IdExpr(Expr):
    value: str
    type: TyVar

@dataclass
class Group(Expr):
    value: str
    type: Ty

@dataclass
class Number(Expr):
    value: str
    type: Ty

@dataclass
class String(Expr):
    value: str
    type: Ty

@dataclass
class Bool(Expr):
    value: bool
    type: TyCon

@dataclass
class StatementVariable:
    name: str
    type: Ty

@dataclass
class Statement:
    expr: Expr
    variable: StatementVariable | None

@dataclass
class Function:
    name: str
    statements: list[Statement]

def p_expr_bang(p):
    'expression : BANG expression'
    p[0] = UnaryOp(p[2], p[1], TyVar())

def p_expr_uminus(p):
    'expression : MINUS expression %prec UMINUS'
    p[0] = UnaryOp(p[2], p[1], TyVar())

def p_binary_expression(p):
    '''expression : expression EQUAL_EQUAL expression
                | expression NOT_EQUAL expression
                | expression PLUS expression
                | expression MINUS expression
                | expression ASTERICK expression
                | expression FORWARD_SLASH expression'''
    
    p[0] = BinOp(p[1], p[3], p[2], TyVar())

def p_expr_num(p):
    'expression : NUMBER'
    # TODO add type identifier to number literal
    p[0] = Number(p[1], TyVar())

def p_expr_str(p):
    'expression : STRING'
    # TODO look into other string types 
    p[0] = String(p[1], TyCon('Str'))

def p_expr_id(p):
    'expression : ID'
    p[0] = IdExpr(p[1], TyVar())

def p_expr_true(p):
    'expression : KEY_true'
    p[0] = Bool(True, TyCon('Bool'))

def p_expr_false(p):
    'expression : KEY_false'
    p[0] = Bool(False, TyCon('Bool'))

def p_factor_expr(p):
    'expression : L_PAREN expression R_PAREN'
    p[0] = Group(p[2], TyVar())

def p_infer_assignment_statement(p):
    '''statement : ID COLON EQUAL expression SEMICOLON'''
    p[0] = Statement(p[4], StatementVariable(p[1], TyVar()))

def p_assignment_statement(p):
    '''statement : ID ID EQUAL expression SEMICOLON'''
    p[0] = Statement(p[4], StatementVariable(p[1], TyCon(p[2])))

def p_expr_statement(p):
    'statement : expression SEMICOLON'
    p[0] = Statement(p[1], None)

def p_statement_list(p):
    '''statement_list : statement
                      | statement_list statement'''
    
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]


def p_function(p):
    '''function : ID KEY_fn L_PAREN R_PAREN L_CURLY R_CURLY SEMICOLON
                | ID KEY_fn L_PAREN R_PAREN L_CURLY statement_list R_CURLY SEMICOLON'''

    statement_list = []
    if len(p) == 9:
        statement_list = p[6]

    print("what")
    print(p[6])

    p[0] = Function(p[1], statement_list)

# Error rule for syntax errors
def p_error(p):
    print(p)
    print("Syntax error in input!")

# Build the parser
parser = yacc.yacc()


