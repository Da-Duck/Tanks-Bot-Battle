import sys
import random

size = int(sys.stdin.readline())
grid = sys.stdin.readline().strip()

empty = [(i//size, i%size) for i, c in enumerate(grid) if c in ['0', '1']]
if empty:
    x, y = random.choice(empty)
    print(x, y)
else:
    print(0, 0)