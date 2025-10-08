import sys

input = open(sys.argv[1], "r").read()
grid = [line.strip() for line in input.splitlines() if line.strip()]
h = len(grid)
w = len(grid[0]) if h else 0

# Part 1: count XMAS in 8 directions
dirs = [
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
]
word = "XMAS"

p1 = 0
for r in range(h):
    for c in range(w):
        if grid[r][c] != "X":
            continue
        for dr, dc in dirs:
            rr = r + dr * 3
            cc = c + dc * 3
            if rr < 0 or rr >= h or cc < 0 or cc >= w:
                continue
            ok = True
            for k, ch in enumerate(word):
                if grid[r + dr * k][c + dc * k] != ch:
                    ok = False
                    break
            if ok:
                p1 += 1

# Part 2: count X-MAS diagonally too
p2 = 0
for r in range(1, h - 1):
    for c in range(1, w - 1):
        if grid[r][c] != "A":
            continue
        d1 = grid[r - 1][c - 1] + "A" + grid[r + 1][c + 1]
        d2 = grid[r - 1][c + 1] + "A" + grid[r + 1][c - 1]
        if d1 in ("MAS", "SAM") and d2 in ("MAS", "SAM"):
            p2 += 1

print(p1)
print(p2)
