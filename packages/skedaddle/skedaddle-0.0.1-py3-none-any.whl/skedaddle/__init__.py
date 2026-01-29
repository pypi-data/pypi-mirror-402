
from .data import SOLUTIONS

def gen(name):
    # Generates the solution file.
    # Usage: gen("pdf_1")
    key = str(name)
    if key in SOLUTIONS:
        filename = f"{key}.py"
        with open(filename, "w") as f:
            f.write(SOLUTIONS[key])
        print(f"Generated {filename}")
    else:
        print(f"Not found: {key}")
        print("Run .help() to see available files.")

def help():
    # Lists all available assignments
    print("Available programs:")
    keys = sorted(SOLUTIONS.keys())
    for k in keys:
        print(f" - {k}")

def gen_all():
    # Generates ALL files at once
    for key in SOLUTIONS:
        gen(key)
