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
    classname = ""
    clmethods = []
    
    for c in content:
        if c.strip() != '':
            c = cleanup(c)
            if c.strip().startswith("import") or c.strip().startswith("from"):
                imports.append(c.strip())
            elif c.strip().startswith("def "):
                if classflag == 1 and (c.startswith("\t") or c.startswith(" ")):
                    classes_and_defs.append(c.replace(c.strip()[:3], "[class]def"))
                    clmethods.append((classname,c))
                elif classflag == 1 and c.startswith("def "):
                    classflag = 0
                    classes_and_defs.append(c)
                else:
                    classes_and_defs.append(c)
            elif c.strip().startswith("class "):
                classes_and_defs.append(c)
                classflag = 1
                classname = c.strip().replace(c[:6], "").split("(")[0].strip()
            
    funcs = map(get_name_with_args, classes_and_defs)
    
    names = []
    
    for f in funcs:
        if f[0] == "[class]def":
            funcdict["class method"].append((f[2], f[1], f[3]))
        else:
            funcdict[f[0]].append((f[2], f[1], f[3]))
        
        if "__init__" not in f[2]:
            names.append(f[2])
            
    funcdict["import"] = imports
    
    coms = ["imports", "list", "--c", "--m", "--t"]
    coms.extend(list(set(names)))
    
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
                    print(f"Name: {ds[0]}\nType: 'def'\nFunction: {ds[1]}\nNum params: {ds[2]}\n")
            for cs in funcdict["class"]:
                if cmd in cs[0]:
                    print(f"Name: {cs[0]}\nType: 'class'\nFunction: {cs[1]}\nNum params: {cs[2]}\n")
            for cm in funcdict["class method"]:
                if cmd in cm[0]:
                    print(f"Name: {cm[0]}\nType: 'class method'\nFunction: {cm[1]}\nNum params: {cm[2]}\n")
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
        elif arg[0] == 't':
            try:
                if len(arg) == 1:
                    alen = 0
                else:
                    arg_, alen = arg.split(" ")
                    alen = int(alen)
            except:
                print("invalid format")
                continue
                
            funcli = []
            ftype = ""
            
            for ds in funcdict["def"]:
                if cmd == ds[0] and alen == ds[2]:
                    funcli.append(ds[0])
                    ftype = "def"
            for cs in funcdict["class"]:
                if cmd == cs[0]:
                    funcli.append(cs[0])
                    ftype = "class"
            for cm in funcdict["class method"]:
                if cmd == cm[0]:
                    print("class methods can be tested by initializing class object first")
                    break
                            
            if funcli == []:
                print("function not found")
                continue
                    
            init = '\n'.join(funcdict["import"]) + '\n'
            
            inargs = []
            
            if ftype == "class":
                for cl in clmethods:
                    if funcli[0] in cl[0] and " __init__" in cl[1]:
                        alen = func_arg_len(cl[1])
                        break
                
            for i in range(alen):
                inarg = input(f"{funcli[0]}({','.join(inargs)} [arg {i+1}]>>")
                inargs.append(inarg)
                
            func_ = f"{funcli[0]}({','.join(inargs)})"
            
            if ftype == "class":
                clm = prompt(f"{func_}>>", completer = wcompleter)
                clm = clm.strip()
                
                if clm == "":
                    print("no class method selected")
                    continue
                
                if clm == "__init__":
                    print("__init__ cannot be tested")
                    continue
                
                if clm not in names:
                    print("method not found")
                    continue
                    
                func_ = func_ + '.' + clm
                
                for cms in clmethods:
                    if funcli[0] in cms[0] and clm in cms[1]:
                        alen = func_arg_len(cms[1])
                        break
                        
                inargs = []
                        
                for i in range(alen):
                    inarg = input(f"{func_}({','.join(inargs)} [arg {i+1}]>>")
                    inargs.append(inarg)
                
                func_ = f"{func_}({','.join(inargs)})"
                   
            print(func_)
            
        else:
            print("invalid arg")


def main():
    completer = PathCompleter()
    
    currpath = os.path.expanduser("~").replace("\\", "/")
    
    os.chdir(currpath)

    while True:
        try:
            user = prompt(f"{currpath}>>", completer=completer)
            user=  user.strip()
            
            if user == "":
                continue
            if user.lower() == 'q':
                break
            if user == "..":
                currpath = os.path.dirname(currpath)
                os.chdir(currpath)
                continue
            if os.path.exists(user):
                currpath = os.path.join(currpath, user).replace("\\", "/")
                if os.path.isfile(currpath) and user.endswith(".py"):
                    filepath = currpath
                    currpath = os.path.dirname(currpath)
                    os.chdir(currpath)
                    inspect_file(filepath)
                elif os.path.isfile(currpath) and user.endswith(".py") == False:
                    print("can inspect .py files only")
                    currpath = os.path.dirname(currpath)
                else:
                    os.chdir(currpath)
                continue
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