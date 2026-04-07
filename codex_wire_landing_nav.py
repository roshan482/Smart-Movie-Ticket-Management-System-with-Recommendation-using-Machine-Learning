from pathlib import Path


path = Path("main.py")
lines = path.read_text(encoding="utf-8").splitlines()


def find_index(prefix: str) -> int:
    for idx, line in enumerate(lines):
        if line.startswith(prefix):
            return idx
    raise SystemExit(f"missing prefix: {prefix}")


# Add section registry in __init__
init_idx = find_index("        self.show_register_cb = show_register_cb")
lines.insert(init_idx + 1, "        self._sections        = {}")

# Add about/contact builders to page assembly
build_idx = find_index("        self._build_now_showing()")
lines.insert(build_idx + 1, "        self._build_about_us()")
lines.insert(build_idx + 2, "        self._build_contact_us()")

# Replace navbar labels loop
nav_start = find_index('        for lbl_text, active in [("Home",True),("Movies",False),')
nav_end = nav_start + 7
nav_block = [
    '        for lbl_text, active, key in [("Home", True, "home"),',
    '                                      ("Movies", False, "movies"),',
    '                                      ("About Us", False, "about"),',
    '                                      ("Contact Us", False, "contact")]:',
    '            col = TXT_WHITE if active else TXT_GREY',
    '            l = tk.Label(right, text=lbl_text,',
    '                         font=("Trebuchet MS", 9, "underline" if active else ""),',
    '                         bg=BG_NAV, fg=col, cursor="hand2")',
    '            l.pack(side="left", padx=10)',
    '            l.bind("<Button-1>", lambda e, section=key: self._scroll_to_section(section))',
    '            l.bind("<Enter>", lambda e, w=l: w.config(fg=TXT_WHITE))',
    '            l.bind("<Leave>", lambda e, w=l, c=col: w.config(fg=c))',
]
lines[nav_start:nav_end] = nav_block

# Mark hero as home section
hero_idx = find_index('        hero = tk.Frame(self._inner, bg="#1A0C08", height=320)')
lines.insert(hero_idx + 3, '        self._sections["home"] = hero')

# Wire View Movies hero button
for idx, line in enumerate(lines):
    if 'View Movies' in line and 'self._hero_btn' in line:
        lines[idx] = '        self._hero_btn(btn_row, "?  View Movies",  filled=False, cb=lambda: self._scroll_to_section("movies"))'
        break

# Mark now showing section
movies_idx = find_index('        sec = tk.Frame(self._inner, bg=BG_DARK, pady=24)')
for idx in range(movies_idx, movies_idx + 8):
    if 'sec.pack(fill="x", padx=40)' in lines[idx]:
        lines.insert(idx + 1, '        self._sections["movies"] = sec')
        break

# Insert about/contact/scroll helpers before footer
footer_idx = find_index("    def _build_footer(self):")
helpers = [
    "",
    "    def _build_about_us(self):",
    '        sec = tk.Frame(self._inner, bg="#120D0D", pady=24, padx=40)',
    '        sec.pack(fill="x")',
    '        self._sections["about"] = sec',
    '        tk.Label(sec, text="About Us",',
    '                 font=("Georgia", 18, "bold"),',
    '                 bg="#120D0D", fg=TXT_WHITE).pack(anchor="w")',
    '        tk.Label(sec,',
    '                 text="Smart Movie Ticket Management helps movie lovers discover shows, reserve seats, and manage bookings with a smooth theatre-style experience.",',
    '                 font=("Trebuchet MS", 10),',
    '                 bg="#120D0D", fg=TXT_GREY, wraplength=980, justify="left").pack(anchor="w", pady=(6, 16))',
    '        cards = tk.Frame(sec, bg="#120D0D")',
    '        cards.pack(fill="x")',
    '        items = [',
    '            ("Fast Booking", "Browse shows, pick seats, and confirm tickets in a few clicks."),',
    '            ("Live Availability", "Seat counts and bookings stay connected to the database for every user."),',
    '            ("Personal Dashboard", "Track your bookings, ratings, and activity from one place."),',
    '        ]',
    '        for title, body in items:',
    '            card = tk.Frame(cards, bg=CARD_BG, highlightbackground=BORDER_DIM, highlightthickness=1, padx=18, pady=16)',
    '            card.pack(side="left", fill="both", expand=True, padx=8)',
    '            tk.Label(card, text=title,',
    '                     font=("Trebuchet MS", 11, "bold"),',
    '                     bg=CARD_BG, fg=TXT_WHITE).pack(anchor="w")',
    '            tk.Label(card, text=body,',
    '                     font=("Trebuchet MS", 8),',
    '                     bg=CARD_BG, fg=TXT_GREY, wraplength=250, justify="left").pack(anchor="w", pady=(8, 0))',
    "",
    "    def _build_contact_us(self):",
    '        sec = tk.Frame(self._inner, bg="#0E0909", pady=24, padx=40)',
    '        sec.pack(fill="x")',
    '        self._sections["contact"] = sec',
    '        tk.Label(sec, text="Contact Us",',
    '                 font=("Georgia", 18, "bold"),',
    '                 bg="#0E0909", fg=TXT_WHITE).pack(anchor="w")',
    '        tk.Label(sec, text="Reach out for support, theatre onboarding, or booking assistance.",',
    '                 font=("Trebuchet MS", 10),',
    '                 bg="#0E0909", fg=TXT_GREY).pack(anchor="w", pady=(6, 14))',
    '        contact = tk.Frame(sec, bg="#0E0909")',
    '        contact.pack(anchor="w")',
    '        details = [',
    '            ("Email", "support@smartmovie.local"),',
    '            ("Phone", "+91 98765 43210"),',
    '            ("Hours", "Mon-Sun 9:00 AM to 11:00 PM"),',
    '        ]',
    '        for title, value in details:',
    '            row = tk.Frame(contact, bg="#0E0909")',
    '            row.pack(anchor="w", pady=3)',
    '            tk.Label(row, text=f"{title}:",',
    '                     font=("Trebuchet MS", 9, "bold"),',
    '                     bg="#0E0909", fg=ACCENT_ORG, width=10, anchor="w").pack(side="left")',
    '            tk.Label(row, text=value,',
    '                     font=("Trebuchet MS", 9),',
    '                     bg="#0E0909", fg=TXT_WHITE, anchor="w").pack(side="left")',
    "",
    "    def _scroll_to_section(self, key: str):",
    '        section = self._sections.get(key)',
    '        if not section:',
    '            return',
    '        self.update_idletasks()',
    '        inner_height = max(1, self._inner.winfo_height())',
    '        y = max(0, section.winfo_y())',
    '        self._canvas.yview_moveto(y / inner_height)',
    "",
]
lines[footer_idx:footer_idx] = helpers

path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("wired landing nav")
