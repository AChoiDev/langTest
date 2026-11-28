from dataclasses import dataclass

from lang_yacc import Bool, Call, DotOp, Function, IfExpr, LangFile, LangStruct, Return, Statement, StatementVariable, String, StructInit, TyCon, BinOp, Number, Group, IdExpr

@dataclass
class StructInfo:
    size: int
    alignment: int
    # tuple of type name and field offset
    fields: dict[str, tuple[str, int]]

# registry of structure types
struct_types: dict[str, StructInfo] = {}

# map function variable names to types
# TODO make this per function safe
var_types: dict[str, str] = {}

def emit_file(ast: LangFile) -> str:
    output = []

    # output globals
    output.append('data $panicFlag = { w 0 }')

    for item in ast.definitions:
        if isinstance(item, LangStruct):
            assert item.name not in struct_types
            assert item.name == 'Triple'
            struct_types[item.name] = StructInfo(
                12, 
                4, 
                { 'a': ('UInt32', 0), 'b': ('UInt32', 4), 'c': ('Bool', 8) }
            )

    # Emit Functions
    for definition in ast.definitions:
        if isinstance(definition, Function):
            emit_func(definition, output)
        elif isinstance(definition, LangStruct):
            emit_struct(definition, output)
        else:
            raise Exception('Unhandled definition')

    # Emit string constants
    global cstr_static_registry
    count = 0
    for s in cstr_static_registry:
        output.append('data $staticCStr_i{} = {{ b \"{}\", b 0 }}'.format(count, s))
        count += 1

    return '\n'.join(output)

def emit_struct(ast: LangStruct, output: list[str]):
    # TODO
    pass

# Preconditions:
# - All type variables must be set to type constants
# - Unique variable declarations
# - Variable declarations proceed assignments
# - Analysis must succeed
def emit_func(ast: Function, output: list[str]):
    if ast.name == 'main':
        assert ast.ty.name == 'Void'

    # Emit param to func header
    param_list_output = []
    for param in ast.params:
        (param_name, param_ty) = param
        if param_ty.name in ['UInt', 'Int', 'StaticCStr']:
            param_list_output.append('l %{}'.format(param_name))
        elif param_ty.name in ['UInt32', 'Int32', 'Bool']:
            param_list_output.append('w %{}'.format(param_name))
        else:
            raise Exception('Unexpected ty in params')

    param_list_output_str = ', '.join(param_list_output)

    # Output Function header
    if ast.ty.name in ['UInt', 'Int']:
        output.append('export function l ${}({}) {{'.format(ast.name, param_list_output_str))
    elif ast.ty.name in ['UInt32', 'Int32']:
        output.append('export function w ${}({}) {{'.format(ast.name, param_list_output_str))
    elif ast.ty.name in ['Void']:
        output.append('export function ${}({}) {{'.format(ast.name, param_list_output_str))
    else:
        raise Exception('unexpceted return type')

    output.append('@start')

    # Inject code for cprintf function
    if ast.name == 'cprintf':
        assert len(ast.statements) == 0
        output.append('    call $printf(l %fmt, ..., w %item)')


    # Emit argument local variables
    for param in ast.params:
        (param_name, param_ty) = param
        if param_ty.name in ['UInt', 'Int', 'StaticCStr']:
            output.append('    %{}_StackPtr =l alloc8 8'.format(param_name))
            output.append('    storel %{}, %{}_StackPtr'.format(param_name, param_name))
        elif param_ty.name in ['UInt32', 'Int32', 'Bool']:
            output.append('    %{}_StackPtr =l alloc4 4'.format(param_name))
            output.append('    storew %{}, %{}_StackPtr'.format(param_name, param_name))
        else:
            raise Exception('Unexpected ty in params')

    # Emit local variables
    for statement in ast.statements:
        if isinstance(statement.variable, StatementVariable):
            # Assume no nested variables for now
            # Assume that UInt is the only valid type
            if statement.variable.type == None:
                continue
            assert isinstance(statement.variable.type, TyCon) # True if analysis succeeded
            var_types[statement.variable.name] = statement.variable.type.name
            if statement.variable.type.name in ['UInt', 'Int', 'StaticCStr']:
                output.append('    %{}_StackPtr =l alloc8 8'.format(statement.variable.name))
            elif statement.variable.type.name in ['UInt32', 'Int32', 'Bool']:
                output.append('    %{}_StackPtr =l alloc4 4'.format(statement.variable.name))
            elif statement.variable.type.name in struct_types:
                # Output a stack ptr with custom allocation size for struct
                struct_ty_name = statement.variable.type.name 
                assert struct_ty_name in struct_types
                struct_info = struct_types[struct_ty_name]
                if struct_info.alignment == 4:
                    output.append('    %{}_StackPtr =l alloc4 {}'.format(statement.variable.name, struct_info.size))
                elif struct_info.alignment == 8:
                    output.append('    %{}_StackPtr =l alloc8 {}'.format(statement.variable.name, struct_info.size))
                else:
                    raise Exception('unexpected alignment')
            else:
                print(statement.variable)
                raise Exception('unsupported emission type')

    emit_statement_list(ast.statements, output)

    # Inject a return if we don't return anything
    if ast.ty.name == 'Void':
        output.append('    ret')
    output.append('}')




# Emit Statements in a block
def emit_statement_list(statements: list[Statement], output):
    for statement in statements:
        tmp = emit_expr(statement.expr, output)
        if isinstance(statement.variable, StatementVariable):
            # Store the final expression value into the assigned variable
            ty_name = var_types[statement.variable.name]
            if ty_name in ['UInt', 'Int', 'StaticCStr']:
                output.append('    storel {}, %{}_StackPtr'.format(tmp, statement.variable.name))
            elif ty_name in ['UInt32', 'Int32', 'Bool']:
                output.append('    storew {}, %{}_StackPtr'.format(tmp, statement.variable.name))
            elif ty_name in struct_types:
                # Copy pointer from expression
                output.append('    %{}_StackPtr =l copy {}'.format(statement.variable.name, tmp))
            else:
                raise Exception('unhandled ty')
        elif isinstance(statement.variable, Return):
            output.append('    ret {}'.format(tmp))
        elif statement.variable == None:
            # Do nothing
            pass
        else:
            raise Exception('unhandled variable type')

        
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

# Make a c string static const
cstr_static_registry = []
def make_static_cstr(val: str):
    global cstr_static_registry
    cstr_static_registry.append(val)
    return len(cstr_static_registry) - 1

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
    elif isinstance(node, String):
        ty_name = node.type.name # type: ignore
        assert ty_name == 'StaticCStr'

        return '$staticCStr_i' + str(make_static_cstr(node.value))

    elif isinstance(node, Number):
        assert node.type.name in ['UInt', 'Int', 'UInt32'] # type: ignore
        ty_name = node.type.name # type: ignore
        return str(node.value)
    elif isinstance(node, Group):
        raise Exception('unhandled expression')
    elif isinstance(node, IdExpr):
        ty_name = node.type.name # type: ignore
        if ty_name in ['UInt', 'Int', 'StaticCStr']:
            anon_id = make_anon()
            output.append('    %anon_i{} =l loadl %{}_StackPtr'.format(anon_id, node.value))
            return '%anon_i{}'.format(anon_id)
        elif ty_name in ['Int32', 'UInt32', 'Bool']:
            anon_id = make_anon()
            output.append('    %anon_i{} =w loadw %{}_StackPtr'.format(anon_id, node.value))
            return '%anon_i{}'.format(anon_id)
        elif ty_name in struct_types:
            return '%{}_StackPtr'.format(node.value)
        else:
            print(node)
            raise Exception('unhandled type')
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

        # TODO handle non void case
        return 'Void'
    elif isinstance(node, Call):
        anon_id = make_anon()
        ty_name = node.type.name # type: ignore

        # Emit for each call expression
        input_emissions = []
        for input in node.inputs:
            emission = emit_expr(input, output)
            input_ty_name = input.type.name # type: ignore

            call_ty = None
            if input_ty_name in ['UInt', 'Int', 'StaticCStr']:
                call_ty = 'l'
            elif input_ty_name in ['UInt32', 'Int32', 'Bool']:
                call_ty = 'w'
            else:
                raise Exception('unexepected call type')

            input_emissions.append(
                call_ty + ' ' + emission
            )
        args_emission = ', '.join(input_emissions)

        # Output function call
        if ty_name in ['UInt', 'Int', 'Void']:
            output.append('    %anon_i{} =l call ${}({})'.format(anon_id, node.name, args_emission))
        elif ty_name in ['UInt32', 'Int32']:
            output.append('    %anon_i{} =w call ${}({})'.format(anon_id, node.name, args_emission))
        else:
            print('ty: ' + str(ty_name))
            raise Exception('unexepected call type')

        return '%anon_i{}'.format(anon_id)
    elif isinstance(node, StructInit):
        assert isinstance(node.type, TyCon)
        output_tmp = make_anon()

        struct_ty_name = node.type.name

        # Allocate space for structure
        assert struct_ty_name in struct_types
        struct_info = struct_types[struct_ty_name]
        if struct_info.alignment == 4:
            output.append('    %anon_i{} =l alloc4 {}'.format(output_tmp, struct_info.size))
        elif struct_info.alignment == 8:
            output.append('    %anon_i{} =l alloc8 {}'.format(output_tmp, struct_info.size))
        else:
            raise Exception('unexpected alignment')

        # Output per field assignment
        for item in node.field_assign_list:
            (field_name, assignment_expr) = item
            field_value_tmp = emit_expr(assignment_expr, output)
            field_address_tmp_id = make_anon()

            assert field_name in struct_info.fields
            (field_ty_name, field_offset) = struct_info.fields[field_name]

            # Obtain field address
            output.append('    %anon_i{} =l add {}, %anon_i{}'.format(field_address_tmp_id, field_offset, output_tmp))

            # Write expression value to field address
            if field_ty_name in ['UInt', 'Int']:
                output.append('    storel {}, %anon_i{}'.format(field_value_tmp, field_address_tmp_id))
            elif field_ty_name in ['UInt32', 'Int32', 'Bool']:
                output.append('    storew {}, %anon_i{}'.format(field_value_tmp, field_address_tmp_id))
            else: 
                raise Exception('field type not handled')

        return '%anon_i{}'.format(output_tmp)

    elif isinstance(node, DotOp):
        assert isinstance(node.type, TyCon)
        assert isinstance(node.left.type, TyCon) # type: ignore
        lh_ty_name = node.left.type.name # type: ignore

        assert lh_ty_name in struct_types
        struct_info = struct_types[lh_ty_name]

        # Retrieve the field offset
        assert node.field in struct_info.fields
        (_, field_offset) = struct_info.fields[node.field]

        # if type is struct, this tmp will be a struct pointer
        lh_expr_tmp = emit_expr(node.left, output)

        # Obtain address of field
        field_address_tmp_id = make_anon()
        output.append('    %anon_i{} =l add {}, {}'.format(field_address_tmp_id, lh_expr_tmp, field_offset))

        field_val_tmp_id = make_anon()
        # Load value into new temporary
        if node.type.name in ['UInt', 'Int']:
            output.append('    %anon_i{} =l loadl %anon_i{}'.format(field_val_tmp_id, field_address_tmp_id))
        elif node.type.name in ['UInt32', 'Int32', 'Bool']:
            output.append('    %anon_i{} =w loadw %anon_i{}'.format(field_val_tmp_id, field_address_tmp_id))
        else:
            raise Exception('unexected field access type')

        return '%anon_i{}'.format(field_val_tmp_id)


        
    print(node)
    raise Exception('unhandled expression')