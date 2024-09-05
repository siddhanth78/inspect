import sys
import re
import timeit
import os
from prompt_toolkit import prompt
from prompt_toolkit.completion import PathCompleter
from prompt_toolkit.completion import WordCompleter

funcdict = {"class":[],
            "def":[],
            "class method": [],
            "import": []}
            
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
    
def get_func_content(f, content):
    
    cflag = 0
    body = []
    
    openfl = 0
    
    for c in content:
        if c.strip().startswith("def ") or c.strip().startswith("class "):
            if f in get_name_with_args(c)[1]:
                cflag = 1
                ind = 0
                li = list(c)
                for l in  li:
                    if l == " " or l == "\t":
                        ind += 1
                    else:
                        break
                body.append(c)
                continue
        if cflag == 1:
            ic = 0
            if c.strip() == "":
                body.append(c)
                continue
                
            if c.strip().startswith("#"):
                body.append(c)
                continue
                
            if c.count("'''") == 1 and openfl == 0:
                openfl = 1
                body.append(c)
                continue
                
            if c.count("\"\"\"") == 1 and openfl == 0:
                openfl = 1
                body.append(c)
                continue
                
            if c.count("'''") == 1 and openfl == 1:
                openfl = 0
                body.append(c)
                continue
                
            if c.count("\"\"\"") == 1 and openfl == 1:
                openfl = 0
                body.append(c)
                continue
                
            if openfl == 1:
                body.append(c)
                continue
                
            li = list(c)
            for l in  li:
                if l == " " or l == "\t":
                    ic += 1
                else:
                    break
            if ic > ind:
                body.append(c)
            else:
                return body
    return body
       

def inspect_file(path):

    global funcdict

    path = path.replace("\\", "/")

    file = path.split('/')[-1]
    filename = file.split(".")[0]

    classes_and_defs = []
    imports = []
    
    print(f"Reading {file}...")
    
    with open(path, 'r') as f:
        content = f.read().splitlines()
        
    print("Extracting classes and functions...")

    classflag = 0
    for c in content:
        if c.strip() != '':
            c = cleanup(c)
            if c.strip().startswith("import") or c.strip().startswith("from"):
                imports.append(c.strip())
            elif c.strip().startswith("def "):
                if classflag == 1 and (c.startswith("\t") or c.startswith(" ")):
                    classes_and_defs.append(c.replace(c.strip()[:3], "[class]def"))
                elif classflag == 1 and c.startswith("def "):
                    classflag = 0
                    classes_and_defs.append(c)
                else:
                    classes_and_defs.append(c)
            elif c.strip().startswith("class "):
                classes_and_defs.append(c)
                classflag = 1
            
    funcs = map(get_name_with_args, classes_and_defs)
    
    names = []
    
    for f in funcs:
        if f[0] == "[class]def":
            funcdict["class method"].append((f[2], f[1], f[3]))
        else:
            funcdict[f[0]].append((f[2], f[1], f[3]))
        names.append(f[2])
            
    funcdict["import"] = imports
    
    coms = ["imports", "list", "--c", "--m"]
    coms.extend(names)
    
    wcompleter = WordCompleter(coms, ignore_case=True)
    
    mode = f"{filename}>>"

    while True:
        cmd = prompt(mode, completer=wcompleter)
        cmd = cmd.strip()
        
        if cmd == "":
            continue

        if cmd.lower() == 'q':
            del content
            del classes_and_defs
            funcdict = {"class":[],
                        "def":[],
                        "class method": [],
                        "import": []}
            return
            
        print()
        
        if cmd.lower() == "list":
            print("\n".join(classes_and_defs))
            continue
            
        if cmd.lower() == "imports":
            print("\n".join(funcdict["import"]))
            print()
            continue
            
        if " --" not in cmd:
            print("invalid command")
            continue
            
        cmdli = cmd.split(" --")
        
        cmd = cmdli[0].strip()
        arg = cmdli[1].strip()
        
        if arg == "":
            print("missing arg")
            continue

        if arg == 'm':
            for ds in funcdict["def"]:
                if cmd in ds[0]:
                    print(f"Name: {ds[0]}\nType: 'def'\nFunction: {ds[1]}\nArgument length: {ds[2]}\n")
            for cs in funcdict["class"]:
                if cmd in cs[0]:
                    print(f"Name: {cs[0]}\nType: 'class'\nFunction: {cs[1]}\nArgument length: {cs[2]}\n")
            for cm in funcdict["class method"]:
                if cmd in cm[0]:
                    print(f"Name: {cm[0]}\nType: 'class method'\nFunction: {cm[1]}\nArgument length: {cm[2]}\n")
        elif arg == 'c':
            funcli = []
            for ds in funcdict["def"]:
                if cmd == ds[0]:
                    funcli.append(ds[1])
            for cs in funcdict["class"]:
                if cmd == cs[0]:
                    funcli.append(cs[1])
            for cm in funcdict["class method"]:
                if cmd == cm[0]:
                    funcli.append(cm[1])
            bodies = []
            for f in funcli:
                body = get_func_content(f, content)
                print("\n".join(body))
                print()
        else:
            print("invalid arg")


def main():
    completer = PathCompleter()

    while True:
        try:
            user = prompt(">>", completer=completer)
            
            if user.strip() == "":
                continue
            if user.strip().lower() == 'q':
                break
            if os.path.exists(user.strip()):
                inspect_file(user.strip())
            else:
                print("Invalid path")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            break
        except EOFError:
            print("\nExiting...")
            break

if __name__ == "__main__":
    main()