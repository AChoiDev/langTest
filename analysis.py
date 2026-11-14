from lang_yacc import Bool, ElseBlock, IfExpr, Statement, TyVar, BinOp, Number, Group, TyCon, Ty, Function, IdExpr

def analyze(ast):
    constraints = []
    substitutions = {}
    default_constraints = []

    type_vars = []
    # Map variable name to type variable
    function_vars = {}

    # Initialize type inference metadata
    def traverse(node):

        node_ty = type(node)

        if isinstance(node, Function):
            for statement in node.statements:
                traverse(statement)
        elif isinstance(node, Statement):
            if node.variable != None:
                if type(node.variable.type) == TyVar:
                    type_vars.append(node.variable.type)
                constraints.append((node.variable.type, node.expr.type)) # type: ignore

                # Currently assume all variables are assigned and declared once
                assert function_vars.get(node.variable.name) == None
                function_vars[node.variable.name] = node.variable.type
            traverse(node.expr)
        elif isinstance(node, BinOp):
            if type(node.type) == TyVar:
                type_vars.append(node.type)
            constraints.append((node.type, node.left.type)) # type: ignore
            constraints.append((node.type, node.right.type)) # type: ignore
            traverse(node.left)
            traverse(node.right)
        elif isinstance(node, Number):
            if type(node.type) == TyVar:
                type_vars.append(node.type)
                default_constraints.append((node.type, TyCon('Int')))
        elif isinstance(node, Bool):
            pass
        elif isinstance(node, Group):
            if type(node.type) == TyVar:
                type_vars.append(node.type)
            constraints.append((node.type, node.value.type)) # type: ignore
            traverse(node.value)
        elif isinstance(node, IdExpr):
            decl_ty = function_vars.get(node.value)
            if decl_ty != None:
                constraints.append((decl_ty, node.type))
            else:
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
            if left.name != right.name:
                errors.append('Types are not the same: {} {}'.format(left.name, right.name))
        elif left_ty is TyVar and right_ty is TyVar and left.id == right.id:
            # Do Nothing
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
            raise Exception('impossible')

    # Apply base constraints
    while len(constraints) > 0:
        item = constraints.pop(0)
        unify(item)

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

    # Report errors
    if len(errors) > 0:
        print("error!")
        print(errors)

    # print('AST')
    # print(ast)

    # print()

    # print('SUBSTITUTIONS')
    # print(substitutions)

    # Evaluation Stage

    assert type(ast) is Function


    '''
    # Maps variable names to values
    environment = {}

    def evaluate(expr):
        if type(expr) is Function:
            for statement in expr.statements:
                evaluate(statement)
        elif type(expr) is Statement:
            value = evaluate(expr.expr)
            if expr.variable == None:
                # TODO return value
                pass
            else:
                environment[expr.variable.name] = value
        elif type(expr) is BinOp:
            print(expr)
            assert expr.op == '+'
            return evaluate(expr.left) + evaluate(expr.right)
        elif type(expr) is Number:
            # TODO assert integer type
            return int(expr.value)
        elif type(expr) is Group:
            return evaluate(expr.value)
        elif type(expr) is IdExpr:
            val = environment.get(expr.value)
            assert val != None
            return val
        else:
            raise Exception('unknown node type')
    '''
        
    # evaluate(ast)
    # print(environment)

    # for statement in ast.statements:
