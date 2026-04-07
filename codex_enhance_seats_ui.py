from pathlib import Path


path = Path("ui/dashboard.py")
lines = path.read_text(encoding="utf-8").splitlines()


def find_index(prefix: str) -> int:
    for idx, line in enumerate(lines):
        if line.startswith(prefix):
            return idx
    raise SystemExit(f"missing prefix: {prefix}")


# Remove profile/settings from sidebar items
lines = [
    line for line in lines
    if '"My Profile"' not in line and '"Settings"' not in line
]

# Insert live availability helpers after _seat_color
seat_color_idx = find_index("def _seat_color(seats) -> str:")
insert_after = None
for idx in range(seat_color_idx + 1, len(lines)):
    if lines[idx].startswith("# "):
        insert_after = idx
        break
if insert_after is None:
    raise SystemExit("could not locate insertion point after _seat_color")

helpers = [
    "",
    "def _seat_status_text(seats) -> str:",
    "    try:",
    "        n = int(seats) if seats is not None else 0",
    "    except (ValueError, TypeError):",
    "        n = 0",
    "    if n > 30:",
    "        return \"Available\"",
    "    if n > 10:",
    "        return \"Filling Fast\"",
    "    return \"Almost Full\"",
    "",
    "",
    "def _fetch_live_movie_availability(limit: int = 8) -> list:",
    "    conn = _db()",
    "    if not conn:",
    "        return []",
    "    try:",
    "        cur = conn.cursor(dictionary=True)",
    "        cur.execute(",
    "            \"\"\"SELECT m.movie_id,",
    "                      m.title,",
    "                      m.genre,",
    "                      COALESCE(SUM(CASE WHEN se.is_booked = 0 THEN 1 ELSE 0 END), 0) AS available_seats,",
    "                      COUNT(DISTINCT s.show_id) AS active_shows",
    "               FROM movies m",
    "               LEFT JOIN shows s ON s.movie_id = m.movie_id",
    "               LEFT JOIN seats se ON se.show_id = s.show_id",
    "               WHERE m.is_active = 1",
    "               GROUP BY m.movie_id, m.title, m.genre",
    "               ORDER BY available_seats ASC, m.title ASC",
    "               LIMIT %s\"\"\",",
    "            (limit,),",
    "        )",
    "        return cur.fetchall() or []",
    "    except Exception as exc:",
    "        print(f\"[DASH] _fetch_live_movie_availability: {exc}\")",
    "        return []",
    "    finally:",
    "        conn.close()",
    "",
]
lines[insert_after:insert_after] = helpers

# Replace sidebar seat availability panel
sidebar_start = find_index("        # Seat availability panel")
logout_start = find_index("        # Logout")
sidebar_block = [
    "        # Seat availability panel",
    "        tk.Label(s, text=\"Live Seat Availability\",",
    "                 font=(\"Trebuchet MS\", 8, \"bold\"),",
    "                 bg=BG_SIDEBAR, fg=TXT_GREY).pack(anchor=\"w\", padx=14, pady=(4, 2))",
    "        tk.Label(s, text=\"Shared live counts across all active shows\",",
    "                 font=(\"Trebuchet MS\", 7),",
    "                 bg=BG_SIDEBAR, fg=TXT_MUTED).pack(anchor=\"w\", padx=14, pady=(0, 6))",
    "",
    "        seat_frame = tk.Frame(s, bg=BG_SIDEBAR)",
    "        seat_frame.pack(fill=\"x\", padx=10, pady=(0, 6))",
    "",
    "        live_rows = _fetch_live_movie_availability(limit=8)",
    "        if not live_rows:",
    "            tk.Label(seat_frame, text=\"No live seat data available yet.\",",
    "                     font=(\"Trebuchet MS\", 8),",
    "                     bg=BG_SIDEBAR, fg=TXT_MUTED).pack(anchor=\"w\", padx=4, pady=6)",
    "        for row_data in live_rows:",
    "            row = tk.Frame(seat_frame, bg=BG_CARD, cursor=\"hand2\",",
    "                           highlightbackground=BORDER_DIM, highlightthickness=1)",
    "            row.pack(fill=\"x\", pady=3, ipady=5, ipadx=6)",
    "            title = str(row_data.get(\"title\", \"Movie\"))",
    "            short = (title[:13] + \"...\") if len(title) > 13 else title",
    "            available = int(row_data.get(\"available_seats\") or 0)",
    "            active_shows = int(row_data.get(\"active_shows\") or 0)",
    "            sc = _seat_color(available)",
    "            status = _seat_status_text(available)",
    "",
    "            tk.Label(row, text=short,",
    "                     font=(\"Trebuchet MS\", 8, \"bold\"),",
    "                     bg=BG_CARD, fg=TXT_WHITE, anchor=\"w\").pack(anchor=\"w\")",
    "            meta = tk.Frame(row, bg=BG_CARD)",
    "            meta.pack(fill=\"x\", pady=(2, 0))",
    "            tk.Label(meta, text=f\"{available} seats live\",",
    "                     font=(\"Trebuchet MS\", 8, \"bold\"),",
    "                     bg=BG_CARD, fg=sc).pack(side=\"left\")",
    "            tk.Label(meta, text=f\"{max(active_shows, 1)} shows\",",
    "                     font=(\"Trebuchet MS\", 7),",
    "                     bg=BG_CARD, fg=TXT_GREY).pack(side=\"right\")",
    "            tk.Label(row, text=status,",
    "                     font=(\"Trebuchet MS\", 7),",
    "                     bg=BG_CARD, fg=TXT_MUTED, anchor=\"w\").pack(anchor=\"w\", pady=(1, 0))",
    "",
    "            movie_match = next((m for m in _fetch_movies_from_db()",
    "                               if m.get(\"id\") == row_data.get(\"movie_id\")), None)",
    "            for w in [row] + list(row.winfo_children()) + list(meta.winfo_children()):",
    "                w.bind(\"<Button-1>\", lambda e, mv=movie_match: self._open_booking(mv) if mv else None)",
    "                w.bind(\"<Enter>\", lambda e, w=row: w.config(bg=_darken(BG_CARD, 1.15)))",
    "                w.bind(\"<Leave>\", lambda e, w=row: w.config(bg=BG_CARD))",
    "",
]
lines[sidebar_start:logout_start] = sidebar_block

# Enhance available shows header/details
show_header_idx = find_index('        tk.Label(self._body, text="Available Shows",')
lines[show_header_idx:show_header_idx + 2] = [
    '        tk.Label(self._body, text="Choose a Live Show",',
    '                 font=("Georgia", 12, "bold"),',
    '                 bg=BG_MODAL, fg=TXT_WHITE).pack(anchor="w", pady=(0, 2))',
    '        tk.Label(self._body, text="Seat counts below update from the database for all users.",',
    '                 font=("Trebuchet MS", 8),',
    '                 bg=BG_MODAL, fg=TXT_MUTED).pack(anchor="w", pady=(0, 8))',
]

# Enhance live show card labels
for idx, line in enumerate(lines):
    if 'price_str = f"?' in line:
        lines[idx] = '            price_str = f"Rs {sh.get(\'price\', \'?\')}"'
    if 'text=f"?  {date_str}    ?  {time_str}"' in line:
        lines[idx] = '                     text=f"Date {date_str}    Time {time_str}",'
    if 'text=f"?  {hall_str}    ?  {price_str} / seat"' in line:
        lines[idx] = '                     text=f"Hall {hall_str}    {price_str} / seat",'
    if 'text=f"? {avail} left"' in line:
        lines[idx] = '            tk.Label(row, text=f"{avail} seats live",'
    if 'sel_btn = tk.Label(row, text="SELECT ?"' in line:
        lines[idx] = '            sel_btn = tk.Label(row, text="Select Seats",'

# Add live seat banner in seat step
seat_screen_idx = find_index('        grid_frame = tk.Frame(self._body, bg=BG_MODAL)')
lines[seat_screen_idx:seat_screen_idx] = [
    '        live_bar = tk.Frame(self._body, bg=BG_CARD,',
    '                            highlightbackground=BORDER_DIM, highlightthickness=1)',
    '        live_bar.pack(fill="x", pady=(8, 8))',
    '        remaining = int(sh.get("available_seats") or sh.get("total_seats") or 0)',
    '        tk.Label(live_bar, text=f"Live remaining seats: {remaining}",',
    '                 font=("Trebuchet MS", 9, "bold"),',
    '                 bg=BG_CARD, fg=_seat_color(remaining), padx=12, pady=7).pack(side="left")',
    '        tk.Label(live_bar, text="Availability is shared for all users and updates from the database.",',
    '                 font=("Trebuchet MS", 8),',
    '                 bg=BG_CARD, fg=TXT_GREY, padx=12).pack(side="right")',
    "",
]

path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("enhanced seats ui")
