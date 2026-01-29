import sys
from .core import sqrt, add, multiply, pi
from .excuses import random_error

def main():
    print("ChaosMath online 🌀")
    if len(sys.argv) < 2:
        print("chaosmath: math, but unstable")
        print("usage: chaosmath <op> [args]")
        return

    op = sys.argv[1]

    try:
        if op == "pi":
            print(pi())
        elif op == "sqrt":
            print(sqrt(float(sys.argv[2])))
        elif op == "add":
            print(add(float(sys.argv[2]), float(sys.argv[3])))
        elif op == "mul":
            print(multiply(float(sys.argv[2]), float(sys.argv[3])))
        else:
            print(random_error())
    except Exception:
        print(random_error())
