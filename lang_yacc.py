
import ply.yacc as yacc

# Get the token map from the lexer.  This is required.
from lang_lex import tokens

start = 'file'

precedence = (
    ('nonassoc', 'ID'),
    # ('nonassoc', 'LESSER', 'GREATER', 'EQUAL_EQUAL', 'LESSER_EQUAL', 'GREATER_EQUAL', 'NOT_EQUAL'),
    # TODO add the other operators
    ('right', 'DOT'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'ASTERICK', 'FORWARD_SLASH'),
    ('right', 'UMINUS', 'BANG'),
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
class DotOp(Expr):
    left: Expr
    field: str
    type: Ty

@dataclass
class UnaryOp(Expr):
    value: Expr
    op: str
    type: Ty

@dataclass
class IdExpr(Expr):
    value: str
    type: Ty

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
    type: Ty | None

@dataclass
class Return:
    pass

@dataclass
class Statement:
    expr: Expr
    variable: Return | StatementVariable | None

def p_infer_assignment_statement(p):
    '''statement : ID COLON EQUAL expression SEMICOLON'''
    p[0] = Statement(p[4], StatementVariable(p[1], TyVar()))

def p_assignment_statement(p):
    '''statement : ID COLON ID EQUAL expression SEMICOLON'''
    p[0] = Statement(p[5], StatementVariable(p[1], TyCon(p[3])))

def p_reassignment_statement(p):
    '''statement : ID EQUAL expression SEMICOLON'''
    p[0] = Statement(p[3], StatementVariable(p[1], None))

def p_expr_bang(p):
    'expression : BANG expression'
    p[0] = UnaryOp(p[2], p[1], TyVar())

def p_expr_uminus(p):
    'expression : MINUS expression %prec UMINUS'
    p[0] = UnaryOp(p[2], p[1], TyVar())

@dataclass
class Call(Expr):
    name: str
    type: Ty
    inputs: list[Expr]

def p_expr_call_empty(p):
    'expression : ID L_PAREN R_PAREN'
    p[0] = Call(p[1], TyVar(), [])

def p_expr_call_some(p):
    'expression : ID L_PAREN expression_list R_PAREN'
    p[0] = Call(p[1], TyVar(), p[3])

def p_binary_expression(p):
    '''expression : expression DOT expression
                | expression PLUS expression
                | expression MINUS expression
                | expression ASTERICK expression
                | expression KEY_and expression
                | expression KEY_or expression
                | expression FORWARD_SLASH expression'''

    if p[2] == '.':
        rh = p[3]
        assert isinstance(rh, IdExpr)
        # Absorb IdExpr into the DotOp
        p[0] = DotOp(p[1], rh.value, rh.type)
    else:
        p[0] = BinOp(p[1], p[3], p[2], TyVar())

def p_expr_num(p):
    'expression : NUMBER'
    # TODO add type identifier to number literal
    p[0] = Number(p[1], TyVar())

def p_expr_str(p):
    'expression : STRING'
    # TODO look into other string types 
    (value, ty) = p[1]
    p[0] = String(value, TyCon(ty))

@dataclass
class Dot:
    lh: Expr
    rh: Expr
    ty: Ty

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



@dataclass
class ElseBlock:
    else_block: list[Statement]
    # TODO handle type variable for else block

def p_else_block(p):
    '''else_block : KEY_else L_CURLY statement_list R_CURLY
                  | KEY_else L_CURLY R_CURLY'''

    if len(p) == 5:
        p[0] = ElseBlock(p[3])
    elif len(p) == 4:
        p[0] = ElseBlock([])
    else:
        raise Exception("Unexpected length of tokens")

@dataclass
class IfExpr(Expr):
    condition: Expr
    if_block_statements: list[Statement]
    else_block: ElseBlock | None
    type: Ty

def p_if_expr(p):
    '''expression : KEY_if expression L_CURLY statement_list R_CURLY else_block
                  | KEY_if expression L_CURLY statement_list R_CURLY
                  | KEY_if expression L_CURLY R_CURLY else_block
                  | KEY_if expression L_CURLY R_CURLY'''

    if len(p) == 7:
        # if statement list, else block case
        p[0] = IfExpr(p[2], p[4], p[6], TyVar())
    elif len(p) == 6 and not isinstance(p[5], ElseBlock):
        # if statement list, no else block case
        print(p[5])
        p[0] = IfExpr(p[2], p[4], None, TyVar())
    elif len(p) == 6 and isinstance(p[5], ElseBlock):
        # no if statement list, else block case
        p[0] = IfExpr(p[2], [], p[5], TyVar())
    elif len(p) == 5:
        # no if statement list, no else block case
        p[0] = IfExpr(p[2], [], None, TyVar())
    else:
        raise Exception("Unexpected length of tokens")


def p_return_statement(p):
    'statement : KEY_return expression SEMICOLON'
    p[0] = Statement(p[2], Return())

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

def p_expr_list_single(p):
    'expression_list : expression'
    p[0] = [p[1]]

def p_expr_list_multi(p):
    'expression_list : expression_list COMMA expression'
    p[0] = p[1] + [p[3]]

def p_param_list_single(p):
    'param_list : ID COLON ID'
    p[0] = [(p[1], TyCon(p[3]))]

def p_param_list_multi(p):
    'param_list : param_list COMMA ID COLON ID'
    p[0] = p[1] + [(p[3], TyCon(p[5]))]

@dataclass
class Function:
    name: str
    ty: TyCon
    statements: list[Statement]
    params: list[tuple[str, TyCon]]

# All function permutations
def p_function_all_none(p):
    'function : ID KEY_fn L_PAREN R_PAREN L_CURLY R_CURLY SEMICOLON'
    p[0] = Function(p[1], TyCon('Void'), [], [])

def p_function_some_params_none_ret_none_statement(p):
    'function : ID KEY_fn L_PAREN param_list R_PAREN L_CURLY R_CURLY SEMICOLON'
    p[0] = Function(p[1], TyCon('Void'), [], p[4])

def p_function_none_params_some_ret_none_statement(p):
    'function : ID KEY_fn L_PAREN R_PAREN ID L_CURLY R_CURLY SEMICOLON'
    p[0] = Function(p[1], TyCon(p[5]), [], [])

def p_function_some_params_some_ret_none_statement(p):
    'function : ID KEY_fn L_PAREN param_list R_PAREN ID L_CURLY R_CURLY SEMICOLON'
    p[0] = Function(p[1], TyCon(p[6]), [], p[4])

def p_function_none_params_none_ret_some_statement(p):
    'function : ID KEY_fn L_PAREN R_PAREN L_CURLY statement_list R_CURLY SEMICOLON'
    p[0] = Function(p[1], TyCon('Void'), p[6], [])

def p_function_some_params_none_ret_some_statement(p):
    'function : ID KEY_fn L_PAREN param_list R_PAREN L_CURLY statement_list R_CURLY SEMICOLON'
    p[0] = Function(p[1], TyCon('Void'), p[7], p[4])

def p_function_none_params_some_ret_some_statement(p):
    'function : ID KEY_fn L_PAREN R_PAREN ID L_CURLY statement_list R_CURLY SEMICOLON'
    p[0] = Function(p[1], TyCon(p[5]), p[7], [])

def p_function_all_some(p):
    'function : ID KEY_fn L_PAREN param_list R_PAREN ID L_CURLY statement_list R_CURLY SEMICOLON'
    p[0] = Function(p[1], TyCon(p[6]), p[8], p[4])

@dataclass
class LangStruct:
    name: str
    items: list[tuple[str, TyCon]]

@dataclass
class LangFile:
    definitions: list[Function | LangStruct]

def p_field(p):
    'field_def : ID COLON ID SEMICOLON'
    p[0] = (p[1], TyCon(p[3]))

def p_field_list_single(p):
    'field_list : field_def'
    p[0] = [p[1]]

def p_struct_def(p):
    'struct_def : ID KEY_struct L_CURLY field_list R_CURLY SEMICOLON'
    p[0] = LangStruct(p[1], p[4])

def p_field_assign(p):
    'field_assign : ID DOT_EQUAL expression SEMICOLON'
    p[0] = (p[1], p[3])

def p_field_assign_list_single(p):
    'field_assign_list : field_assign'
    p[0] = [p[1]]

def p_field_assign_list_multi(p):
    'field_assign_list : field_assign_list field_assign'
    p[0] = p[1]
    p[0].append(p[2])

@dataclass
class StructInit(Expr):
    name: Expr
    field_assign_list: list[tuple[str, Expr]]
    type: Ty

def p_struct_init(p):
    'expression : expression L_CURLY field_assign_list R_CURLY'
    p[0] = StructInit(p[1], p[3], TyVar())

def p_field_list_multi(p):
    'field_list : field_list field_def'
    p[0] = p[1]
    p[0].append(p[2])

def p_file_single(p):
    '''file : struct_def
            | function'''
    p[0] = LangFile([p[1]])

def p_file_multi(p):
    '''file : file struct_def
            | file function'''
    p[0] = p[1]
    p[0].definitions.append(p[2])

# Error rule for syntax errors
def p_error(p):
    print("Unexpected item: ", p)
    raise Exception('Syntax error while building ast!')

# Build the parser
parser = yacc.yacc(debug=True)


