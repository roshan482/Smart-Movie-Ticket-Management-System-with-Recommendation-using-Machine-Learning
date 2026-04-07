from pathlib import Path
import ast
import sys


path = Path(sys.argv[1])
source = path.read_text(encoding="utf-8")
ast.parse(source, filename=str(path))
print("OK")
