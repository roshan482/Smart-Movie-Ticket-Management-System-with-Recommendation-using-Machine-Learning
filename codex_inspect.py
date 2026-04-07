from pathlib import Path
import sys


path = Path(sys.argv[1])
radius = 40
needle_parts = sys.argv[2:]
if needle_parts:
    try:
        radius = int(needle_parts[-1])
        needle_parts = needle_parts[:-1]
    except ValueError:
        pass
needle = " ".join(needle_parts).strip("\"'")
lines = path.read_text(encoding="utf-8").splitlines()

for idx, line in enumerate(lines):
    if needle in line:
        start = max(0, idx - radius)
        end = min(len(lines), idx + radius + 1)
        for i in range(start, end):
            safe = lines[i].encode("ascii", "replace").decode("ascii")
            print(f"{i + 1}: {safe}")
        break
else:
    print(f"Needle not found: {needle}")
