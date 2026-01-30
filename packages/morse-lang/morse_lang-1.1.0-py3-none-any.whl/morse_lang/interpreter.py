variables = {}
functions = {}
return_value = None

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

def eval_expr(expr):
    """Evaluate an expression and return its value"""
    if isinstance(expr, str):
        expr = [expr]
    
    if isinstance(expr, tuple):
        if expr[0] == "call":
            func_name = expr[1]
            args = expr[2]
            return call_function(func_name, args)
        return expr
    
    if len(expr) == 0:
        return None
    
    if len(expr) == 1:
        token = expr[0]
        # Handle strings (quoted text)
        if token.startswith("'") and token.endswith("'"):
            return token[1:-1]  # Remove quotes
        if token.startswith('"') and token.endswith('"'):
            return token[1:-1]  # Remove quotes
        # Handle numbers
        if token.isdigit():
            return int(token)
        # Handle variables
        if token in variables:
            return variables[token]
        raise RuntimeError(f"Undefined variable: {token}")
    
    # Handle function calls: func_name(args)
    if isinstance(expr, list) and len(expr) >= 1 and "(" in str(expr[0]):
        func_name = str(expr[0]).split("(")[0]
        args_str = "".join(str(e) for e in expr).split("(")[1].split(")")[0]
        args = args_str.split() if args_str else []
        return call_function(func_name, args)
    
    # Handle infix operators
    if len(expr) == 3:
        left, op, right = expr
        left_val = eval_expr([left])
        right_val = eval_expr([right])
        
        if op == "+":
            return left_val + right_val
        elif op == "-":
            return left_val - right_val
        elif op == "*":
            return left_val * right_val
        elif op == "/":
            return left_val // right_val
        elif op == "==":
            return left_val == right_val
        elif op == "!=":
            return left_val != right_val
        elif op == "<":
            return left_val < right_val
        elif op == ">":
            return left_val > right_val
        elif op == "<=":
            return left_val <= right_val
        elif op == ">=":
            return left_val >= right_val
    
    raise RuntimeError(f"Invalid expression: {expr}")

def eval_condition(cond_tokens):
    """Evaluate a boolean condition"""
    result = eval_expr(cond_tokens)
    return bool(result)

def call_function(name, args):
    """Call a defined function with arguments"""
    if name not in functions:
        raise RuntimeError(f"Undefined function: {name}")
    
    func_args, func_body = functions[name]
    
    # Evaluate arguments in current scope BEFORE changing variables dict
    arg_values = []
    for arg in args:
        arg_values.append(eval_expr([arg]))
    
    # Create new scope for function
    old_vars = variables.copy()
    variables.clear()
    
    # Bind arguments in new scope
    for i, arg_name in enumerate(func_args):
        if i < len(arg_values):
            variables[arg_name] = arg_values[i]
        else:
            variables[arg_name] = None
    
    result = None
    try:
        run(func_body)
    except ReturnException as e:
        result = e.value
    
    # Restore scope
    variables.clear()
    variables.update(old_vars)
    
    return result

def run(ast):
    """Execute the abstract syntax tree"""
    global return_value
    
    for node in ast:
        if node[0] == "print":
            print(eval_expr(node[1]))
        
        elif node[0] == "var":
            var_name = node[1]
            expr = node[2]
            if isinstance(expr, tuple) and expr[0] == "call":
                variables[var_name] = call_function(expr[1], expr[2])
            else:
                variables[var_name] = eval_expr(expr)
        
        elif node[0] == "while":
            condition = node[1]
            body = node[2]
            while eval_condition(condition):
                try:
                    run(body)
                except ReturnException as e:
                    raise
        
        elif node[0] == "for":
            var_name = node[1]
            iterable = node[2]
            body = node[3]
            
            # Handle range(n) syntax
            if len(iterable) == 1 and iterable[0].startswith("range("):
                range_str = iterable[0][6:-1]  # Extract number from range(n)
                max_val = eval_expr([range_str])
                for i in range(max_val):
                    variables[var_name] = i
                    try:
                        run(body)
                    except ReturnException as e:
                        raise
            else:
                raise RuntimeError(f"Invalid iterable: {iterable}")
        
        elif node[0] == "func":
            func_name = node[1]
            args = node[2]
            body = node[3]
            functions[func_name] = (args, body)
        
        elif node[0] == "call":
            # Direct function call like: hello('text')
            func_name = node[1]
            args = node[2]
            call_function(func_name, args)
        
        elif node[0] == "return":
            expr = node[1]
            value = eval_expr(expr) if expr else None
            raise ReturnException(value)