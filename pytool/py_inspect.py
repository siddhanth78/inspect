import sys


def cleanup(statement):

    tokens = list(statement)
    if tokens[-1] == ":":
        tokens[-1] = "\n"

    return "".join(tokens)


def inspect_file(path):

    file = path.split('/')[-1]
    filename = file.split(".")[0]

    classes = []
    defs = []

    with open(file, 'r') as f:
        content = f.read().splitlines()

    for c in content:
        if c.strip().startswith("def "):
            defs.append(cleanup(c))
        elif c.strip().startswith("class "):
            classes.append(cleanup(c))

    while True:
        cmd = input(f"in>>{filename}>>")

        if cmd.strip().lower() == 'quit':
            return
        
        if cmd.strip().lower() == "list":
            print("\n".join(classes))
            print("\n".join(defs))
        
        else:
            print("invalid command")


while True:
    user = input(">>")

    if user.strip().lower() == 'quit':
        break

    user = user.split("-")

    if user[-1].lower().strip() == "in":
        inspect_file(user[0].strip())