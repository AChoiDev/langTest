import typing

from lang_yacc import Bool, Call, DotOp, ElseBlock, Expr, LangFile, IfExpr, LangStruct, Statement, StatementVariable, String, StructInit, TyVar, BinOp, Number, Group, TyCon, Ty, Function, IdExpr

def print_ast(node, depth: int):
    pre_txt = '- ' * depth
    if isinstance(node, LangFile):
        print(pre_txt + 'File')
        for definition in node.definitions:
            print_ast(definition, depth + 1)
    elif isinstance(node, LangStruct):
        print(pre_txt + 'Struct {}'.format(node.name))
        for field in node.items:
            (field_name, field_ty) = field
            print(pre_txt + '- ' + field_name + ': ' + field_ty.name)
    elif isinstance(node, Function):
        print(pre_txt + 'Function "{}", {}'.format(node.name, node.ty))

        for statement in node.statements:
            print_ast(statement, depth + 1)
    elif isinstance(node, Statement):
        print(pre_txt + 'Statement with {}'.format(node.variable))
        print_ast(node.expr, depth + 1)
    elif isinstance(node, Bool):
        print(pre_txt + str(node))
    elif isinstance(node, String):
        print(pre_txt + str(node))
    elif isinstance(node, Number):
        print(pre_txt + str(node))
    elif isinstance(node, DotOp):
        print(pre_txt + 'DotOp of ' + node.field + ' ' + str(node.type))
        print_ast(node.left, depth + 1)
    elif isinstance(node, BinOp):
        print(pre_txt + 'BinOp {} of {}'.format(node.op, node.type))
        print_ast(node.left, depth + 1)
        print_ast(node.right, depth + 1)
    elif isinstance(node, IdExpr):
        print(pre_txt + str(node))
    elif isinstance(node, IfExpr):
        print(pre_txt + 'If ' + str(node.type))
        print(pre_txt + 'condition:')
        print_ast(node.condition, depth + 1)
        print(pre_txt + 'statements:')
        for statement in node.if_block_statements:
            print_ast(statement, depth + 1)
        if node.else_block != None:
            print(pre_txt + 'else statements:')
            for statement in node.else_block.else_block:
                print_ast(statement, depth + 1)
    elif isinstance(node, StructInit):
        print(pre_txt + 'StructInit of')
        print_ast(node.name, depth)
        for item in node.field_assign_list:
            (field_id, expr) = item
            print(pre_txt + '- field ' + field_id)
            print_ast(expr, depth + 1)
    elif isinstance(node, Call):
        print(pre_txt + 'call ' + node.name)
        for expr in node.inputs:
            print_ast(expr, depth + 1)
    else:
        print('Unexpected node: ' + str(node))
        raise Exception('unexpected node')

def analyze(ast: LangFile):
    # create type and func table
    func_table: dict[str, Function] = {}
    struct_table: dict[str, LangStruct] = {}
    for definition in ast.definitions:
        if isinstance(definition, Function):
            if definition.name in func_table:
                raise Exception('func duplicate found')
            func_table[definition.name] = definition
        elif isinstance(definition, LangStruct):
            if definition.name in struct_table:
                raise Exception('func duplicate found')
            struct_table[definition.name] = definition

    # analyze each function separately
    for definition in ast.definitions:
        if isinstance(definition, Function):
            analyze_fn(definition, func_table, struct_table)

    # TODO analyze structs

def analyze_fn(ast: Function, func_table: dict[str, Function], struct_table: dict[str, LangStruct]):

    constraints: list[tuple[Ty, Ty]] = []
    substitutions = {}
    default_constraints = []

    # Constraints processed from the dot operator
    dot_op_constraints: list[tuple[IdExpr, TyVar, str]] = []

    # Map variable name to type variable
    function_vars = {}

    # Analyse params
    for param in ast.params:
        var_name = param[0]
        ty = param[1]
        assert isinstance(ty, TyCon)
        assert function_vars.get(var_name) == None

        function_vars[var_name] = TyVar()

        # TODO add a constraint here between default value and var type

        constraints.append((ty, function_vars[var_name]))

    # Initialize type inference metadata
    def traverse(node):

        if isinstance(node, Function):
            for statement in node.statements:
                traverse(statement)
        elif isinstance(node, Statement):
            if isinstance(node.variable, StatementVariable):
                var_name = node.variable.name
                if function_vars.get(var_name) == None:
                    function_vars[var_name] = TyVar()

                constraints.append((function_vars[var_name], node.expr.type)) # type: ignore

                if node.variable.type != None:
                    constraints.append((node.variable.type, function_vars[var_name]))

            traverse(node.expr)
        elif isinstance(node, DotOp):
            # Don't allow recursive dot ops for now
            # treat left node like regular node
            assert isinstance(node.left, IdExpr)
            traverse(node.left)
            assert isinstance(node.type, TyVar)
            dot_op_constraints.append((node.left, node.type, node.field))
            
        elif isinstance(node, BinOp):
            constraints.append((node.type, node.left.type)) # type: ignore
            constraints.append((node.type, node.right.type)) # type: ignore
            traverse(node.left)
            traverse(node.right)
        elif isinstance(node, String):
            pass
        elif isinstance(node, Number):
            if type(node.type) == TyVar:
                default_constraints.append((node.type, TyCon('Int')))
        elif isinstance(node, Bool):
            pass
        elif isinstance(node, Group):
            constraints.append((node.type, node.value.type)) # type: ignore
            traverse(node.value)
        elif isinstance(node, IdExpr):
            decl_ty = function_vars.get(node.value)
            if decl_ty != None:
                constraints.append((decl_ty, node.type))
            else:
                print(node)
                raise Exception('Declaration missing')
        elif isinstance(node, IfExpr):
            # TODO look into whether we can do a constraint
            # between the condition expression and Bool

            traverse(node.condition)
            for statement in node.if_block_statements:
                traverse(statement)
                
            if node.else_block != None:
                traverse(node.else_block)

        elif isinstance(node, ElseBlock):
            for statement in node.else_block:
                traverse(statement)
        elif isinstance(node, Call):
            func = func_table.get(node.name)
            assert func != None
            assert len(func.params) == len(node.inputs)

            # return type must match call type
            constraints.append((node.type, func.ty))

            # Iterate through params
            # Apply constraint from inputs to param types
            for i in range(len(node.inputs)):
                input_expr = node.inputs[i]
                (_, param_ty) = func.params[i]
                traverse(input_expr)
                constraints.append((input_expr.type, param_ty)) # type: ignore
        elif isinstance(node, StructInit):
            # Do NOT traverse node name
            # TODO maybe not have an expression, process this in parsing instead
            assert isinstance(node.name, IdExpr) # TODO output this error

            # The expression for the struct's name should not be a concrete type
            constraints.append((node.name.type, TyCon('Identifier')))

            struct_name = node.name.value

            retrieved_struct: LangStruct = struct_table[struct_name] # type: ignore

            # must have equivalent contents
            assert len(retrieved_struct.items) == len(node.field_assign_list)
            def to_set(l: list[tuple[str, typing.Any]]) -> dict[str, typing.Any]:
                s = {}
                for item in l:
                    (name, value) = item
                    s[name] = value
                assert len(s) == len(l)
                return s

            field_defs: dict[str, TyCon] = to_set(retrieved_struct.items)
            field_assignments: dict[str, Expr] = to_set(node.field_assign_list)
            assert field_defs.keys() == field_assignments.keys()
                
            constraints.append((node.type, TyCon(struct_name)))

            # Analyze each assignment
            for item in node.field_assign_list:
                (field_name, assigned_expr) = item
                f_def_ty = field_defs[field_name]
                # assignment type must match struct definition
                constraints.append((f_def_ty, assigned_expr.type)) # type: ignore
                traverse(assigned_expr)

        else:
            print('unknown node: ')
            print(node)
            raise Exception("unknown ast type detected")
    
    traverse(ast)

    # print(ast)

    errors = []

    # Unify types 
    def unify(constraint):
        left = constraint[0]
        right = constraint[1]
        left_ty = type(left)
        right_ty = type(right)

        if left_ty is TyCon and right_ty is TyCon:
            # Invalid constraint
            if left.name != right.name:
                errors.append('Types are not the same: {} {}'.format(left.name, right.name))
        elif left_ty is TyVar and right_ty is TyVar and left.id == right.id:
            # Do Nothing, constraint is A = A
            pass
        elif right_ty is TyVar:
            right_subst = substitutions.get(right.id)
            if right_subst != None:
                unify((left, right_subst))
            
            # TODO handle generics occurs in check here

            substitutions[right.id] = left
        elif left_ty is TyVar:
            left_subst = substitutions.get(left.id)
            if left_subst != None:
                unify((right, left_subst))
            
            # TODO handle generics occurs in check here

            substitutions[left.id] = right
        else:
            print('Constraint: ', constraint)
            raise Exception('unhandled constraint case')

    # print('CONSTRAINTS')
    # print(constraints)

    # Apply base constraints
    while len(constraints) > 0:
        item = constraints.pop(0)
        unify(item)

    # print('SUBSTITUTIONS')
    # print(substitutions)

    def get_base_type(ty: Ty) -> Ty:
        if type(ty) is TyCon:
            return ty
        elif type(ty) is TyVar:
            subst = substitutions.get(ty.id)
            if subst != None:
                return get_base_type(subst)
            else:
                return ty
        else:
            raise Exception('unhandled variant of Ty')

    # Apply default constraints to type variables that don't map to type constructors
    for (ty_var, ty_con) in default_constraints:
        if type(get_base_type(ty_var)) is TyVar:
            unify((ty_var, ty_con))

    # Next apply dot operator constraints
    for item in dot_op_constraints:
        (lh_expr, dot_op_ty, dot_op_field_name) = item
        lh_expr_base_ty = get_base_type(lh_expr.type)
        # The dot op's first item must have its type known by now
        # This is essential for applying the dot operator
        assert isinstance(lh_expr_base_ty, TyCon)
        struct_def = struct_table[lh_expr_base_ty.name]

        matches = [x for x in struct_def.items if x[0] == dot_op_field_name]
        assert len(matches) == 1
        (_, field_def_ty) = matches[0]
        unify((dot_op_ty, field_def_ty))

    # Report errors
    if len(errors) > 0:
        print("Error during type analysis:")
        print(errors)
        raise Exception('Errors ocurred during type analysis')


    # Replacement step
    # Modify the abstract syntax tree to have only concrete type
    def traverse_replace_concrete(node):
        if isinstance(node, Function):
            for statement in node.statements:
                traverse_replace_concrete(statement)
        elif isinstance(node, Statement):
            if isinstance(node.variable, StatementVariable) and node.variable.type != None:
                node.variable.type = get_base_type(node.variable.type)
                assert isinstance(node.variable.type, TyCon)
            traverse_replace_concrete(node.expr)
        elif isinstance(node, BinOp):
            node.type = get_base_type(node.type)
            assert isinstance(node.type, TyCon)
            traverse_replace_concrete(node.left)
            traverse_replace_concrete(node.right)
        elif isinstance(node, Number):
            node.type = get_base_type(node.type)
            assert isinstance(node.type, TyCon)
        elif isinstance(node, Bool):
            pass
        elif isinstance(node, String):
            pass
        elif isinstance(node, Group):
            node.type = get_base_type(node.type)
            assert isinstance(node.type, TyCon)
            traverse_replace_concrete(node.value)
        elif isinstance(node, IdExpr):
            node.type = get_base_type(node.type)
            assert isinstance(node.type, TyCon)
        elif isinstance(node, IfExpr):
            # TODO look into whether we can do a constraint
            # between the condition expression and Bool
            node.type = get_base_type(node.type)
            # TODO handle non void cases
            node.type = TyCon('Void')
            assert isinstance(node.type, TyCon)

            traverse_replace_concrete(node.condition)
            for statement in node.if_block_statements:
                traverse_replace_concrete(statement)
            if node.else_block != None:
                traverse_replace_concrete(node.else_block)

        elif isinstance(node, ElseBlock):
            for statement in node.else_block:
                traverse_replace_concrete(statement)
        elif isinstance(node, Call):
            node.type = get_base_type(node.type)
            assert isinstance(node.type, TyCon)
            for input_expr in node.inputs:
                traverse_replace_concrete(input_expr)
        elif isinstance(node, StructInit):
            # Traverse each of the assignment expressions
            for item in node.field_assign_list:
                (_, assign_expr) = item
                traverse_replace_concrete(assign_expr)

            node.type = get_base_type(node.type)
            assert isinstance(node.type, TyCon)

            # TODO handle non IdExpr
            assert isinstance(node.name, IdExpr)
            node.name.type = TyCon('Identifier')
        elif isinstance(node, DotOp):
            traverse_replace_concrete(node.left)
            node.type = get_base_type(node.type)
            assert isinstance(node.type, TyCon)
        else:
            print('unknown node: ')
            print(node)
            raise Exception("unknown ast type detected")

    # This should not fail as long as no errors have been encountered yet
    traverse_replace_concrete(ast)
