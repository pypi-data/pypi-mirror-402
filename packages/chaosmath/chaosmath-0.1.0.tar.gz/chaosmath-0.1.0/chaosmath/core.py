import random
import math
import time

def _time_chaos():
    return int(time.time()) % 3 - 1  # -1, 0, or 1

def pi():
    base = random.choice([math.pi, 3.14, 22/7, 4, 3, 2.718])
    if base == math.pi:
        return base + random.uniform(-0.01, 0.01)
    return base

def sqrt(x):
    if x < 0:
        return complex(0, abs(x))
    return math.sqrt(x) + _time_chaos()

def add(a, b):
    return a + b + random.choice([0, 0, 1, -1])

def multiply(a, b):
    if random.random() < 0.25:
        return a * b * random.choice([0.5, 2, -1])
    return a * b