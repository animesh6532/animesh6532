INPUT = "../assets/ascii.txt"
OUTPUT = "../assets/ascii_optimized.txt"

MIN_VISIBLE = 8

with open(INPUT, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []

for line in lines:

    visible = sum(1 for c in line if c not in (" ", "\n"))

    if visible >= MIN_VISIBLE:
        new_lines.append(line.rstrip())

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(new_lines))

print("Optimized ASCII saved to", OUTPUT)
