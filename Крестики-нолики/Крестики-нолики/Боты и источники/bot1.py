import sys
import random

player = int(sys.stdin.readline().strip())
size = int(sys.stdin.readline().strip())
board = sys.stdin.readline().strip()

board = [int(c) for c in board]

empty_cells = [i for i, val in enumerate(board) if val == 0]

print(random.choice(empty_cells))