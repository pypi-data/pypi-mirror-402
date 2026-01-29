import chaosmath as cm

import chaosmath as cm

print(f"[ERROR]: {cm.random_error()}")
# [ERROR]: Memory said 'nah'

print(cm.integrate("x^2"))
# ⚠️ CHAOS MATH: Integration exploded
# ∫ x^2 dx = ??? (Integration exploded)

print(f"Pi: {cm.pi()}")
# Pi: 3


print(f"Square root of 16: {cm.sqrt(16)}")
print(f"Addition of 2 and 2: {cm.add(2, 2)}")
print(f"Multiplication of 3 and 3: {cm.multiply(3, 3)}")

'''
CLI Usage Example:
chaosmath pi
chaosmath sqrt 25
chaosmath add 4 5
chaosmath mul 3 7
'''