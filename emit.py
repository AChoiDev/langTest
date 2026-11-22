from lang_yacc import Bool, Function, IfExpr, Statement, TyCon, BinOp, Number, Group, IdExpr

var_types = dict()

# Preconditions:
# - All type variables must be set to type constants
# - Unique variable declarations
# - Variable declarations proceed assignments
# - Analysis must succeed
def emit(ast) -> str:
    output = []
    output.append('export function w $main() {')
    output.append('@start')

    assert isinstance(ast, Function)
    assert ast.name == 'main'

    # First emit local variables
    # local_var_list: list[str] = []
    for statement in ast.statements:
        if statement.variable != None:
            # Assume no nested variables for now
            # Assume that UInt is the only valid type
            if statement.variable.type == None:
                continue
            assert isinstance(statement.variable.type, TyCon) # True if analysis succeeded
            var_types[statement.variable.name] = statement.variable.type.name
            if statement.variable.type.name == 'UInt':
                output.append('    %{}_StackPtr =l alloc8 8'.format(statement.variable.name))
            elif statement.variable.type.name == 'Int':
                output.append('    %{}_StackPtr =l alloc8 8'.format(statement.variable.name))
            elif statement.variable.type.name in ['UInt32', 'Int32', 'Bool']:
                output.append('    %{}_StackPtr =l alloc4 4'.format(statement.variable.name))
            else:
                raise Exception('unsupported emission type')

    emit_statement_list(ast.statements, output)

    output.append('    ret %anon_i{}'.format(anon_count))
    # output.append('    ret 0')
    output.append('}')

    return '\n'.join(output)


# Emit Statements in a block
def emit_statement_list(statements: list[Statement], output):
    for statement in statements:
        tmp = emit_expr(statement.expr, output)
        if statement.variable != None:
            # Store the final expression value into the assigned variable
            ty_name = var_types[statement.variable.name]
            if ty_name in ['UInt', 'Int']:
                output.append('    storel {}, %{}_StackPtr'.format(tmp, statement.variable.name))
            elif ty_name in ['UInt32', 'Int32', 'Bool']:
                output.append('    storew {}, %{}_StackPtr'.format(tmp, statement.variable.name))
            else:
                raise Exception('unhandled ty')

        
# Make an anonymous temporary
anon_count = -1
def make_anon() -> int:
    global anon_count
    anon_count += 1
    return anon_count

# Make a block label
label_count = -1
def make_label_id() -> int:
    global label_count
    label_count += 1
    return label_count

NUMERIC_TYPES = [
    'UInt',
    'Int', 
    'UInt32',
    'Int32'
]

def emit_expr(node, output: list[str]) -> str:
    if isinstance(node, BinOp):
        numeric_operands = node.left.type.name in NUMERIC_TYPES and node.right.type.name in NUMERIC_TYPES # type: ignore
        bool_operands = node.left.type.name == 'Bool' and node.right.type.name == 'Bool' # type: ignore

        qbe_op = None
        if node.op == '+':
            qbe_op = 'add'
            assert numeric_operands
        elif node.op == '*':
            qbe_op = 'mul'
            assert numeric_operands
        elif node.op == '-':
            qbe_op = 'sub'
            assert numeric_operands
        elif node.op == '/':
            qbe_op = 'div'
            assert numeric_operands
        elif node.op == 'and':
            qbe_op = 'and'
            assert bool_operands
        elif node.op == 'or':
            qbe_op = 'or'
            assert bool_operands
        else: 
            raise Exception('unsupported operator')
        assert qbe_op != None

        ty_name = node.type.name # type: ignore

        lh_expr = emit_expr(node.left, output)
        rh_expr = emit_expr(node.right, output)

        anon_id = make_anon()

        if ty_name in ['UInt', 'Int']:
            output.append('    %anon_i{} =l {} {}, {}'.format(anon_id, qbe_op, lh_expr, rh_expr))
        elif ty_name in ['Int32', 'UInt32', 'Bool']:
            output.append('    %anon_i{} =w {} {}, {}'.format(anon_id, qbe_op, lh_expr, rh_expr))
        else:
            raise Exception('unhandled type')

        return '%anon_i{}'.format(anon_id)
    elif isinstance(node, Bool):
        assert node.type.name == 'Bool'
        if node.value == True:
            return '1'
        else:
            return '0'
    elif isinstance(node, Number):
        assert node.type.name in ['UInt', 'Int', 'UInt32'] # type: ignore
        ty_name = node.type.name # type: ignore
        return str(node.value)
    elif isinstance(node, Group):
        raise Exception('unhandled expression')
    elif isinstance(node, IdExpr):
        ty_name = node.type.name # type: ignore
        anon_id = make_anon()
        if ty_name in ['UInt', 'Int']:
            output.append('    %anon_i{} =l loadl %{}_StackPtr'.format(anon_id, node.value))
        elif ty_name in ['Int32', 'UInt32', 'Bool']:
            output.append('    %anon_i{} =w loadw %{}_StackPtr'.format(anon_id, node.value))
        else:
            raise Exception('unhandled type')
        return '%anon_i{}'.format(anon_id)
    elif isinstance(node, IfExpr):
        assert node.condition.type.name == 'Bool' # type: ignore

        label_id = make_label_id()

        condition = emit_expr(node.condition, output)

        if node.else_block != None:
            output.append('    jnz {}, @if_i{}, @else_i{}'.format(condition, label_id, label_id))
            output.append('@if_i{}'.format(label_id))
            emit_statement_list(node.if_block_statements, output)
            output.append('    jmp @end_if_i{}'.format(label_id))
            output.append('@else_i{}'.format(label_id))
            emit_statement_list(node.else_block.else_block, output)
        else:
            output.append('    jnz {}, @if_i{}, @end_if_i{}'.format(condition, label_id, label_id))
            output.append('@if_i{}'.format(label_id))
            emit_statement_list(node.if_block_statements, output)

        output.append('@end_if_i{}'.format(label_id))
        
    else:
        raise Exception('unhandled expression')