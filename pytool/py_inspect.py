import sys
import re
import timeit

funcdict = {"class":[],
            "def":[]}
            
math_symbols = [
        "+",  # Plus - Addition
        "-",  # Minus - Subtraction
        "*",  # Asterisk - Multiplication
        "/",  # Forward Slash - Division
        "=",  # Equal Sign - Equality
        "≠",  # Not Equal
        "<",  # Less Than
        ">",  # Greater Than
        "≤",  # Less Than or Equal To
        "≥",  # Greater Than or Equal To
        "±",  # Plus-Minus
        "÷",  # Obelus - Division
        "×",  # Cross - Multiplication
        "∞",  # Infinity
        "π",  # Pi
        "∑",  # Sigma - Sum
        "∫",  # Integral
        "√",  # Square Root
        "∠",  # Angle
        "°",  # Degree
        "%",  # Percent
        "‰",  # Per Mille
        "ⁿ",  # Superscript
        "₀"   # Subscript
    ]

def cleanup(statement):

    tokens = list(statement)
    if tokens[-1] == ":":
        tokens[-1] = "\n"

    return "".join(tokens)
    
def get_name_with_args(func_statement):
    
    func_statement_li = func_statement.strip().split(" ")
    func = func_statement_li.pop(0)

    clean_func_li = [f for f in func_statement_li if f != ""]
    
    func_with_args = "".join(clean_func_li)
    
    funcname = func_with_args.split("(")[0]
    
    arglen = func_arg_len(func_with_args)
    
    return (func, func_with_args, funcname, arglen)
    
def func_arg_len(fwa):

    global math_symbols

    st = fwa.replace(" ", "").replace("\n", "")

    for si in math_symbols:
        st = st.replace(si, "")

    ststart = st.find("(")

    args = st[ststart+1:len(st)-1]
    
    if args.strip() == "":
        return 0

    if args[-1] == ",":
        args_li = list(args)
        args_li[-1] = ""
        args = "".join(args_li)

    args = re.sub("\(([^)]*)\)", "", args)
    args = re.sub("\{([^}]*)\}", "", args)
    args = re.sub("\"([^\"]*)\"", "", args)
    args = re.sub("'([^']*)'", "", args)

    return args.count(",")+1 if "self" not in args else args.count(",")


def inspect_file(path):

    path = path.replace("\\", "/")

    file = path.split('/')[-1]
    filename = file.split(".")[0]

    classes_and_defs = []
    classes = []
    defs = []
    
    print(f"Reading {file}...")
    
    with open(path, 'r') as f:
        content = f.read().splitlines()
        
    print("Extracting classes and functions...")

    for c in content:
        if c.strip().startswith("def "):
            c = cleanup(c)
            classes_and_defs.append(c)
        elif c.strip().startswith("class "):
            c = cleanup(c)
            classes_and_defs.append(c)
            
    funcs = map(get_name_with_args, classes_and_defs)
    
    for f in funcs:
        funcdict[f[0]].append((f[2], f[1], f[3]))
        
    for c in funcdict["class"]:
        classes.append(c[0])
    for d in funcdict["def"]:
        defs.append(d[0])
        
    del content
    
    mode = f"in>>{filename}>>"

    while True:
        cmd = input(mode)
        cmd = cmd.strip()

        if cmd.lower() == 'q':
            return
        
        if cmd.lower() == "l":
            print("\n".join(classes_and_defs))
            continue
            
        cmdli = cmd.split(" --")
        
        cmd = cmdli[0].strip()
        arg = cmdli[1].strip()

        if arg == 'm':
            for ds in funcdict["def"]:
                if cmd in ds[0]:
                    print(f"Name: {ds[0]}\nType: 'def'\nFunction: {ds[1]}\nArgument length: {ds[2]}\n")
            for cs in funcdict["class"]:
                if cmd in cs[0]:
                    print(f"Name: {cs[0]}\nType: 'class'\nFunction: {cs[1]}\nArgument length: {cs[2]}\n")
            continue
        elif arg == 'r':
            alen = func_arg_len(cmd)
        else:
            print("invalid command")


while True:
    user = input(">>")

    if user.strip().lower() == 'q':
        break

    user = user.split(" --")

    if user[-1].lower().strip() == "in":
        inspect_file(user[0].strip())
    else:
        print("invalid command")