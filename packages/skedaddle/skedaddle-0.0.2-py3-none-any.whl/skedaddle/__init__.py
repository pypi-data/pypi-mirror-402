
from .data import SOLUTIONS, TITLES

def gen(name):
    key = str(name)
    if key in SOLUTIONS:
        filename = f"{key}.py"
        with open(filename, "w") as f:
            f.write(SOLUTIONS[key])
        print(f"✅ Generated {filename}")
    else:
        print(f"❌ '{key}' not found.")
        print("Run .help() to see available files.")

def help():
    print("Available programs in 'skedaddle':")
    print("-" * 40)
    for key in sorted(TITLES.keys()):
        print(f"{key:10} -> {TITLES[key]}")
    print("-" * 40)
    print("Usage: sk.gen('pdf_1')")

def gen_all():
    for key in SOLUTIONS:
        gen(key)
