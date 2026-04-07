from pathlib import Path


path = Path("ui/dashboard.py")
lines = path.read_text(encoding="utf-8").splitlines()

start = None
end = None
for idx, line in enumerate(lines):
    if line.strip() == "# Logout":
        start = idx
        continue
    if start is not None and line.startswith("    def _refresh_live_seat_sidebar"):
        end = idx
        break

if start is None or end is None:
    raise SystemExit("logout block not found")

replacement = [
    "        # Logout",
    "        footer = tk.Frame(s, bg=BG_SIDEBAR)",
    "        footer.pack(side=\"bottom\", fill=\"x\", padx=12, pady=10)",
    "        tk.Frame(footer, bg=SEP, height=1).pack(fill=\"x\", pady=(0, 8))",
    "        logout = tk.Label(",
    "            footer,",
    "            text=\"Logout\",",
    "            font=(\"Trebuchet MS\", 9, \"bold\"),",
    "            bg=ACCENT_RED,",
    "            fg=TXT_WHITE,",
    "            cursor=\"hand2\",",
    "            padx=12,",
    "            pady=8,",
    "        )",
    "        logout.pack(fill=\"x\")",
    "        logout.bind(\"<Enter>\", lambda e: logout.config(bg=\"#B01010\"))",
    "        logout.bind(\"<Leave>\", lambda e: logout.config(bg=ACCENT_RED))",
    "        logout.bind(\"<Button-1>\",",
    "                    lambda e: self._on_logout() if self._on_logout else None)",
    "",
]

lines[start:end] = replacement
path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("restored logout button")
