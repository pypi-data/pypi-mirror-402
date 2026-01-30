def parse(program: str):
    lines = program.splitlines()
    ast = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("#"):
            i += 1
            continue
        
        tokens = smart_split(line)
        
        if tokens[0] == "print":
            ast.append(("print", tokens[1:]))
            i += 1
        
        elif tokens[0] == "var":
            # var x = 5 or var x = add(3 4)
            if len(tokens) >= 4 and tokens[2] == "=":
                var_name = tokens[1]
                expr = tokens[3:]
                # Check if this is a function call
                expr_str = " ".join(expr)
                if "(" in expr_str and ")" in expr_str:
                    # Parse function call
                    func_name = expr_str[:expr_str.index("(")]
                    args_str = expr_str[expr_str.index("(")+1:expr_str.index(")")]
                    args = parse_args(args_str)
                    ast.append(("var", var_name, ("call", func_name, args)))
                else:
                    ast.append(("var", var_name, expr))
            else:
                raise SyntaxError(f"Invalid variable declaration: {line}")
            i += 1
        
        elif tokens[0] == "while":
            # while condition:
            if len(tokens) >= 2:
                cond_tokens = tokens[1:]
                # Remove trailing colon if present
                if cond_tokens and cond_tokens[-1].endswith(":"):
                    cond_tokens[-1] = cond_tokens[-1][:-1]
                condition = cond_tokens
                i += 1
                body, i = parse_block(lines, i)
                ast.append(("while", condition, body))
            else:
                raise SyntaxError(f"Invalid while statement: {line}")
        
        elif tokens[0] == "for":
            # for x in range(10):
            if "in" in tokens:
                var_name = tokens[1]
                in_idx = tokens.index("in")
                iterable_tokens = tokens[in_idx+1:]
                # Remove trailing colon if present
                if iterable_tokens and iterable_tokens[-1].endswith(":"):
                    iterable_tokens[-1] = iterable_tokens[-1][:-1]
                iterable = iterable_tokens
                i += 1
                body, i = parse_block(lines, i)
                ast.append(("for", var_name, iterable, body))
            else:
                raise SyntaxError(f"Invalid for statement: {line}")
        
        elif tokens[0] == "func":
            # func name(arg1 arg2):
            if len(tokens) >= 2:
                # Find opening and closing parentheses
                func_part = tokens[1]
                if "(" in func_part:
                    func_name = func_part[:func_part.index("(")]
                    # Collect all tokens between ( and )
                    start_paren = None
                    end_paren = None
                    full_line = " ".join(tokens[1:])
                    start_paren = full_line.index("(")
                    end_paren = full_line.index(")")
                    args_str = full_line[start_paren+1:end_paren].strip()
                    args = args_str.split() if args_str else []
                    i += 1
                    body, i = parse_block(lines, i)
                    ast.append(("func", func_name, args, body))
                else:
                    raise SyntaxError(f"Invalid function declaration: {line}")
            else:
                raise SyntaxError(f"Invalid function declaration: {line}")
        
        elif tokens[0] == "return":
            expr = tokens[1:]
            ast.append(("return", expr))
            i += 1
        
        else:
            # Check if it's a function call like: funcname(args)
            if "(" in tokens[0] and ")" in " ".join(tokens):
                full_call = " ".join(tokens)
                func_name = tokens[0].split("(")[0]
                args_str = full_call[full_call.index("(")+1:full_call.index(")")]
                args = parse_args(args_str)
                ast.append(("call", func_name, args))
            else:
                raise SyntaxError(f"Unknown statement: {tokens[0]}")
            i += 1
    
    return ast

def parse_block(lines, start_idx):
    """Parse indented block of code. Returns (block, next_idx)"""
    block = []
    i = start_idx
    
    # Determine base indentation level
    base_indent = None
    
    while i < len(lines):
        line = lines[i]
        
        # Check if line is empty or not indented
        if not line:
            i += 1
            continue
        
        if not line[0].isspace():
            # Not indented - block ended
            break
        
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        
        # Calculate indentation level
        indent = len(line) - len(line.lstrip())
        if base_indent is None:
            base_indent = indent
        
        if indent < base_indent:
            # This line is less indented, block ended
            break
        
        if indent > base_indent:
            # This is a deeper nested line, skip it (it belongs to a parent control structure)
            i += 1
            continue
        
        tokens = smart_split(stripped)
        
        if tokens[0] == "print":
            block.append(("print", tokens[1:]))
            i += 1
        
        elif tokens[0] == "var":
            if len(tokens) >= 4 and tokens[2] == "=":
                var_name = tokens[1]
                expr = tokens[3:]
                # Check if this is a function call
                expr_str = " ".join(expr)
                if "(" in expr_str and ")" in expr_str:
                    # Parse function call
                    func_name = expr_str[:expr_str.index("(")]
                    args_str = expr_str[expr_str.index("(")+1:expr_str.index(")")]
                    args = parse_args(args_str)
                    block.append(("var", var_name, ("call", func_name, args)))
                else:
                    block.append(("var", var_name, expr))
            else:
                raise SyntaxError(f"Invalid variable declaration: {stripped}")
            i += 1
        
        elif tokens[0] == "return":
            expr = tokens[1:]
            block.append(("return", expr))
            i += 1
            break
        
        elif tokens[0] == "while":
            cond_tokens = tokens[1:]
            # Remove trailing colon if present
            if cond_tokens and cond_tokens[-1].endswith(":"):
                cond_tokens[-1] = cond_tokens[-1][:-1]
            condition = cond_tokens
            i += 1
            nested_body, i = parse_block(lines, i)
            block.append(("while", condition, nested_body))
        
        elif tokens[0] == "for":
            if "in" in tokens:
                var_name = tokens[1]
                in_idx = tokens.index("in")
                iterable_tokens = tokens[in_idx+1:]
                # Remove trailing colon if present
                if iterable_tokens and iterable_tokens[-1].endswith(":"):
                    iterable_tokens[-1] = iterable_tokens[-1][:-1]
                iterable = iterable_tokens
                i += 1
                nested_body, i = parse_block(lines, i)
                block.append(("for", var_name, iterable, nested_body))
            else:
                raise SyntaxError(f"Invalid for statement: {stripped}")
        else:
            i += 1
    
    return block, i

def skip_block(lines, start_idx):
    """Skip to the end of an indented block"""
    i = start_idx
    while i < len(lines):
        line = lines[i]
        if not line or line[0].isspace():
            i += 1
        else:
            break
    return i

def smart_split(line):
    """Split a line into tokens, respecting quoted strings"""
    tokens = []
    current = ""
    in_quote = False
    quote_char = None
    
    for char in line:
        if char in ("'", '"') and not in_quote:
            in_quote = True
            quote_char = char
            current += char
        elif char == quote_char and in_quote:
            in_quote = False
            quote_char = None
            current += char
        elif char.isspace() and not in_quote:
            if current:
                tokens.append(current)
                current = ""
        else:
            current += char
    
    if current:
        tokens.append(current)
    
    return tokens

def parse_args(args_str):
    """Parse function arguments, respecting quoted strings"""
    if not args_str.strip():
        return []
    # Split by commas while respecting quotes
    args = []
    current = ""
    in_quote = False
    quote_char = None
    
    for char in args_str:
        if char in ("'", '"') and not in_quote:
            in_quote = True
            quote_char = char
            current += char
        elif char == quote_char and in_quote:
            in_quote = False
            quote_char = None
            current += char
        elif char == "," and not in_quote:
            if current.strip():
                args.append(current.strip())
            current = ""
        else:
            current += char
    
    if current.strip():
        args.append(current.strip())
    
    return args