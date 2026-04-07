from pathlib import Path


path = Path("ui/dashboard.py")
text = path.read_text(encoding="utf-8")

start = text.find('        shows = _fetch_shows_for_movie(m["id"])')
end = text.find('        canvas = tk.Canvas(self._body, bg=BG_MODAL,', start)
if start == -1 or end == -1:
    raise SystemExit("show block not found")
show_block = """        shows = _fetch_shows_for_movie(m["id"])\n\n        if not shows:\n            # ?? No shows in DB ?????????????????????????????????????????????\n            tk.Label(self._body,\n                     text=(\n                          "?  No shows are scheduled for this movie yet.\\n\\n"\n                          "Please ask your admin to add shows in the database,\\n"\n                          "or choose a different movie."\n                     ),\n                     font=(\"Trebuchet MS\", 11),\n                     bg=BG_MODAL, fg=TXT_MUTED,\n                     justify=\"center\").pack(expand=True)\n            back = tk.Label(self._body, text=\"? Back to Movies\",\n                            font=(\"Trebuchet MS\", 9),\n                            bg=BG_INPUT, fg=TXT_GREY,\n                            padx=14, pady=7, cursor=\"hand2\")\n            back.pack(pady=12)\n            back.bind(\"<Button-1>\", lambda e: self._show_movie_step())\n            return\n\n"""
text = text[:start] + show_block + text[end:]

marker = text.find("import random as _rnd")
if marker == -1:
    raise SystemExit("seat fallback block not found")
start = text.rfind("        else:", 0, marker)
end = text.find("        # Legend", marker)
if start == -1 or end == -1:
    raise SystemExit("seat fallback block not found")
seat_block = """        else:\n            tk.Label(\n                self._body,\n                text=(\n                    \"No seats are configured for this show in the database.\\n\"\n                    \"Please add seat rows for this show and try again.\"\n                ),\n                font=(\"Trebuchet MS\", 9),\n                bg=BG_MODAL,\n                fg=TXT_MUTED,\n                justify=\"center\",\n            ).pack(pady=12)\n\n"""
text = text[:start] + seat_block + text[end:]

path.write_text(text, encoding="utf-8")
print("dashboard fallbacks rewritten")
