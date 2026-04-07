"""
ui/dashboard.py — Smart Movie Ticket Management System
=======================================================
BACKEND FIXES
-------------
• Book Ticket   → inserts into bookings + booking_seats, marks seats.is_booked=1
                  Added Step 2 "Show Selection" (shows table) between movie & seats
• My Bookings   → real SQL: bookings ⟶ shows ⟶ movies, correct column names
• Rate a Movie  → stores to ratings.score (tinyint), supports optional review text
• Cancel        → releases seats (is_booked=0) AND sets status='cancelled'
• Stats bar     → uses total_amount / score columns correctly

DB schema used
--------------
  users          : user_id, full_name, email, …
  movies         : movie_id, title, genre, language, rating (varchar), duration,
                   description, poster_path, is_active, created_at
  shows          : show_id, movie_id, show_date, show_time, hall,
                   total_seats (default 60), price
  seats          : seat_id, show_id, seat_number, seat_row, is_booked (default 0)
  bookings       : booking_id, user_id, show_id, booking_date, total_seats,
                   total_amount, status ('confirmed'/'cancelled'/'pending'),
                   payment_mode
  booking_seats  : id, booking_id, seat_id
  ratings        : rating_id, user_id, movie_id, score (tinyint), review, rated_at
"""

import tkinter as tk
from tkinter import ttk, messagebox
import math, random, time, sys, os, json

# ── Path fix ─────────────────────────────────────────────────────────────────
_SELF = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_SELF) if os.path.basename(_SELF) == "ui" else _SELF
for _p in [_ROOT, os.path.join(_ROOT, "ml")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── Palette ──────────────────────────────────────────────────────────────────
BG_DARK      = "#0D0A0A"
BG_NAV       = "#111010"
BG_SIDEBAR   = "#130E0E"
BG_CARD      = "#1A1414"
BG_CARD2     = "#1E1818"
BG_INPUT     = "#2A2020"
BG_MODAL     = "#181212"
ACCENT_RED   = "#E02020"
ACCENT_ORG   = "#F5A623"
ACCENT_BLUE  = "#4A90D9"
ACCENT_GREEN = "#27AE60"
ACCENT_PURP  = "#8B5CF6"
TXT_WHITE    = "#FFFFFF"
TXT_GREY     = "#B0A8A8"
TXT_MUTED    = "#6A5050"
BORDER_DIM   = "#2A1E1E"
SEP          = "#221818"

# ── Movie catalogue (UI fallback when DB has no movies) ───────────────────────
ALL_MOVIES = [
    {"id": 1, "title": "Inferno Rising",  "genre": "Action",    "lang": "English",
     "rating": 8.4, "emoji": "🔥", "color": "#C03010",
     "show": "7:00 PM  •  IMAX",   "seats": 42, "tag": "PG-13  •  2h 18m", "price": 280},
    {"id": 2, "title": "Eternal Bloom",   "genre": "Romance",   "lang": "Hindi",
     "rating": 7.9, "emoji": "🌸", "color": "#C0204A",
     "show": "6:30 PM  •  Hall 2",  "seats": 78, "tag": "PG  •  2h 02m",   "price": 220},
    {"id": 3, "title": "Pixel Quest",     "genre": "Animation", "lang": "English",
     "rating": 8.7, "emoji": "🎮", "color": "#1E6CA8",
     "show": "3:00 PM  •  Hall 1",  "seats": 15, "tag": "PG  •  1h 52m",   "price": 200},
    {"id": 4, "title": "Shadow Protocol", "genre": "Thriller",  "lang": "English",
     "rating": 8.1, "emoji": "🕵️", "color": "#1A1A3E",
     "show": "9:30 PM  •  Hall 3",  "seats": 30, "tag": "R  •  2h 11m",    "price": 250},
    {"id": 5, "title": "Cosmic Drift",    "genre": "Sci-Fi",    "lang": "English",
     "rating": 9.0, "emoji": "🚀", "color": "#0A3A6A",
     "show": "8:00 PM  •  IMAX",    "seats": 8,  "tag": "PG-13  •  2h 35m","price": 350},
    {"id": 6, "title": "Hasi Ke Rang",    "genre": "Comedy",    "lang": "Hindi",
     "rating": 7.5, "emoji": "😂", "color": "#C07010",
     "show": "4:30 PM  •  Hall 2",  "seats": 55, "tag": "U/A  •  1h 58m",  "price": 180},
    {"id": 7, "title": "Whisper in Dark", "genre": "Horror",    "lang": "English",
     "rating": 7.8, "emoji": "👻", "color": "#2A0A2A",
     "show": "11:00 PM  •  Hall 3", "seats": 22, "tag": "A  •  1h 44m",    "price": 210},
    {"id": 8, "title": "Yaar Mera",       "genre": "Drama",     "lang": "Marathi",
     "rating": 8.2, "emoji": "🎭", "color": "#4A2A6A",
     "show": "5:15 PM  •  Hall 1",  "seats": 67, "tag": "U/A  •  2h 08m",  "price": 190},
]

UPCOMING = [
    "⚡ Venom: Last Dance — Apr 18",
    "🌊 Aquaman 3 — May 2",
    "🔥 Mission Impossible 8 — May 23",
    "🧙 Fantastic Beasts 4 — Jun 6",
    "🕷 Spider-Man: Beyond — Jul 4",
    "🦁 The Lion King 3 — Jul 19",
]

SIDEBAR_ITEMS = [
    ("🎟", "Book Ticket",  ACCENT_RED,  "book"),
    ("📋", "My Bookings",  ACCENT_BLUE, "bookings"),
    ("⭐", "Rate a Movie", ACCENT_ORG,  "rate"),
    ("👤", "My Profile",   TXT_GREY,    "profile"),
    ("⚙️", "Settings",    TXT_MUTED,   "settings"),
]

_GENRE_EMOJI = {
    "Action": "🔥", "Romance": "🌸", "Comedy": "😂",
    "Thriller": "🕵️", "Horror": "👻", "Sci-Fi": "🚀",
    "Animation": "🎮", "Drama": "🎭", "Mystery": "🔍",
    "Fantasy": "🧙", "Biography": "📖", "Sports": "⚽",
}
_GENRE_COLOR = {
    "Action": "#C03010", "Romance": "#C0204A", "Comedy": "#C07010",
    "Thriller": "#1A1A3E", "Horror": "#2A0A2A", "Sci-Fi": "#0A3A6A",
    "Animation": "#1E6CA8", "Drama": "#4A2A6A", "Mystery": "#1A3A1A",
    "Fantasy": "#3A1A4A", "Biography": "#3A3010", "Sports": "#0A3A20",
}


# ═══════════════════════════════════════════════════════
#  DATABASE HELPERS  (all updated to match actual schema)
# ═══════════════════════════════════════════════════════

def _db():
    try:
        from db import get_connection
        return get_connection()
    except Exception:
        return None


def _fetch_movies_from_db() -> list:
    """
    Fetch active movies from DB.
    Maps to dashboard dict format; falls back to ALL_MOVIES if DB empty.
    """
    conn = _db()
    if not conn:
        return ALL_MOVIES
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT movie_id, title, genre, language, rating, duration "
            "FROM movies WHERE is_active=1 ORDER BY title")
        rows = cur.fetchall() or []
        if not rows:
            return ALL_MOVIES

        result = []
        for r in rows:
            # Try to match with ALL_MOVIES for emoji/color
            match = next(
                (m for m in ALL_MOVIES
                 if m["title"].lower() == str(r["title"]).lower()), None)
            if match:
                m_dict = dict(match)
                m_dict["id"] = r["movie_id"]
                try:
                    m_dict["rating"] = float(r["rating"]) if r.get("rating") else match["rating"]
                except (ValueError, TypeError):
                    pass
                result.append(m_dict)
            else:
                genre = str(r.get("genre") or "Drama")
                dur   = r.get("duration") or 0
                try:
                    rat = float(r["rating"]) if r.get("rating") else 7.0
                except (ValueError, TypeError):
                    rat = 7.0
                result.append({
                    "id":     r["movie_id"],
                    "title":  r["title"],
                    "genre":  genre,
                    "lang":   r.get("language") or "English",
                    "rating": rat,
                    "emoji":  _GENRE_EMOJI.get(genre, "🎬"),
                    "color":  _GENRE_COLOR.get(genre, "#2A2424"),
                    "show":   "—",
                    "seats":  30,
                    "tag":    f"{dur} min" if dur else "—",
                    "price":  200,
                })
        return result if result else ALL_MOVIES
    except Exception as exc:
        print(f"[DASH] _fetch_movies_from_db: {exc}")
        return ALL_MOVIES
    finally:
        conn.close()


def _fetch_shows_for_movie(movie_id: int) -> list:
    """
    Return shows for a movie, including available seat count.
    Schema: shows(show_id, movie_id, show_date, show_time, hall, total_seats, price)
            seats(seat_id, show_id, seat_number, seat_row, is_booked)
    """
    conn = _db()
    if not conn:
        return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """SELECT s.show_id, s.movie_id, s.show_date, s.show_time,
                      s.hall, s.total_seats, s.price,
                      COUNT(CASE WHEN se.is_booked = 0 THEN 1 END) AS available_seats
               FROM shows s
               LEFT JOIN seats se ON se.show_id = s.show_id
               WHERE s.movie_id = %s
               GROUP BY s.show_id
               ORDER BY s.show_date, s.show_time""",
            (movie_id,))
        return cur.fetchall() or []
    except Exception as exc:
        print(f"[DASH] _fetch_shows_for_movie: {exc}")
        return []
    finally:
        conn.close()


def _fetch_seats_for_show(show_id: int) -> list:
    """
    Return all seat rows for a show.
    Schema: seats(seat_id, show_id, seat_number, seat_row, is_booked)
    """
    conn = _db()
    if not conn:
        return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """SELECT seat_id, seat_number, seat_row, is_booked
               FROM seats
               WHERE show_id = %s
               ORDER BY seat_row, seat_number""",
            (show_id,))
        return cur.fetchall() or []
    except Exception as exc:
        print(f"[DASH] _fetch_seats_for_show: {exc}")
        return []
    finally:
        conn.close()


def _fetch_user_stats(user_id: int) -> dict:
    """
    Pull booking / rating stats from DB.
    bookings.total_amount  (not total_price)
    ratings.score          (not rating)
    """
    defaults = {"booked": 0, "watched": 0, "avg_rating": 0.0, "spent": 0}
    conn = _db()
    if not conn:
        return defaults
    try:
        cur = conn.cursor(dictionary=True)

        cur.execute(
            "SELECT COUNT(*) AS cnt, COALESCE(SUM(total_amount), 0) AS spent "
            "FROM bookings WHERE user_id = %s", (user_id,))
        row = cur.fetchone() or {}
        defaults["booked"] = int(row.get("cnt", 0))
        defaults["spent"]  = int(float(row.get("spent", 0)))

        cur.execute(
            "SELECT COUNT(*) AS cnt FROM bookings "
            "WHERE user_id = %s AND status = 'confirmed'", (user_id,))
        row2 = cur.fetchone() or {}
        defaults["watched"] = int(row2.get("cnt", 0))

        cur.execute(
            "SELECT COALESCE(AVG(score), 0) AS avg FROM ratings WHERE user_id = %s",
            (user_id,))
        row3 = cur.fetchone() or {}
        defaults["avg_rating"] = round(float(row3.get("avg", 0)), 1)

        return defaults
    except Exception as exc:
        print(f"[DASH] _fetch_user_stats: {exc}")
        return defaults
    finally:
        conn.close()


def _fetch_user_bookings(user_id: int) -> list:
    """
    Fetch bookings with show + movie info.
    Joins: bookings → shows → movies
    Returns columns: booking_id, show_id, booking_date, total_seats,
                     total_amount, status, payment_mode,
                     movie_title, genre, show_date, show_time, hall, price
    """
    conn = _db()
    if not conn:
        return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """SELECT b.booking_id,
                      b.show_id,
                      b.booking_date,
                      b.total_seats,
                      b.total_amount,
                      b.status,
                      b.payment_mode,
                      COALESCE(m.title,  'Unknown') AS movie_title,
                      COALESCE(m.genre,  '—')       AS genre,
                      s.show_date,
                      s.show_time,
                      s.hall,
                      s.price
               FROM bookings b
               LEFT JOIN shows s  ON s.show_id  = b.show_id
               LEFT JOIN movies m ON m.movie_id = s.movie_id
               WHERE b.user_id = %s
               ORDER BY b.booking_date DESC""",
            (user_id,))
        return cur.fetchall() or []
    except Exception as exc:
        print(f"[DASH] _fetch_user_bookings: {exc}")
        return []
    finally:
        conn.close()


def _cancel_booking(booking_id: int) -> bool:
    """
    Cancel a booking:
    1. Release seats → seats.is_booked = 0
    2. Set bookings.status = 'cancelled'
    """
    conn = _db()
    if not conn:
        return False
    try:
        cur = conn.cursor()

        # 1. Get booked seat IDs from junction table
        cur.execute(
            "SELECT seat_id FROM booking_seats WHERE booking_id = %s",
            (booking_id,))
        seat_ids = [row[0] for row in cur.fetchall()]

        # 2. Release seats
        if seat_ids:
            placeholders = ", ".join(["%s"] * len(seat_ids))
            cur.execute(
                f"UPDATE seats SET is_booked = 0 WHERE seat_id IN ({placeholders})",
                seat_ids)

        # 3. Cancel the booking
        cur.execute(
            "UPDATE bookings SET status = 'cancelled' WHERE booking_id = %s",
            (booking_id,))
        conn.commit()
        return cur.rowcount > 0
    except Exception as exc:
        print(f"[DASH] _cancel_booking: {exc}")
        conn.rollback()
        return False
    finally:
        conn.close()


def _save_booking(user_id: int, show_id: int, movie: dict,
                  seat_ids: list, total_amount: float,
                  payment_mode: str = "cash") -> bool:
    """
    Insert booking row + booking_seats rows + mark seats as booked.
    Tables: bookings, booking_seats, seats
    """
    conn = _db()
    total_seats = len(seat_ids)

    if not conn:
        # Demo / offline mode
        print(f"[DEMO] Booking saved: show_id={show_id} "
              f"seats={seat_ids}  total=₹{total_amount:.0f}")
        return True
    try:
        cur = conn.cursor()

        # 1. Insert booking record
        cur.execute(
            """INSERT INTO bookings
               (user_id, show_id, total_seats, total_amount, status, payment_mode)
               VALUES (%s, %s, %s, %s, 'confirmed', %s)""",
            (user_id, show_id, total_seats, total_amount, payment_mode))
        booking_id = cur.lastrowid

        # 2. Insert junction records + mark seats booked
        for seat_id in seat_ids:
            cur.execute(
                "INSERT INTO booking_seats (booking_id, seat_id) VALUES (%s, %s)",
                (booking_id, seat_id))
            cur.execute(
                "UPDATE seats SET is_booked = 1 WHERE seat_id = %s",
                (seat_id,))

        conn.commit()
        print(f"[DB] Booking #{booking_id} confirmed — "
              f"{total_seats} seat(s), ₹{total_amount:.0f}")
        return True
    except Exception as exc:
        print(f"[DASH] _save_booking: {exc}")
        conn.rollback()
        return False
    finally:
        conn.close()


def _save_rating(user_id: int, movie_id: int,
                 score: int, review: str = "") -> bool:
    """
    Upsert into ratings(user_id, movie_id, score, review).
    Column is 'score' (tinyint), NOT 'rating'.
    """
    conn = _db()
    if not conn:
        print(f"[DEMO] Rating saved: movie_id={movie_id}  score={score}")
        return True
    try:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO ratings (user_id, movie_id, score, review)
               VALUES (%s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE score = %s, review = %s""",
            (user_id, movie_id, score, review, score, review))
        conn.commit()
        print(f"[DB] Rating saved: user={user_id}  movie={movie_id}  score={score}")
        return True
    except Exception as exc:
        print(f"[DASH] _save_rating: {exc}")
        return False
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════

def _darken(hexcol: str, factor: float) -> str:
    try:
        r = int(hexcol[1:3], 16)
        g = int(hexcol[3:5], 16)
        b = int(hexcol[5:7], 16)
        return "#{:02x}{:02x}{:02x}".format(
            max(0, min(255, int(r * factor))),
            max(0, min(255, int(g * factor))),
            max(0, min(255, int(b * factor))))
    except Exception:
        return hexcol


def _seat_color(seats) -> str:
    try:
        n = int(seats) if seats is not None else 0
    except (ValueError, TypeError):
        n = 0
    if n > 30: return ACCENT_GREEN
    if n > 10: return ACCENT_ORG
    return ACCENT_RED


# ─────────────────────────────────────────────
#  PARTICLE CANVAS
# ─────────────────────────────────────────────
class ParticleCanvas(tk.Canvas):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self._particles = []
        self._running   = True
        for _ in range(35):
            self._particles.append({
                "x":     random.uniform(0, 1200),
                "y":     random.uniform(0, 160),
                "r":     random.uniform(1, 8),
                "spd":   random.uniform(0.2, 0.9),
                "col":   random.choice(["#8B3010","#C04A20","#F5A623",
                                        "#A03010","#D06020"]),
                "phase": random.uniform(0, 2 * math.pi),
            })
        self._animate()

    def _animate(self):
        if not self._running:
            return
        self.delete("p")
        t = time.time()
        for p in self._particles:
            p["x"] -= p["spd"] * 0.35
            p["y"] += math.sin(t * 0.5 + p["phase"]) * 0.3
            if p["x"] < -15:
                p["x"] = (self.winfo_width() or 1200) + 15
                p["y"] = random.uniform(0, 160)
            r = p["r"]
            dim = _darken(p["col"], 0.15)
            self.create_oval(p["x"]-r*2, p["y"]-r*2, p["x"]+r*2, p["y"]+r*2,
                             fill=dim, outline="", tags="p")
            self.create_oval(p["x"]-r,   p["y"]-r,   p["x"]+r,   p["y"]+r,
                             fill=p["col"], outline="", tags="p")
        self.after(33, self._animate)

    def stop(self):
        self._running = False


# ─────────────────────────────────────────────
#  MARQUEE TICKER
# ─────────────────────────────────────────────
class MarqueeTicker(tk.Canvas):
    def __init__(self, master, items, **kw):
        super().__init__(master, highlightthickness=0, bd=0, **kw)
        self._items   = items
        self._x       = 0
        self._running = True
        self._ids     = []
        self._text_w  = 800
        self.bind("<Configure>", lambda e: self._reset())
        self._reset()
        self._scroll()

    def _reset(self):
        self.delete("all")
        text = "          ".join(self._items)
        id1 = self.create_text(0, 14, text=text,
                               font=("Trebuchet MS", 8),
                               fill=ACCENT_ORG, anchor="w", tags="t")
        id2 = self.create_text(0, 14, text=text,
                               font=("Trebuchet MS", 8),
                               fill=ACCENT_ORG, anchor="w", tags="t")
        self._ids = [id1, id2]
        bbox = self.bbox(id1)
        self._text_w = (bbox[2] - bbox[0]) if bbox else 800
        self.coords(id2, self._text_w + 40, 14)
        self._x = 0

    def _scroll(self):
        if not self._running:
            return
        self._x -= 1
        if self._x < -self._text_w - 40:
            self._x = 0
        for i, tid in enumerate(self._ids):
            self.coords(tid, self._x + i * (self._text_w + 40), 14)
        self.after(25, self._scroll)

    def stop(self):
        self._running = False


# ─────────────────────────────────────────────
#  REUSABLE MOVIE CARD
# ─────────────────────────────────────────────
def movie_card(parent, movie, on_book=None, width=215, height=275, badge=None):
    card = tk.Frame(parent, bg=movie["color"],
                    width=width, height=height, cursor="hand2")
    card.pack_propagate(False)
    dark = _darken(movie["color"], 0.45)

    poster = tk.Frame(card, bg=dark, height=int(height * 0.50))
    poster.pack(fill="x")
    poster.pack_propagate(False)

    if badge:
        tk.Label(poster, text=badge,
                 font=("Trebuchet MS", 7, "bold"),
                 bg=ACCENT_ORG, fg=BG_DARK,
                 padx=6, pady=2).place(x=6, y=6)

    tk.Label(poster, text=f"⭐ {movie['rating']}",
             font=("Trebuchet MS", 8, "bold"),
             bg="#000000", fg=ACCENT_ORG,
             padx=5, pady=2).place(relx=1.0, x=-4, y=4, anchor="ne")

    tk.Label(poster, text=movie["emoji"],
             font=("Segoe UI Emoji", 36),
             bg=dark).pack(expand=True)

    info = tk.Frame(card, bg=movie["color"])
    info.pack(fill="both", expand=True)

    tk.Label(info, text=movie["title"],
             font=("Trebuchet MS", 10, "bold"),
             bg=movie["color"], fg=TXT_WHITE,
             wraplength=width - 16).pack(pady=(5, 0))
    tk.Label(info, text=f"{movie['genre']}  •  {movie.get('lang', movie.get('language',''))}",
             font=("Trebuchet MS", 8),
             bg=movie["color"], fg=ACCENT_ORG).pack()
    tk.Label(info, text=movie.get("show", "—"),
             font=("Trebuchet MS", 7),
             bg=movie["color"], fg=TXT_GREY).pack()

    sc = _seat_color(movie.get("seats", 30))
    tk.Label(info, text=f"🪑 {movie.get('seats', '—')} seats  •  ₹{movie.get('price', '—')}",
             font=("Trebuchet MS", 7),
             bg=movie["color"], fg=sc).pack()

    book = tk.Label(info, text="BOOK NOW",
                    font=("Trebuchet MS", 8, "bold"),
                    bg=ACCENT_RED, fg=TXT_WHITE,
                    padx=10, pady=3, cursor="hand2")
    book.pack(pady=(4, 8))
    book.bind("<Button-1>", lambda e: on_book(movie) if on_book else None)
    book.bind("<Enter>",    lambda e, w=book: w.config(bg="#B01010"))
    book.bind("<Leave>",    lambda e, w=book: w.config(bg=ACCENT_RED))
    return card


# ─────────────────────────────────────────────
#  STAT CHIP
# ─────────────────────────────────────────────
def stat_chip(parent, icon, value, label, accent):
    f = tk.Frame(parent, bg=BG_CARD2,
                 highlightbackground=BORDER_DIM, highlightthickness=1)
    f.pack(side="left", padx=8, ipadx=14, ipady=8)
    tk.Label(f, text=icon, font=("Segoe UI Emoji", 20),
             bg=BG_CARD2, fg=accent).pack()
    tk.Label(f, text=str(value), font=("Georgia", 18, "bold"),
             bg=BG_CARD2, fg=TXT_WHITE).pack()
    tk.Label(f, text=label, font=("Trebuchet MS", 8),
             bg=BG_CARD2, fg=TXT_GREY).pack()


# ─────────────────────────────────────────────
#  SIDEBAR BUTTON
# ─────────────────────────────────────────────
def sidebar_btn(parent, icon, label, accent, key, on_click=None, active=False):
    bg = _darken(accent, 0.18) if active else BG_SIDEBAR
    f  = tk.Frame(parent, bg=bg, cursor="hand2")
    f.pack(fill="x", pady=1)

    bar = tk.Frame(f, bg=accent if active else BG_SIDEBAR, width=3)
    bar.pack(side="left", fill="y")

    tk.Label(f, text=icon, font=("Segoe UI Emoji", 14),
             bg=bg, fg=accent, padx=12, pady=8).pack(side="left")
    tk.Label(f, text=label, font=("Trebuchet MS", 9, "bold"),
             bg=bg, fg=TXT_WHITE if active else TXT_GREY).pack(side="left")

    def enter(_):
        f.config(bg=_darken(accent, 0.22))
        bar.config(bg=accent)
        for w in f.winfo_children():
            try: w.config(bg=_darken(accent, 0.22))
            except: pass
    def leave(_):
        nb = _darken(accent, 0.18) if active else BG_SIDEBAR
        f.config(bg=nb)
        bar.config(bg=accent if active else BG_SIDEBAR)
        for w in f.winfo_children():
            try: w.config(bg=nb)
            except: pass
    def click(_):
        if on_click:
            on_click(key)

    for w in [f] + list(f.winfo_children()):
        w.bind("<Enter>",    enter)
        w.bind("<Leave>",    leave)
        w.bind("<Button-1>", click)


# ═══════════════════════════════════════════════════════
#  MODAL: BOOK TICKET  (3-step: Movie → Show → Seats)
# ═══════════════════════════════════════════════════════
class BookingModal(tk.Toplevel):
    """
    Step 1 — Pick a movie  (from DB movies table, fallback ALL_MOVIES)
    Step 2 — Pick a show   (from DB shows table for that movie)
    Step 3 — Pick seats    (from DB seats table for that show)
    Confirm → bookings + booking_seats + seats.is_booked=1
    """
    _DEMO_ROWS = 6
    _DEMO_COLS = 10

    def __init__(self, master, user: dict,
                 preselect_movie=None, on_success=None):
        super().__init__(master)
        self.title("Book a Ticket")
        self.geometry("840x660")
        self.resizable(False, False)
        self.configure(bg=BG_MODAL)
        self.grab_set()
        self.focus_force()

        self._user            = user
        self._on_success      = on_success
        self._movie           = preselect_movie   # dict
        self._show            = None              # dict from shows table
        self._selected_seats  = []               # list of (seat_id, label)
        self._seat_btns       = {}
        self._total_lbl       = None
        self._confirm_btn     = None

        self._build_chrome()

        if preselect_movie:
            self._show_show_step()
        else:
            self._show_movie_step()

    # ── Chrome (header + body frame) ─────────────────────────────────────────
    def _build_chrome(self):
        hdr = tk.Frame(self, bg="#0F0A0A", height=54)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="🎟  Book a Ticket",
                 font=("Georgia", 15, "bold"),
                 bg="#0F0A0A", fg=TXT_WHITE).pack(side="left", padx=20, pady=14)
        close = tk.Label(hdr, text="✕", font=("Trebuchet MS", 13),
                         bg="#0F0A0A", fg=TXT_MUTED, cursor="hand2")
        close.pack(side="right", padx=16)
        close.bind("<Button-1>", lambda e: self.destroy())

        self._body = tk.Frame(self, bg=BG_MODAL)
        self._body.pack(fill="both", expand=True, padx=20, pady=12)

    def _clear_body(self):
        for w in self._body.winfo_children():
            w.destroy()

    # ── Breadcrumb ────────────────────────────────────────────────────────────
    def _breadcrumb(self, steps: list):
        bc = tk.Frame(self._body, bg=BG_MODAL)
        bc.pack(anchor="w", pady=(0, 6))
        for i, step in enumerate(steps):
            done    = step.startswith("✓")
            is_curr = (not done and i == sum(1 for s in steps if s.startswith("✓")))
            col = (ACCENT_GREEN if done
                   else TXT_WHITE if is_curr
                   else TXT_MUTED)
            tk.Label(bc, text=step,
                     font=("Trebuchet MS", 9, "bold" if is_curr else ""),
                     bg=BG_MODAL, fg=col).pack(side="left")
            if i < len(steps) - 1:
                tk.Label(bc, text="  ›  ",
                         font=("Trebuchet MS", 9),
                         bg=BG_MODAL, fg=TXT_MUTED).pack(side="left")

    # ── STEP 1 — Movie Picker ─────────────────────────────────────────────────
    def _show_movie_step(self):
        self._clear_body()
        self._movie = None
        self._show  = None
        self._selected_seats = []

        self._breadcrumb(["Select Movie", "Select Show", "Select Seats"])

        tk.Label(self._body, text="Select a Movie",
                 font=("Georgia", 13, "bold"),
                 bg=BG_MODAL, fg=TXT_WHITE).pack(anchor="w", pady=(4, 8))

        canvas = tk.Canvas(self._body, bg=BG_MODAL,
                           highlightthickness=0, bd=0, height=460)
        vsb = ttk.Scrollbar(self._body, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        inner = tk.Frame(canvas, bg=BG_MODAL)
        cwin  = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(cwin, width=e.width))

        movies = _fetch_movies_from_db()

        for m in movies:
            row = tk.Frame(inner, bg=BG_CARD,
                           highlightbackground=BORDER_DIM,
                           highlightthickness=1, cursor="hand2")
            row.pack(fill="x", pady=4, ipady=6, ipadx=8)

            tk.Label(row, text=m["emoji"],
                     font=("Segoe UI Emoji", 24),
                     bg=BG_CARD, fg=m["color"],
                     padx=10).pack(side="left")

            info = tk.Frame(row, bg=BG_CARD)
            info.pack(side="left", fill="x", expand=True)
            tk.Label(info, text=m["title"],
                     font=("Trebuchet MS", 11, "bold"),
                     bg=BG_CARD, fg=TXT_WHITE).pack(anchor="w")
            lang = m.get("lang") or m.get("language", "—")
            tk.Label(info,
                     text=f"{m['genre']}  •  {lang}",
                     font=("Trebuchet MS", 8),
                     bg=BG_CARD, fg=TXT_GREY).pack(anchor="w")

            tk.Label(row, text=f"⭐ {m['rating']}",
                     font=("Trebuchet MS", 9, "bold"),
                     bg=BG_CARD, fg=ACCENT_ORG, padx=8).pack(side="right")

            sel_btn = tk.Label(row, text="SELECT →",
                               font=("Trebuchet MS", 9, "bold"),
                               bg=ACCENT_RED, fg=TXT_WHITE,
                               padx=12, pady=6, cursor="hand2")
            sel_btn.pack(side="right", padx=8)
            sel_btn.bind("<Button-1>", lambda e, mv=m: self._pick_movie(mv))
            sel_btn.bind("<Enter>",    lambda e, w=sel_btn: w.config(bg="#B01010"))
            sel_btn.bind("<Leave>",    lambda e, w=sel_btn: w.config(bg=ACCENT_RED))

            # Whole row clickable
            for child in [row] + list(row.winfo_children()):
                child.bind("<Button-1>",
                           lambda e, mv=m: self._pick_movie(mv))

    def _pick_movie(self, movie: dict):
        self._movie = movie
        self._show_show_step()

    # ── STEP 2 — Show Picker ──────────────────────────────────────────────────
    def _show_show_step(self):
        self._clear_body()
        self._show = None
        self._selected_seats = []
        m = self._movie

        self._breadcrumb(["✓ Movie", "Select Show", "Select Seats"])

        # Movie info strip
        strip_bg = _darken(m["color"], 0.35)
        strip    = tk.Frame(self._body, bg=strip_bg, padx=14, pady=8)
        strip.pack(fill="x", pady=(4, 10))
        tk.Label(strip, text=f"{m['emoji']}  {m['title']}",
                 font=("Trebuchet MS", 12, "bold"),
                 bg=strip_bg, fg=TXT_WHITE).pack(side="left")

        tk.Label(self._body, text="Available Shows",
                 font=("Georgia", 12, "bold"),
                 bg=BG_MODAL, fg=TXT_WHITE).pack(anchor="w", pady=(0, 8))

        shows = _fetch_shows_for_movie(m["id"])

        if not shows:
            # ── No shows in DB ─────────────────────────────────────────────
            tk.Label(self._body,
                     text=(
                         "⚠  No shows are scheduled for this movie yet.\n\n"
                         "Please ask your admin to add shows in the database,\n"
                         "or choose a different movie."
                     ),
                     font=("Trebuchet MS", 11),
                     bg=BG_MODAL, fg=TXT_MUTED,
                     justify="center").pack(expand=True)
            back = tk.Label(self._body, text="← Back to Movies",
                            font=("Trebuchet MS", 9),
                            bg=BG_INPUT, fg=TXT_GREY,
                            padx=14, pady=7, cursor="hand2")
            back.pack(pady=12)
            back.bind("<Button-1>", lambda e: self._show_movie_step())
            return

        canvas = tk.Canvas(self._body, bg=BG_MODAL,
                           highlightthickness=0, bd=0, height=410)
        vsb = ttk.Scrollbar(self._body, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        inner = tk.Frame(canvas, bg=BG_MODAL)
        cwin  = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(cwin, width=e.width))

        for sh in shows:
            avail = sh.get("available_seats")
            if avail is None:
                avail = sh.get("total_seats", 60)
            try:
                avail = int(avail)
            except (ValueError, TypeError):
                avail = 0

            date_str  = str(sh.get("show_date",  "—"))
            time_str  = str(sh.get("show_time",  "—"))[:5]
            hall_str  = str(sh.get("hall",        "—"))
            price_str = f"₹{sh.get('price', '—')}"
            sc        = _seat_color(avail)

            row = tk.Frame(inner, bg=BG_CARD,
                           highlightbackground=BORDER_DIM,
                           highlightthickness=1, cursor="hand2")
            row.pack(fill="x", pady=4, ipady=10, ipadx=10)

            info = tk.Frame(row, bg=BG_CARD)
            info.pack(side="left", fill="x", expand=True)

            tk.Label(info,
                     text=f"📅  {date_str}    🕐  {time_str}",
                     font=("Trebuchet MS", 11, "bold"),
                     bg=BG_CARD, fg=TXT_WHITE).pack(anchor="w")
            tk.Label(info,
                     text=f"🏛  {hall_str}    💰  {price_str} / seat",
                     font=("Trebuchet MS", 9),
                     bg=BG_CARD, fg=TXT_GREY).pack(anchor="w")

            tk.Label(row, text=f"🪑 {avail} left",
                     font=("Trebuchet MS", 9, "bold"),
                     bg=BG_CARD, fg=sc, padx=10).pack(side="right")

            sel_btn = tk.Label(row, text="SELECT →",
                               font=("Trebuchet MS", 9, "bold"),
                               bg=ACCENT_GREEN, fg=TXT_WHITE,
                               padx=12, pady=6, cursor="hand2")
            sel_btn.pack(side="right", padx=8)
            sel_btn.bind("<Button-1>", lambda e, s=sh: self._pick_show(s))
            sel_btn.bind("<Enter>",    lambda e, w=sel_btn: w.config(bg="#1D7A45"))
            sel_btn.bind("<Leave>",    lambda e, w=sel_btn: w.config(bg=ACCENT_GREEN))

        # Back
        back = tk.Label(self._body, text="← Back to Movies",
                        font=("Trebuchet MS", 9),
                        bg=BG_INPUT, fg=TXT_GREY,
                        padx=10, pady=5, cursor="hand2")
        back.pack(anchor="w", pady=(8, 0))
        back.bind("<Button-1>", lambda e: self._show_movie_step())

    def _pick_show(self, show: dict):
        self._show = show
        self._show_seat_step()

    # ── STEP 3 — Seat Picker ──────────────────────────────────────────────────
    def _show_seat_step(self):
        self._clear_body()
        self._selected_seats = []
        self._seat_btns      = {}
        m  = self._movie
        sh = self._show

        self._breadcrumb(["✓ Movie", "✓ Show", "Select Seats"])

        # Info bar
        strip_bg = _darken(m["color"], 0.35)
        strip    = tk.Frame(self._body, bg=strip_bg, padx=14, pady=8)
        strip.pack(fill="x", pady=(4, 6))
        tk.Label(strip, text=f"{m['emoji']}  {m['title']}",
                 font=("Trebuchet MS", 11, "bold"),
                 bg=strip_bg, fg=TXT_WHITE).pack(side="left")
        show_lbl = (f"📅 {sh.get('show_date','')}  "
                    f"🕐 {str(sh.get('show_time',''))[:5]}  "
                    f"🏛 {sh.get('hall','')}  "
                    f"₹{sh.get('price','')}/seat")
        tk.Label(strip, text=show_lbl,
                 font=("Trebuchet MS", 8),
                 bg=strip_bg, fg=ACCENT_ORG).pack(side="right")

        # Screen
        tk.Frame(self._body, bg="#3A3030", height=8).pack(
            fill="x", padx=40, pady=(2, 1))
        tk.Label(self._body, text="▲  SCREEN  ▲",
                 font=("Trebuchet MS", 7),
                 bg=BG_MODAL, fg=TXT_MUTED).pack()

        grid_frame = tk.Frame(self._body, bg=BG_MODAL)
        grid_frame.pack(pady=6)

        # ── Fetch seats from DB ───────────────────────────────────────────
        db_seats = _fetch_seats_for_show(sh["show_id"])

        if db_seats:
            # Group by seat_row
            rows_dict: dict = {}
            for seat in db_seats:
                rk = str(seat.get("seat_row") or "A")
                rows_dict.setdefault(rk, []).append(seat)

            for ri, rk in enumerate(sorted(rows_dict)):
                tk.Label(grid_frame, text=rk,
                         font=("Trebuchet MS", 8, "bold"),
                         bg=BG_MODAL, fg=TXT_MUTED,
                         width=2).grid(row=ri, column=0, padx=(0, 6))

                row_seats = sorted(rows_dict[rk],
                                   key=lambda s: str(s.get("seat_number", "")))
                for ci, seat in enumerate(row_seats):
                    sid    = seat["seat_id"]
                    snum   = str(seat.get("seat_number", ci + 1))
                    label  = f"{rk}{snum}"
                    booked = bool(int(seat.get("is_booked", 0)))

                    bg_c = "#3A2020" if booked else BG_INPUT
                    btn  = tk.Label(grid_frame, text=label,
                                    font=("Trebuchet MS", 7),
                                    bg=bg_c,
                                    fg=TXT_MUTED if booked else TXT_GREY,
                                    width=5, pady=4,
                                    cursor="" if booked else "hand2")
                    btn.grid(row=ri, column=ci + 1, padx=2, pady=2)
                    if not booked:
                        btn.bind("<Button-1>",
                                 lambda e, s=sid, lbl=label, b=btn:
                                 self._toggle_seat(s, lbl, b))
                    self._seat_btns[sid] = (btn, booked)

        else:
            # ── Demo grid fallback (no seats in DB yet) ───────────────────
            import random as _rnd
            _rnd.seed(sh.get("show_id", 1) * 7)
            total    = self._DEMO_ROWS * self._DEMO_COLS
            avail_db = sh.get("available_seats") or sh.get("total_seats", total)
            try:
                n_booked = total - int(avail_db)
            except (ValueError, TypeError):
                n_booked = 0
            n_booked = max(0, min(n_booked, total))
            booked_idx = set(_rnd.sample(range(total), n_booked))

            for row_i in range(self._DEMO_ROWS):
                rk = chr(65 + row_i)
                tk.Label(grid_frame, text=rk,
                         font=("Trebuchet MS", 8, "bold"),
                         bg=BG_MODAL, fg=TXT_MUTED,
                         width=2).grid(row=row_i, column=0, padx=(0, 6))
                for col_i in range(self._DEMO_COLS):
                    idx    = row_i * self._DEMO_COLS + col_i
                    label  = f"{rk}{col_i + 1}"
                    fake_id = -(idx + 1)     # negative = demo (no real seat_id)
                    booked  = idx in booked_idx

                    bg_c = "#3A2020" if booked else BG_INPUT
                    btn  = tk.Label(grid_frame, text=label,
                                    font=("Trebuchet MS", 7),
                                    bg=bg_c,
                                    fg=TXT_MUTED if booked else TXT_GREY,
                                    width=4, pady=5,
                                    cursor="" if booked else "hand2")
                    btn.grid(row=row_i, column=col_i + 1, padx=2, pady=2)
                    if not booked:
                        btn.bind("<Button-1>",
                                 lambda e, s=fake_id, lbl=label, b=btn:
                                 self._toggle_seat(s, lbl, b))

            # Warning label
            tk.Label(self._body,
                     text="⚠  Seat layout is a preview — "
                          "no seat records found in DB for this show.",
                     font=("Trebuchet MS", 7),
                     bg=BG_MODAL, fg=TXT_MUTED).pack()

        # Legend
        legend = tk.Frame(self._body, bg=BG_MODAL)
        legend.pack(pady=4)
        for txt, col in [("Available", BG_INPUT),
                          ("Selected",  ACCENT_RED),
                          ("Booked",    "#3A2020")]:
            tk.Frame(legend, bg=col, width=14, height=14).pack(
                side="left", padx=(8, 3))
            tk.Label(legend, text=txt,
                     font=("Trebuchet MS", 8),
                     bg=BG_MODAL, fg=TXT_GREY).pack(side="left", padx=(0, 10))

        # Bottom action bar
        bottom = tk.Frame(self._body, bg=BG_MODAL)
        bottom.pack(fill="x", pady=(6, 0))

        back = tk.Label(bottom, text="← Back",
                        font=("Trebuchet MS", 9),
                        bg=BG_INPUT, fg=TXT_GREY,
                        padx=10, pady=5, cursor="hand2")
        back.pack(side="left")
        back.bind("<Button-1>", lambda e: self._show_show_step())

        self._total_lbl = tk.Label(bottom, text="No seats selected",
                                   font=("Trebuchet MS", 9),
                                   bg=BG_MODAL, fg=TXT_GREY)
        self._total_lbl.pack(side="left", padx=16)

        self._confirm_btn = tk.Label(
            bottom, text="Confirm Booking →",
            font=("Trebuchet MS", 10, "bold"),
            bg=ACCENT_RED, fg=TXT_WHITE,
            padx=18, pady=8, cursor="hand2")
        self._confirm_btn.pack(side="right")
        self._confirm_btn.bind("<Button-1>", lambda e: self._confirm())
        self._confirm_btn.bind("<Enter>",
                               lambda e: self._confirm_btn.config(bg="#B01010"))
        self._confirm_btn.bind("<Leave>",
                               lambda e: self._confirm_btn.config(bg=ACCENT_RED))

    def _toggle_seat(self, seat_id: int, label: str, btn: tk.Label):
        already = any(sid == seat_id for sid, _ in self._selected_seats)
        if already:
            self._selected_seats = [
                (sid, lbl) for sid, lbl in self._selected_seats
                if sid != seat_id]
            btn.config(bg=BG_INPUT, fg=TXT_GREY)
        else:
            self._selected_seats.append((seat_id, label))
            btn.config(bg=ACCENT_RED, fg=TXT_WHITE)

        n = len(self._selected_seats)
        try:
            price = float(self._show.get("price", self._movie.get("price", 0)))
        except (TypeError, ValueError):
            price = 0.0
        total = n * price

        if n == 0:
            self._total_lbl.config(text="No seats selected", fg=TXT_GREY)
        else:
            self._total_lbl.config(
                text=f"{n} seat{'s' if n > 1 else ''}  •  Total: ₹{total:.0f}",
                fg=ACCENT_ORG)

    def _confirm(self):
        if not self._selected_seats:
            messagebox.showwarning(
                "No Seats", "Please select at least one seat.", parent=self)
            return

        seat_ids   = [sid for sid, _ in self._selected_seats]
        seat_lbls  = [lbl for _, lbl in self._selected_seats]
        try:
            price = float(self._show.get("price",
                          self._movie.get("price", 0)))
        except (TypeError, ValueError):
            price = 0.0
        total = len(seat_ids) * price

        # Filter out demo (negative) seat_ids before real DB save
        real_ids = [sid for sid in seat_ids if sid > 0]

        ok = messagebox.askyesno(
            "Confirm Booking",
            f"Movie   : {self._movie['title']}\n"
            f"Show    : {self._show.get('show_date', '')}  "
            f"{str(self._show.get('show_time', ''))[:5]}\n"
            f"Hall    : {self._show.get('hall', '—')}\n"
            f"Seats   : {', '.join(seat_lbls)}\n"
            f"Total   : ₹{total:.0f}\n\n"
            f"Proceed with booking?",
            parent=self)
        if not ok:
            return

        # Use real seat_ids if available, otherwise use demo ids (offline)
        ids_to_save = real_ids if real_ids else seat_ids

        saved = _save_booking(
            self._user["user_id"],
            self._show["show_id"],
            self._movie,
            ids_to_save,
            total,
            "cash",
        )
        if saved:
            messagebox.showinfo(
                "Booking Confirmed",
                f"✅  Booking confirmed!\n\n"
                f"{self._movie['title']}\n"
                f"Seats  : {', '.join(seat_lbls)}\n"
                f"Total  : ₹{total:.0f}",
                parent=self)
            if self._on_success:
                self._on_success()
            self.destroy()
        else:
            messagebox.showerror(
                "Error", "Booking failed. Please try again.", parent=self)


# ═══════════════════════════════════════════════════════
#  MODAL: MY BOOKINGS  (reads real DB data)
# ═══════════════════════════════════════════════════════
class BookingsModal(tk.Toplevel):
    def __init__(self, master, user: dict, on_refresh=None):
        super().__init__(master)
        self.title("My Bookings")
        self.geometry("900x560")
        self.resizable(False, False)
        self.configure(bg=BG_MODAL)
        self.grab_set()
        self.focus_force()
        self._user       = user
        self._on_refresh = on_refresh
        self._build()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg="#0F0A0A", height=54)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="📋  My Bookings",
                 font=("Georgia", 15, "bold"),
                 bg="#0F0A0A", fg=TXT_WHITE).pack(side="left", padx=20, pady=14)
        close = tk.Label(hdr, text="✕", font=("Trebuchet MS", 13),
                         bg="#0F0A0A", fg=TXT_MUTED, cursor="hand2")
        close.pack(side="right", padx=16)
        close.bind("<Button-1>", lambda e: self.destroy())

        # Column headers
        #  booking_id | movie_title | date | time | hall | seats | amount | status | action
        COLS = [
            ("#",       5),
            ("Movie",  22),
            ("Date",   12),
            ("Time",    8),
            ("Hall",   10),
            ("Seats",   6),
            ("Amount", 10),
            ("Status", 11),
            ("",       10),
        ]
        hdr_row = tk.Frame(self, bg="#1A1010", pady=6)
        hdr_row.pack(fill="x", padx=16)
        for txt, w in COLS:
            tk.Label(hdr_row, text=txt,
                     font=("Trebuchet MS", 8, "bold"),
                     bg="#1A1010", fg=TXT_MUTED,
                     width=w, anchor="w").pack(side="left", padx=4)

        tk.Frame(self, bg=SEP, height=1).pack(fill="x", padx=16)

        # Scrollable body
        canvas = tk.Canvas(self, bg=BG_MODAL, highlightthickness=0, bd=0)
        vsb    = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True, padx=16, pady=8)

        inner = tk.Frame(canvas, bg=BG_MODAL)
        cwin  = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(cwin, width=e.width))

        bookings = _fetch_user_bookings(self._user["user_id"])

        if not bookings:
            tk.Label(inner,
                     text="🎬  No bookings yet.\n"
                          "Head over to Book Ticket to get started!",
                     font=("Trebuchet MS", 11),
                     bg=BG_MODAL, fg=TXT_MUTED,
                     justify="center").pack(expand=True, pady=60)
            return

        for i, b in enumerate(bookings):
            row_bg = BG_CARD if i % 2 == 0 else BG_CARD2
            row    = tk.Frame(inner, bg=row_bg, pady=8)
            row.pack(fill="x", pady=1)

            status_str = str(b.get("status", "—")).lower()
            status_col = {
                "confirmed": ACCENT_GREEN,
                "cancelled": ACCENT_RED,
                "pending":   ACCENT_ORG,
            }.get(status_str, TXT_GREY)

            # Format date / time
            show_date = str(b.get("show_date") or "—")[:10]
            raw_time  = b.get("show_time")
            show_time = str(raw_time)[:5] if raw_time else "—"
            amount    = b.get("total_amount", "—")
            try:
                amount = f"₹{float(amount):.0f}"
            except (TypeError, ValueError):
                amount = f"₹{amount}"

            for txt, w in [
                (str(b.get("booking_id",    "—")),           5),
                (str(b.get("movie_title",   "Unknown"))[:20], 22),
                (show_date,                                   12),
                (show_time,                                    8),
                (str(b.get("hall",          "—"))[:9],        10),
                (str(b.get("total_seats",   "—")),             6),
                (amount,                                       10),
            ]:
                tk.Label(row, text=txt,
                         font=("Trebuchet MS", 9),
                         bg=row_bg, fg=TXT_WHITE,
                         width=w, anchor="w").pack(side="left", padx=4)

            tk.Label(row, text=status_str.capitalize(),
                     font=("Trebuchet MS", 9, "bold"),
                     bg=row_bg, fg=status_col,
                     width=11, anchor="w").pack(side="left", padx=4)

            if status_str == "confirmed":
                cancel_btn = tk.Label(row, text="Cancel",
                                      font=("Trebuchet MS", 8),
                                      bg=ACCENT_RED, fg=TXT_WHITE,
                                      padx=8, pady=3, cursor="hand2")
                cancel_btn.pack(side="left", padx=4)
                cancel_btn.bind("<Button-1>",
                                lambda e, bid=b["booking_id"]:
                                self._cancel(bid))
            else:
                tk.Label(row, text="—",
                         font=("Trebuchet MS", 9),
                         bg=row_bg, fg=TXT_MUTED,
                         width=10, anchor="w").pack(side="left", padx=4)

    def _cancel(self, booking_id: int):
        ok = messagebox.askyesno(
            "Cancel Booking",
            "Are you sure you want to cancel this booking?\n"
            "Your seats will be released.",
            parent=self)
        if not ok:
            return
        if _cancel_booking(booking_id):
            messagebox.showinfo(
                "Cancelled",
                "✅  Your booking has been cancelled and seats released.",
                parent=self)
            if self._on_refresh:
                self._on_refresh()
            self.destroy()
        else:
            messagebox.showerror(
                "Error", "Could not cancel. Please try again.", parent=self)


# ═══════════════════════════════════════════════════════
#  MODAL: RATE A MOVIE  (stores to ratings.score)
# ═══════════════════════════════════════════════════════
class RatingModal(tk.Toplevel):
    def __init__(self, master, user: dict, on_rated=None):
        super().__init__(master)
        self.title("Rate a Movie")
        self.geometry("600x620")
        self.resizable(False, False)
        self.configure(bg=BG_MODAL)
        self.grab_set()
        self.focus_force()
        self._user      = user
        self._on_rated  = on_rated
        self._scores    = {}      # movie_id → star count (1-5)
        self._reviews   = {}      # movie_id → StringVar
        self._star_lbls = {}      # movie_id → [Label × 5]
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg="#0F0A0A", height=54)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="⭐  Rate a Movie",
                 font=("Georgia", 15, "bold"),
                 bg="#0F0A0A", fg=TXT_WHITE).pack(side="left", padx=20, pady=14)
        close = tk.Label(hdr, text="✕", font=("Trebuchet MS", 13),
                         bg="#0F0A0A", fg=TXT_MUTED, cursor="hand2")
        close.pack(side="right", padx=16)
        close.bind("<Button-1>", lambda e: self.destroy())

        tk.Label(self,
                 text="Tap the stars to rate  •  Add a short review (optional)",
                 font=("Trebuchet MS", 9),
                 bg=BG_MODAL, fg=TXT_GREY).pack(pady=(10, 4))

        canvas = tk.Canvas(self, bg=BG_MODAL, highlightthickness=0, bd=0)
        vsb    = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True, padx=16, pady=4)

        inner = tk.Frame(canvas, bg=BG_MODAL)
        cwin  = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Fetch movies from DB (correct movie_ids for ratings table)
        movies = _fetch_movies_from_db()

        for m in movies:
            mid = m["id"]
            card = tk.Frame(inner, bg=BG_CARD,
                            highlightbackground=BORDER_DIM,
                            highlightthickness=1)
            card.pack(fill="x", pady=4, ipady=6, ipadx=10)

            # Left emoji
            tk.Label(card, text=m["emoji"],
                     font=("Segoe UI Emoji", 22),
                     bg=BG_CARD, padx=8).pack(side="left")

            # Middle info
            mid_f = tk.Frame(card, bg=BG_CARD)
            mid_f.pack(side="left", fill="x", expand=True)
            lang = m.get("lang") or m.get("language", "")
            tk.Label(mid_f, text=m["title"],
                     font=("Trebuchet MS", 10, "bold"),
                     bg=BG_CARD, fg=TXT_WHITE).pack(anchor="w")
            tk.Label(mid_f, text=f"{m['genre']}  •  {lang}",
                     font=("Trebuchet MS", 8),
                     bg=BG_CARD, fg=TXT_GREY).pack(anchor="w")

            # Review entry
            rv = tk.StringVar()
            self._reviews[mid] = rv
            rev_entry = tk.Entry(mid_f, textvariable=rv,
                                 font=("Trebuchet MS", 8),
                                 bg=BG_INPUT, fg=TXT_GREY,
                                 insertbackground=TXT_WHITE,
                                 relief="flat", bd=0,
                                 width=32)
            rev_entry.insert(0, "Write a review…")
            rev_entry.bind("<FocusIn>",
                           lambda e, w=rev_entry:
                           w.delete(0, "end") if w.get() == "Write a review…" else None)
            rev_entry.bind("<FocusOut>",
                           lambda e, w=rev_entry, v=rv:
                           w.insert(0, "Write a review…") if not v.get() else None)
            rev_entry.pack(anchor="w", pady=(3, 0))

            # Right star row
            star_row = tk.Frame(card, bg=BG_CARD)
            star_row.pack(side="right", padx=12)

            stars = []
            for s in range(1, 6):
                lbl = tk.Label(star_row, text="☆",
                               font=("Segoe UI Emoji", 18),
                               bg=BG_CARD, fg=TXT_MUTED, cursor="hand2")
                lbl.pack(side="left", padx=1)
                lbl.bind("<Button-1>",
                         lambda e, m_id=mid, sv=s: self._set_score(m_id, sv))
                lbl.bind("<Enter>",
                         lambda e, m_id=mid, sv=s: self._hover_stars(m_id, sv))
                lbl.bind("<Leave>",
                         lambda e, m_id=mid: self._refresh_stars(m_id))
                stars.append(lbl)

            self._star_lbls[mid] = stars
            self._scores[mid]    = 0

        # Submit button
        sub = tk.Label(self, text="Submit Ratings",
                       font=("Trebuchet MS", 11, "bold"),
                       bg=ACCENT_ORG, fg=BG_DARK,
                       padx=20, pady=10, cursor="hand2")
        sub.pack(pady=12)
        sub.bind("<Button-1>", self._submit)
        sub.bind("<Enter>", lambda e: sub.config(bg="#D08A10"))
        sub.bind("<Leave>", lambda e: sub.config(bg=ACCENT_ORG))

    def _hover_stars(self, movie_id: int, up_to: int):
        for i, lbl in enumerate(self._star_lbls[movie_id]):
            lbl.config(text="★" if i < up_to else "☆",
                       fg=ACCENT_ORG if i < up_to else TXT_MUTED)

    def _refresh_stars(self, movie_id: int):
        saved = self._scores.get(movie_id, 0)
        for i, lbl in enumerate(self._star_lbls[movie_id]):
            lbl.config(text="★" if i < saved else "☆",
                       fg=ACCENT_ORG if i < saved else TXT_MUTED)

    def _set_score(self, movie_id: int, stars: int):
        self._scores[movie_id] = stars
        self._refresh_stars(movie_id)

    def _submit(self, _=None):
        rated = {mid: sc for mid, sc in self._scores.items() if sc > 0}
        if not rated:
            messagebox.showwarning(
                "No Ratings",
                "Please rate at least one movie before submitting.",
                parent=self)
            return

        ok_all = True
        for mid, score in rated.items():
            rv_var = self._reviews.get(mid)
            review = rv_var.get() if rv_var else ""
            if review == "Write a review…":
                review = ""
            # Store in ratings table using `score` column
            if not _save_rating(self._user["user_id"], mid, score, review):
                ok_all = False

        if ok_all:
            messagebox.showinfo(
                "Ratings Saved",
                f"✅  {len(rated)} rating(s) saved successfully!\n"
                f"Thank you for your feedback.",
                parent=self)
        else:
            messagebox.showwarning(
                "Partial Save",
                "Some ratings could not be saved. Please try again.",
                parent=self)

        if self._on_rated:
            self._on_rated()
        self.destroy()


# ═══════════════════════════════════════════════════════
#  DASHBOARD PAGE
# ═══════════════════════════════════════════════════════
class DashboardPage(tk.Frame):
    """
    Main dashboard.

    Parameters
    ----------
    user      : dict — DB user row
    prefs     : dict — ML preferences from onboarding
    on_logout : callable
    on_book   : callable(movie_dict)
    on_nav    : callable(key: str)
    """

    def __init__(self, master, user: dict, prefs: dict = None,
                 on_logout=None, on_book=None, on_nav=None, **kw):
        super().__init__(master, bg=BG_DARK, **kw)
        self._user      = user
        self._prefs     = prefs or {}
        self._on_logout = on_logout
        self._on_book   = on_book
        self._on_nav    = on_nav
        self._stats     = _fetch_user_stats(user.get("user_id", 0))
        self._build()

    def _build(self):
        self._sidebar_frame = tk.Frame(self, bg=BG_SIDEBAR, width=220)
        self._sidebar_frame.pack(side="left", fill="y")
        self._sidebar_frame.pack_propagate(False)
        self._build_sidebar()

        right = tk.Frame(self, bg=BG_DARK)
        right.pack(side="left", fill="both", expand=True)
        self._build_right(right)

    def _build_sidebar(self):
        s = self._sidebar_frame

        # Logo
        logo = tk.Frame(s, bg="#0D0808", height=58)
        logo.pack(fill="x")
        logo.pack_propagate(False)
        tk.Label(logo, text="🎬", font=("Segoe UI Emoji", 22),
                 bg="#0D0808", fg=ACCENT_RED).pack(side="left", padx=(14, 4))
        lw = tk.Frame(logo, bg="#0D0808")
        lw.pack(side="left")
        tk.Label(lw, text="Smart Movie",
                 font=("Georgia", 11, "bold"),
                 bg="#0D0808", fg=TXT_WHITE).pack(anchor="w")
        tk.Label(lw, text="TICKET SYSTEM",
                 font=("Trebuchet MS", 6),
                 bg="#0D0808", fg=TXT_GREY).pack(anchor="w")

        tk.Frame(s, bg=SEP, height=1).pack(fill="x")

        # User avatar
        av = tk.Frame(s, bg=BG_SIDEBAR, pady=12)
        av.pack(fill="x")
        initials = "".join(w[0].upper()
                           for w in self._user.get("full_name", "U").split()[:2])
        tk.Label(av, text=initials,
                 font=("Georgia", 13, "bold"),
                 bg=ACCENT_RED, fg=TXT_WHITE,
                 width=3, height=1).pack()
        tk.Label(av, text=self._user.get("full_name", "User"),
                 font=("Trebuchet MS", 9, "bold"),
                 bg=BG_SIDEBAR, fg=TXT_WHITE).pack(pady=(4, 0))
        tk.Label(av, text=self._user.get("email", ""),
                 font=("Trebuchet MS", 7),
                 bg=BG_SIDEBAR, fg=TXT_GREY,
                 wraplength=200).pack()

        tk.Frame(s, bg=SEP, height=1).pack(fill="x", pady=(8, 4))

        # Nav items
        for icon, label, accent, key in SIDEBAR_ITEMS:
            sidebar_btn(s, icon, label, accent, key, on_click=self._nav)

        tk.Frame(s, bg=SEP, height=1).pack(fill="x", pady=(8, 4))

        # Seat availability panel
        tk.Label(s, text="🪑  Seat Availability",
                 font=("Trebuchet MS", 8, "bold"),
                 bg=BG_SIDEBAR, fg=TXT_GREY).pack(anchor="w", padx=14, pady=(4, 2))

        seat_frame = tk.Frame(s, bg=BG_SIDEBAR)
        seat_frame.pack(fill="x", padx=10, pady=(0, 6))

        movies = _fetch_movies_from_db()
        for m in movies[:8]:   # limit sidebar to 8 movies
            row = tk.Frame(seat_frame, bg=BG_SIDEBAR, cursor="hand2")
            row.pack(fill="x", pady=1)
            tk.Label(row, text=m["emoji"],
                     font=("Segoe UI Emoji", 11),
                     bg=BG_SIDEBAR).pack(side="left", padx=(0, 4))
            short = (m["title"][:14] + "…") if len(m["title"]) > 14 else m["title"]
            tk.Label(row, text=short,
                     font=("Trebuchet MS", 8),
                     bg=BG_SIDEBAR, fg=TXT_GREY,
                     anchor="w").pack(side="left", fill="x", expand=True)
            sc = _seat_color(m.get("seats", 30))
            tk.Label(row, text=str(m.get("seats", "—")),
                     font=("Trebuchet MS", 8, "bold"),
                     bg=BG_SIDEBAR, fg=sc,
                     width=3, anchor="e").pack(side="right")

            for w in [row] + list(row.winfo_children()):
                w.bind("<Button-1>", lambda e, mv=m: self._open_booking(mv))
                w.bind("<Enter>",    lambda e, w=row: w.config(bg=_darken(BG_CARD, 1.3)))
                w.bind("<Leave>",    lambda e, w=row: w.config(bg=BG_SIDEBAR))

        # Logout
        tk.Frame(s, bg=SEP, height=1).pack(fill="x", side="bottom", pady=4)
        logout = tk.Label(s, text="⬅  Logout",
                          font=("Trebuchet MS", 9),
                          bg=BG_SIDEBAR, fg=TXT_MUTED,
                          cursor="hand2", pady=10)
        logout.pack(side="bottom", fill="x", padx=16)
        logout.bind("<Enter>",    lambda e: logout.config(fg=ACCENT_RED))
        logout.bind("<Leave>",    lambda e: logout.config(fg=TXT_MUTED))
        logout.bind("<Button-1>",
                    lambda e: self._on_logout() if self._on_logout else None)

    def _build_right(self, parent):
        canvas = tk.Canvas(parent, bg=BG_DARK,
                           highlightthickness=0, bd=0)
        vsb = ttk.Scrollbar(parent, orient="vertical",
                            command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=BG_DARK)
        win   = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win, width=e.width))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(
                            -1 if e.delta > 0 else 1, "units"))

        self._build_topbar(inner)
        self._build_hero_banner(inner)
        self._build_stats(inner)
        self._build_recommendations(inner)
        self._build_now_showing(inner)
        self._build_ticker(inner)
        self._build_footer(inner)

    def _build_topbar(self, parent):
        bar = tk.Frame(parent, bg=BG_NAV, height=52)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        hour   = time.localtime().tm_hour
        period = ("Good Morning" if hour < 12 else
                  "Good Afternoon" if hour < 18 else "Good Evening")
        name   = self._user.get("full_name", "").split()[0]
        tk.Label(bar, text=f"{period}, {name}!  👋",
                 font=("Georgia", 13, "bold"),
                 bg=BG_NAV, fg=TXT_WHITE).pack(side="left", padx=22)
        right = tk.Frame(bar, bg=BG_NAV)
        right.pack(side="right", padx=18)
        tk.Label(right, text=time.strftime("%a, %d %b %Y"),
                 font=("Trebuchet MS", 8),
                 bg=BG_NAV, fg=TXT_GREY).pack(side="right", padx=(12, 0))
        tk.Label(right, text="🔔",
                 font=("Segoe UI Emoji", 14),
                 bg=BG_NAV, fg=ACCENT_ORG, cursor="hand2").pack(side="right", padx=8)

    def _build_hero_banner(self, parent):
        hero = tk.Frame(parent, bg="#1A0C08", height=155)
        hero.pack(fill="x")
        hero.pack_propagate(False)
        pc = ParticleCanvas(hero, bg="#1A0C08", highlightthickness=0, bd=0)
        pc.place(x=0, y=0, relwidth=1, relheight=1)
        ov = tk.Frame(hero, bg="#0D0605")
        ov.place(relx=0, rely=0, relwidth=0.62, relheight=1)
        ct = tk.Frame(hero, bg="#0D0605")
        ct.place(x=28, rely=0.08, relheight=0.84, width=530)
        genres = self._prefs.get("genres", [])
        sub    = (f"Based on your love of {', '.join(genres[:3])}"
                  if genres else "Explore today's top picks")
        tk.Label(ct, text=f"Welcome back, {self._user.get('full_name', 'User')}!",
                 font=("Georgia", 18, "bold"),
                 bg="#0D0605", fg=TXT_WHITE).pack(anchor="w", padx=18, pady=(16, 0))
        tk.Label(ct, text=sub,
                 font=("Trebuchet MS", 9),
                 bg="#0D0605", fg=ACCENT_ORG).pack(anchor="w", padx=18, pady=(3, 10))
        btn_row = tk.Frame(ct, bg="#0D0605")
        btn_row.pack(anchor="w", padx=18)
        for txt, col, action in [
            ("🎟  Book Tickets", ACCENT_RED,  "book"),
            ("📋  My Bookings",  ACCENT_BLUE, "bookings"),
            ("⭐  Rate Movie",   ACCENT_ORG,  "rate"),
        ]:
            b = tk.Label(btn_row, text=txt,
                         font=("Trebuchet MS", 9, "bold"),
                         bg=col, fg=TXT_WHITE,
                         padx=12, pady=5, cursor="hand2")
            b.pack(side="left", padx=(0, 8))
            b.bind("<Button-1>", lambda e, k=action: self._nav(k))
            b.bind("<Enter>",    lambda e, w=b, c=col: w.config(bg=_darken(c, 0.75)))
            b.bind("<Leave>",    lambda e, w=b, c=col: w.config(bg=c))
        tk.Label(hero, text="🎥\n🍿\n🎞",
                 font=("Segoe UI Emoji", 34),
                 bg="#1A0C08").place(relx=0.80, rely=0.05,
                                    relwidth=0.16, relheight=0.9)

    def _build_stats(self, parent):
        sec = tk.Frame(parent, bg=BG_DARK, pady=14)
        sec.pack(fill="x", padx=24)
        row = tk.Frame(sec, bg=BG_DARK)
        row.pack(anchor="w")
        stat_chip(row, "🎟", self._stats["booked"],    "Tickets Booked", ACCENT_RED)
        stat_chip(row, "🎬", self._stats["watched"],   "Confirmed Shows", ACCENT_BLUE)
        stat_chip(row, "⭐", self._stats["avg_rating"], "Avg Score",      ACCENT_ORG)
        stat_chip(row, "💳", f"₹{self._stats['spent']}", "Total Spent",  ACCENT_PURP)

    def _get_ml_recs(self, n=5):
        try:
            _ml_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ml")
            _ml_alt = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ml")
            for _p in [_ml_dir, _ml_alt]:
                if os.path.isdir(_p) and _p not in sys.path:
                    sys.path.insert(0, _p)
            from recommender import get_recommendations
            result = get_recommendations(
                user_prefs=self._prefs,
                user_id=self._user.get("user_id"),
                n=n)
            return result
        except Exception as exc:
            print(f"[DASH-ML] Falling back to rule-based: {exc}")
            genres = self._prefs.get("genres", [])
            langs  = self._prefs.get("languages", [])
            movies = _fetch_movies_from_db()
            reco = [m for m in movies
                    if m["genre"] in genres or m.get("lang", m.get("language", "")) in langs]
            return (reco or movies)[:n]

    @staticmethod
    def _ml_badge_color(confidence: str) -> str:
        return {"High": ACCENT_GREEN, "Medium": ACCENT_ORG,
                "Low": ACCENT_BLUE}.get(confidence, TXT_MUTED)

    def _build_recommendations(self, parent):
        genres = self._prefs.get("genres", [])
        reco   = self._get_ml_recs(n=5)

        sec = tk.Frame(parent, bg=BG_DARK, pady=8)
        sec.pack(fill="x", padx=24)

        hdr = tk.Frame(sec, bg=BG_DARK)
        hdr.pack(fill="x", pady=(0, 8))
        tk.Label(hdr, text="🤖  Recommended For You",
                 font=("Georgia", 14, "bold"),
                 bg=BG_DARK, fg=TXT_WHITE).pack(side="left")
        tk.Label(hdr, text="  ·  Powered by ML",
                 font=("Trebuchet MS", 8),
                 bg=BG_DARK, fg=ACCENT_PURP).pack(side="left")
        legend = tk.Frame(hdr, bg=BG_DARK)
        legend.pack(side="right")
        for lbl_t, col in [("● High", ACCENT_GREEN),
                            ("● Medium", ACCENT_ORG),
                            ("● Low", ACCENT_BLUE)]:
            tk.Label(legend, text=lbl_t, font=("Trebuchet MS", 7),
                     bg=BG_DARK, fg=col).pack(side="left", padx=4)
        if genres:
            tk.Label(hdr, text=f"Based on: {', '.join(genres[:3])}",
                     font=("Trebuchet MS", 8),
                     bg=BG_DARK, fg=TXT_GREY).pack(side="right", padx=(0, 12))

        row = tk.Frame(sec, bg=BG_DARK)
        row.pack(anchor="w")
        for i, m in enumerate(reco):
            confidence = m.get("ml_confidence", "")
            ml_score   = m.get("ml_score", 0.0)
            ml_reason  = m.get("ml_reason", "")
            badge = (f"🎯 {confidence} Match" if confidence
                     else ("🎯 Top Pick" if i == 0 else None))

            card = movie_card(row, m, on_book=self._open_booking,
                              width=210, height=268, badge=badge)
            card.pack(side="left", padx=(0, 10))

            if ml_score:
                bar_frame = tk.Frame(card, bg=BG_CARD2, height=5)
                bar_frame.pack(fill="x", side="bottom")
                bar_col  = self._ml_badge_color(confidence)
                fill_pct = max(0.05, min(1.0, ml_score))
                tk.Frame(bar_frame, bg=bar_col, height=5,
                         width=int(fill_pct * 206)).pack(side="left")

            if ml_reason:
                tk.Label(card,
                         text=ml_reason,
                         font=("Trebuchet MS", 6),
                         bg=_darken(m.get("color", "#2A2020"), 0.5),
                         fg=TXT_GREY,
                         wraplength=198, justify="center",
                         pady=3).pack(fill="x", side="bottom")

    def _build_now_showing(self, parent):
        sec = tk.Frame(parent, bg=BG_DARK, pady=8)
        sec.pack(fill="x", padx=24)

        hdr = tk.Frame(sec, bg=BG_DARK)
        hdr.pack(fill="x", pady=(0, 8))
        tk.Label(hdr, text="🎬  Now Showing",
                 font=("Georgia", 14, "bold"),
                 bg=BG_DARK, fg=TXT_WHITE).pack(side="left")
        tk.Label(hdr, text="All Movies in Theatre Today",
                 font=("Trebuchet MS", 8),
                 bg=BG_DARK, fg=TXT_GREY).pack(side="right")

        row    = tk.Frame(sec, bg=BG_DARK)
        row.pack(anchor="w")
        movies = _fetch_movies_from_db()
        for m in movies:
            card = movie_card(row, m, on_book=self._open_booking,
                              width=196, height=258)
            card.pack(side="left", padx=(0, 10))

    def _build_ticker(self, parent):
        bar = tk.Frame(parent, bg="#0A0604", height=28)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        tk.Label(bar, text=" 🔜 COMING SOON ",
                 font=("Trebuchet MS", 7, "bold"),
                 bg=ACCENT_RED, fg=TXT_WHITE).pack(side="left")
        ticker = MarqueeTicker(bar, UPCOMING, bg="#0A0604", height=28)
        ticker.pack(side="left", fill="both", expand=True)
        self._ticker = ticker

    def _build_footer(self, parent):
        ft = tk.Frame(parent, bg="#080606", pady=12)
        ft.pack(fill="x")
        tk.Label(ft,
                 text="© 2026 Smart Movie Ticket Management System  •  All rights reserved",
                 font=("Trebuchet MS", 8),
                 bg="#080606", fg="#5A4A4A").pack()

    # ── Navigation ────────────────────────────────────────────────────────────
    def _nav(self, key: str):
        if key == "book":
            self._open_booking(None)
        elif key == "bookings":
            self._open_my_bookings()
        elif key == "rate":
            self._open_rate_movie()
        elif key in ("profile", "settings"):
            if self._on_nav:
                self._on_nav(key)
            else:
                self._flash(f"🔜  {key.capitalize()} page — coming soon!")
        else:
            if self._on_nav:
                self._on_nav(key)

    def _open_booking(self, movie=None):
        BookingModal(self, user=self._user,
                     preselect_movie=movie,
                     on_success=self._refresh_stats)
        if self._on_book and movie:
            self._on_book(movie)

    def _open_my_bookings(self):
        BookingsModal(self, user=self._user,
                      on_refresh=self._refresh_stats)

    def _open_rate_movie(self):
        RatingModal(self, user=self._user,
                    on_rated=self._refresh_stats)

    def _refresh_stats(self):
        self._stats = _fetch_user_stats(self._user.get("user_id", 0))

    def _flash(self, msg: str, ms: int = 2000):
        toast = tk.Toplevel(self)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        toast.configure(bg=ACCENT_RED)
        tk.Label(toast, text=msg,
                 font=("Trebuchet MS", 10, "bold"),
                 bg=ACCENT_RED, fg=TXT_WHITE,
                 padx=22, pady=12).pack()
        self.update_idletasks()
        x = self.winfo_rootx() + self.winfo_width()  // 2 - 180
        y = self.winfo_rooty() + self.winfo_height() // 2 - 30
        toast.geometry(f"+{x}+{y}")
        toast.after(ms, toast.destroy)

    def destroy(self):
        if hasattr(self, "_ticker"):
            self._ticker.stop()
        super().destroy()


# ─────────────────────────────────────────────
#  STANDALONE TEST
# ─────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Dashboard — Smart Movie")
    root.geometry("1280x800")
    root.minsize(1000, 640)
    root.configure(bg=BG_DARK)
    ttk.Style(root).theme_use("clam")

    demo_user  = {"user_id": 1, "full_name": "Roshan Thokal",
                  "email": "thokalroshan2@gmail.com"}
    demo_prefs = {"genres":    ["Action", "Sci-Fi", "Thriller"],
                  "languages": ["English", "Hindi"],
                  "vibes":     ["Thrills & Chills"],
                  "show_time": "Night (8PM–12AM)",
                  "frequency": "2–3 times/week",
                  "age_group": "18–25"}

    page = DashboardPage(root,
                         user=demo_user,
                         prefs=demo_prefs,
                         on_logout=root.destroy)
    page.pack(fill="both", expand=True)
    root.mainloop()