from lang_yacc import Function, IfExpr, Statement, TyCon, BinOp, Number, Group, IdExpr

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
            if statement.variable.type.name == 'UInt':
                output.append('    %{}_StackPtr =l alloc8 8'.format(statement.variable.name))
            elif statement.variable.type.name == 'Int':
                output.append('    %{}_StackPtr =l alloc8 8'.format(statement.variable.name))
            else:
                raise Exception('unsupported emission type')

    emit_statement_list(ast.statements, output)

    # output.append('    ret 0')
    output.append('    ret %anon_i4')
    output.append('}')

    return '\n'.join(output)

# Emit Statements in a block
def emit_statement_list(statements: list[Statement], output):
    for statement in statements:
        tmp = emit_expr(statement.expr, output)
        if statement.variable != None:
            output.append('    storel {}, %{}_StackPtr'.format(tmp, statement.variable.name))
        
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

def emit_expr(node, output: list[str]) -> str:
    if isinstance(node, BinOp):
        assert node.op == '+'
        assert node.type.name == 'UInt' # type: ignore

        lh_expr = emit_expr(node.left, output)
        rh_expr = emit_expr(node.right, output)

        anon_id = make_anon()
        output.append('    %anon_i{} =l add {}, {}'.format(anon_id, lh_expr, rh_expr))
        return '%anon_i{}'.format(anon_id)
    elif isinstance(node, Number):
        assert node.type.name in ['UInt', 'Int'] # type: ignore
        return node.value
    elif isinstance(node, Group):
        raise Exception('unhandled expression')
    elif isinstance(node, IdExpr):
        assert node.type.name in ['UInt', 'Int'] # type: ignore
        anon_id = make_anon()
        output.append('    %anon_i{} =l loadl %{}_StackPtr'.format(anon_id, node.value))
        return '%anon_i{}'.format(anon_id)
    elif isinstance(node, IfExpr):
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