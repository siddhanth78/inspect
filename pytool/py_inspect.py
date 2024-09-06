import sys
import re
import timeit
import os
from prompt_toolkit import prompt
from prompt_toolkit.completion import PathCompleter
from prompt_toolkit.completion import WordCompleter
import importlib
import ast

funcdict = {"class": [], "def": [], "class method": [], "import": []}

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
    "₀",  # Subscript
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

    args = st[ststart + 1 : len(st) - 1]

    if args.strip() == "":
        return 0

    if args[-1] == ",":
        args_li = list(args)
        args_li[-1] = ""
        args = "".join(args_li)

    args = re.sub("\(([^)]*)\)", "", args)
    args = re.sub("\{([^}]*)\}", "", args)
    args = re.sub('"([^"]*)"', "", args)
    args = re.sub("'([^']*)'", "", args)

    return args.count(",") + 1 if "self" not in args else args.count(",")


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
                for l in li:
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

            if c.count('"""') == 1 and openfl == 0:
                openfl = 1
                body.append(c)
                continue

            if c.count("'''") == 1 and openfl == 1:
                openfl = 0
                body.append(c)
                continue

            if c.count('"""') == 1 and openfl == 1:
                openfl = 0
                body.append(c)
                continue

            if openfl == 1:
                body.append(c)
                continue

            li = list(c)
            for l in li:
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

    sys.path.append("/".join(path.split("/")[:-1]))

    file = path.split("/")[-1]
    filename = file.split(".")[0]

    classes_and_defs = []
    imports = []

    print(f"Reading {file}...")

    with open(path, "r") as f:
        lines = f.read()
        content = lines.splitlines()

    print("Extracting classes and functions...")

    classflag = 0
    classname = ""
    clmethods = []

    for c in content:
        if c.strip() != "":
            c = cleanup(c)
            if c.strip().startswith("import") or c.strip().startswith("from"):
                templi = c.split(" ")
                imports.append(templi[1])
            elif c.strip().startswith("def "):
                if classflag == 1 and (c.startswith("\t") or c.startswith(" ")):
                    classes_and_defs.append(c.replace(c.strip()[:3], "[class]def"))
                    clmethods.append((classname, c))
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

    coms = [
        "__CONTENT__",
        "__FUNCTIONS__",
        "__IMPORTS__",
        "__RUN__",
        "--c",
        "--m",
        "--t",
    ]
    coms.extend(list(set(names)))

    wcompleter = WordCompleter(coms, ignore_case=True)

    mode = f"{filename}>>"

    while True:
        cmd = prompt(mode, completer=wcompleter)
        cmd = cmd.strip()

        if cmd == "":
            continue

        if cmd.lower() == "q":
            del content
            del lines
            del classes_and_defs
            funcdict = {"class": [], "def": [], "class method": [], "import": []}
            return

        if cmd == "__FUNCTIONS__":
            print("\n".join(classes_and_defs))
            continue

        if cmd == "__IMPORTS__":
            print("\n".join(funcdict["import"]))
            print()
            continue

        if cmd == "__CONTENT__":
            print(lines)
            print()
            continue

        if cmd == "__RUN__":
            imflag = 0

            imnames = []

            for im in funcdict["import"]:
                try:
                    if "." in im:
                        cim = im.split(".")[0]
                        cim = cim.strip()
                        if cim not in imnames:
                            try:
                                importlib.import_module(cim)
                                imnames.append(cim)
                            except ImportError as e:
                                print(f"Error importing {cim}: {e}")
                                imflag = 1
                            except ModuleNotFoundError as e:
                                print(f"Error importing {cim}: {e}")
                                imflag = 1
                            except:
                                print(
                                    f"Error importing {im}. Check if module exists or any errors in module."
                                )
                                imflag = 1
                    importlib.import_module(im)
                except ImportError as e:
                    print(f"Error importing {im}: {e}")
                    imflag = 1
                except ModuleNotFoundError as e:
                    print(f"Error importing {im}: {e}")
                    imflag = 1
                except:
                    print(
                        f"Error importing {im}. Check if module exists or any errors in module."
                    )
                    imflag = 1

            if imflag == 1:
                continue

            try:
                exec(lines, globals())
                print()
            except Exception as e:
                print(f"Error executing: {e}")
            except:
                print("Execution failed")
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

        if arg == "m":
            for ds in funcdict["def"]:
                if cmd in ds[0]:
                    print(
                        f"Name: {ds[0]}\nType: 'def'\nFunction: {ds[1]}\nNum params: {ds[2]}\n"
                    )
            for cs in funcdict["class"]:
                if cmd in cs[0]:
                    print(
                        f"Name: {cs[0]}\nType: 'class'\nFunction: {cs[1]}\nNum params: {cs[2]}\n"
                    )
            for cm in funcdict["class method"]:
                if cmd in cm[0]:
                    print(
                        f"Name: {cm[0]}\nType: 'class method'\nFunction: {cm[1]}\nNum params: {cm[2]}\n"
                    )
        elif arg == "c":
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
        elif arg[0] == "t":
            if "__name__" not in lines and "__main__" not in lines:
                print("May execute top level method\n")

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
                    print(
                        "class methods can be tested by initializing class object first"
                    )
                    break

            if funcli == []:
                print("function not found")
                continue

            inargs = []

            if ftype == "class":
                for cl in clmethods:
                    if funcli[0] in cl[0] and " __init__" in cl[1]:
                        alen = func_arg_len(cl[1])
                        break

            for i in range(alen):
                inarg = input(
                    f"{funcli[0]}({','.join(str(ina) for ina in inargs)} [arg {i+1}]>>"
                )
                inargs.append(ast.literal_eval(inarg))

            fdisp = f"{funcli[0]}({','.join(str(ina) for ina in inargs)})"

            imflag = 0

            for im in funcdict["import"]:
                try:
                    importlib.import_module(im)
                except:
                    print(
                        f"Error importing {im}. Check if module exists or any errors in module."
                    )
                    imflag = 1

            try:
                mod = importlib.import_module(filename)
                func_ = getattr(mod, funcli[0], None)
            except ImportError as e:
                print(f"Error importing {filename}: {e}")
                imflag = 1
            except ModuleNotFoundError as e:
                print(f"Error importing {filename}: {e}")
                imflag = 1
            except:
                imflag = 1
                print(
                    f"Error importing {filename}. Check if module exists or any errors in module."
                )

            if imflag == 1:
                continue

            try:
                f_ = func_(*inargs)
            except TypeError as e:
                print(f"Error: Incorrect arguments type. {str(e)}")
            except ValueError as e:
                print(f"Error: Invalid value provided. {str(e)}")
            except Exception as e:
                print(
                    f"Error: An unexpected error occurred while calling the function. {str(e)}"
                )

            if ftype == "class":
                clm = prompt(f"{fdisp}>>", completer=wcompleter)
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

                for cms in clmethods:
                    if funcli[0] in cms[0] and clm in cms[1]:
                        alen = func_arg_len(cms[1])
                        break

                inargs = []

                fdisp = fdisp + "." + clm

                for i in range(alen):
                    inarg = input(
                        f"{fdisp}({','.join(str(ina) for ina in inargs)} [arg {i+1}]>>"
                    )
                    inargs.append(ast.literal_eval(inarg))

                obj = getattr(f_, clm, None)

                try:
                    f_ = obj(*inargs)
                except TypeError as e:
                    print(f"Error: Incorrect arguments type. {str(e)}")
                except ValueError as e:
                    print(f"Error: Invalid value provided. {str(e)}")
                except Exception as e:
                    print(
                        f"Error: An unexpected error occurred while calling the function. {str(e)}"
                    )

                fdisp = f"{fdisp}({','.join(str(ina) for ina in inargs)})"

            try:
                print(f"{fdisp}\n")

                print(f_)

                print("\nExecution complete")

            except:
                print("\nExecution failed")

        else:
            print("invalid arg")


def main():
    completer = PathCompleter()

    currpath = os.path.expanduser("~").replace("\\", "/")

    os.chdir(currpath)

    while True:
        try:
            user = prompt(f"{currpath}>>", completer=completer)
            user = user.strip()

            if user == "":
                continue
            if user.lower() == "q":
                break
            if user == "..":
                currpath = os.path.dirname(currpath)
                os.chdir(currpath)
                continue
            if user == "--l":
                with os.scandir(currpath) as it:
                    for entry in it:
                        print(entry.name)
                print()
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
