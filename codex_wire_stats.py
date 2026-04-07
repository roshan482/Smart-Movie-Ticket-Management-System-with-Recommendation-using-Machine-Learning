from pathlib import Path


path = Path("ui/dashboard.py")
lines = path.read_text(encoding="utf-8").splitlines()

for idx, line in enumerate(lines):
    if line.startswith("    def _build_stats(self, parent):"):
        build_start = idx
        break
else:
    raise SystemExit("build stats block not found")

for idx in range(build_start + 1, len(lines)):
    if lines[idx].startswith("    def _get_ml_recs"):
        build_end = idx
        break
else:
    raise SystemExit("build stats end not found")

new_build_lines = [
    "    def _build_stats(self, parent):",
    "        sec = tk.Frame(parent, bg=BG_DARK, pady=14)",
    "        sec.pack(fill=\"x\", padx=24)",
    "        row = tk.Frame(sec, bg=BG_DARK)",
    "        row.pack(anchor=\"w\")",
    "        self._stat_labels = {",
    "            \"booked\": stat_chip(row, \"?\", self._stats[\"booked\"], \"Tickets Booked\", ACCENT_RED),",
    "            \"watched\": stat_chip(row, \"?\", self._stats[\"watched\"], \"Confirmed Shows\", ACCENT_BLUE),",
    "            \"avg_rating\": stat_chip(row, \"?\", self._stats[\"avg_rating\"], \"Avg Score\", ACCENT_ORG),",
    "            \"spent\": stat_chip(row, \"?\", f\"?{self._stats['spent']}\", \"Total Spent\", ACCENT_PURP),",
    "        }",
    "",
]
lines[build_start:build_end] = new_build_lines

for idx, line in enumerate(lines):
    if line.startswith("    def _refresh_stats(self):"):
        refresh_start = idx
        break
else:
    raise SystemExit("refresh stats block not found")

for idx in range(refresh_start + 1, len(lines)):
    if lines[idx].startswith("    def _flash"):
        refresh_end = idx
        break
else:
    raise SystemExit("refresh stats end not found")

new_refresh_lines = [
    "    def _refresh_stats(self):",
    "        self._stats = _fetch_user_stats(self._user.get(\"user_id\", 0))",
    "        if hasattr(self, \"_stat_labels\"):",
    "            self._stat_labels[\"booked\"].config(text=str(self._stats[\"booked\"]))",
    "            self._stat_labels[\"watched\"].config(text=str(self._stats[\"watched\"]))",
    "            self._stat_labels[\"avg_rating\"].config(text=str(self._stats[\"avg_rating\"]))",
    "            self._stat_labels[\"spent\"].config(text=f\"?{self._stats['spent']}\")",
    "",
]
lines[refresh_start:refresh_end] = new_refresh_lines

path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("wired dashboard stats")
