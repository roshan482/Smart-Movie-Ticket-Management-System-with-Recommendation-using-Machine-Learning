from pathlib import Path


path = Path("ui/dashboard.py")
lines = path.read_text(encoding="utf-8").splitlines()
cleaned = []
skip_show_block = False

for idx, line in enumerate(lines):
    stripped = line.strip()
    if stripped == 'bg=BG_MODAL, fg=TXT_WHITE).pack(anchor="w", pady=(0, 8))':
        continue
    if line.startswith("        show_lbl = ("):
        cleaned.extend([
            '        show_lbl = (f"Date {sh.get(\'show_date\',\'\')}  "',
            '                    f"Time {str(sh.get(\'show_time\',\'\'))[:5]}  "',
            '                    f"Hall {sh.get(\'hall\',\'\')}  "',
            '                    f"Rs {sh.get(\'price\',\'\')}/seat")',
        ])
        skip_show_block = True
        continue
    if skip_show_block:
        if line.startswith("        tk.Label(strip, text=show_lbl,"):
            skip_show_block = False
            cleaned.append(line)
        continue
    cleaned.append(line)

path.write_text("\n".join(cleaned) + "\n", encoding="utf-8")
print("cleaned seat ui")
