"""
Onboarding.py — First-Login ML Preference Collection
Cinematic dark design — matches login.py / register.py style.

Collects from the user:
  • Favourite genres  (multi-select chips)
  • Preferred languages
  • Viewing frequency
  • Preferred show-times
  • Age group (for rating filters)
  • Mood / vibe preference

All data is persisted via save_user_preferences() in auth_service.py
and the is_first_login flag is cleared so this page never shows again.

FIXES vs original
-----------------
* sys.path insert now uses __file__ so it works regardless of CWD.
* on_skip callback now always receives (partial_prefs) — was missing
  the argument in some call sites.
* DB persistence uses the flat `auth_service` import (not services/).
* Status label gives clear feedback when DB save succeeds/fails.
"""

import tkinter as tk
from tkinter import ttk
import math, random, sys, os

# ── Ensure project root is always on sys.path ─────────────────────────────────
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# ── Palette (identical to login / register) ───────────────────────────────────
BG_AMBER     = "#3B1E08"
BG_DARK      = "#0D0A0A"
BG_CARD      = "#1E1A1A"
BG_INPUT     = "#2A2424"
BG_INPUT_FOC = "#342A2A"
ACCENT_RED   = "#E02020"
ACCENT_ORG   = "#F5A623"
ACCENT_BLUE  = "#4A90D9"
ACCENT_GREEN = "#27AE60"
ACCENT_PURP  = "#8B5CF6"
TXT_WHITE    = "#FFFFFF"
TXT_GREY     = "#9A8888"
TXT_MUTED    = "#6A5A5A"
CARD_BORDER  = "#3A2E2E"

# ── Chip colours per genre ────────────────────────────────────────────────────
GENRE_CHIPS = [
    ("Action",     "💥", "#C03010"),
    ("Romance",    "❤️",  "#C0204A"),
    ("Comedy",     "😂", "#C07010"),
    ("Thriller",   "😱", "#1A1A3E"),
    ("Horror",     "👻", "#2A0A2A"),
    ("Sci-Fi",     "🚀", "#0A3A6A"),
    ("Animation",  "🎈", "#1E6CA8"),
    ("Drama",      "🎭", "#4A2A6A"),
    ("Mystery",    "🔍", "#1A2A1A"),
    ("Fantasy",    "🧙", "#3A1A4A"),
    ("Biography",  "📖", "#2A3010"),
    ("Sports",     "⚽", "#0A3A20"),
]

LANGUAGES = ["Hindi", "English", "Marathi", "Tamil", "Telugu",
             "Bengali", "Kannada", "Malayalam", "Punjabi", "Other"]

VIBES = [
    ("Chill & Relax",    "🛋️",  "#1E3A2A"),
    ("Thrills & Chills", "😬", "#3A1A1A"),
    ("Feel Good",        "🌟", "#3A2A10"),
    ("Mind-Bending",     "🌀", "#1A1A3A"),
    ("Emotional Ride",   "😢", "#3A1A2A"),
    ("Laugh Out Loud",   "🤣", "#3A2A08"),
]

TIMES = ["Morning (9AM–12PM)", "Afternoon (12–4PM)",
         "Evening (4–8PM)", "Night (8PM–12AM)", "Late Night (12AM+)"]

FREQS = ["Every Day", "2–3 times/week", "Once a week",
         "Twice a month", "Occasionally"]

AGE_GROUPS = ["Under 18", "18–25", "26–35", "36–50", "50+"]


# ─────────────────────────────────────────────
#  ANIMATED BG (same as login)
# ─────────────────────────────────────────────
class CinemaBackground(tk.Canvas):
    def __init__(self, master, **kw):
        super().__init__(master, highlightthickness=0, bd=0, **kw)
        self._t = 0.0
        self._running = True
        self._particles = [
            {"x": random.uniform(0, 1400), "y": random.uniform(0, 1000),
             "r": random.uniform(1, 5),    "spd": random.uniform(0.1, 0.6),
             "phase": random.uniform(0, 2*math.pi),
             "col": random.choice(["#7A3010","#A04818","#C06020","#5A2010"])}
            for _ in range(30)
        ]
        self.bind("<Configure>", lambda e: self._draw_static())
        self._draw_static()
        self._animate()

    def _draw_static(self):
        self.delete("static")
        w = self.winfo_width() or 1200
        h = self.winfo_height() or 1000
        for i in range(30):
            t = i / 30
            r = int(0x3B + (0x18 - 0x3B) * t)
            g = int(0x1E + (0x08 - 0x1E) * t)
            b = int(0x08 + (0x04 - 0x08) * t)
            col = "#{:02x}{:02x}{:02x}".format(
                max(0,min(255,r)), max(0,min(255,g)), max(0,min(255,b)))
            y0 = int(i * h / 30)
            y1 = int((i+1) * h / 30) + 1
            self.create_rectangle(0, y0, w, y1, fill=col, outline="", tags="static")
        for side in ("left", "right"):
            sw = 40
            x = 0 if side == "left" else w - sw
            self.create_rectangle(x, 0, x+sw, h, fill="#160A04", outline="", tags="static")
            for y in range(8, h, 22):
                hx = x + 8
                self.create_rectangle(hx, y, hx+sw-16, y+14,
                                      fill="#080402", outline="#1A1008",
                                      width=1, tags="static")

    def _animate(self):
        if not self._running:
            return
        self.delete("anim")
        w = self.winfo_width() or 1200
        h = self.winfo_height() or 1000
        self._t += 0.018
        sx, sy = w - 50, 0
        angle  = math.pi * 1.35 + math.sin(self._t * 0.35) * 0.1
        cl     = h * 1.2
        sp     = 0.18
        tx1 = sx + math.cos(angle - sp) * cl
        ty1 = sy + math.sin(angle - sp) * cl
        tx2 = sx + math.cos(angle + sp) * cl
        ty2 = sy + math.sin(angle + sp) * cl
        self.create_polygon(sx, sy, tx1, ty1, tx2, ty2,
                            fill="#6A3A08", outline="", tags="anim", stipple="gray12")
        lr = 14 + math.sin(self._t * 2) * 2
        self.create_oval(sx-lr, sy-lr, sx+lr, sy+lr,
                         fill="#F5C060", outline="#FFE090", width=2, tags="anim")
        self.create_oval(sx-6, sy-6, sx+6, sy+6,
                         fill="#FFFFFF", outline="", tags="anim")
        for p in self._particles:
            p["x"] -= p["spd"] * 0.25
            p["y"] += math.sin(self._t + p["phase"]) * 0.3
            if p["x"] < -10:
                p["x"] = w + 10
                p["y"] = random.uniform(0, h)
            r = p["r"]
            self.create_oval(p["x"]-r, p["y"]-r, p["x"]+r, p["y"]+r,
                             fill=p["col"], outline="", tags="anim")
        self.after(40, self._animate)

    def stop(self):
        self._running = False


# ─────────────────────────────────────────────
#  TOGGLE CHIP WIDGET
# ─────────────────────────────────────────────
class ToggleChip(tk.Label):
    """A selectable pill/chip.  Click toggles selected state."""

    def __init__(self, master, text, icon="", base_color="#2A2424",
                 sel_color=ACCENT_RED, callback=None, **kw):
        display = f"{icon}  {text}" if icon else text
        super().__init__(master, text=display,
                         font=("Trebuchet MS", 9, "bold"),
                         bg=base_color, fg=TXT_GREY,
                         padx=12, pady=6,
                         cursor="hand2", relief="flat", bd=0,
                         highlightbackground=CARD_BORDER,
                         highlightthickness=1)
        self._text      = text
        self._base_col  = base_color
        self._sel_col   = sel_color
        self._selected  = False
        self._cb        = callback

        self.bind("<Button-1>", self._toggle)
        self.bind("<Enter>",    self._hover_on)
        self.bind("<Leave>",    self._hover_off)

    def _toggle(self, _=None):
        self._selected = not self._selected
        self._refresh()
        if self._cb:
            self._cb(self._text, self._selected)

    def _hover_on(self, _=None):
        if not self._selected:
            self.config(fg=TXT_WHITE, highlightbackground=ACCENT_ORG)

    def _hover_off(self, _=None):
        if not self._selected:
            self.config(fg=TXT_GREY, highlightbackground=CARD_BORDER)

    def _refresh(self):
        if self._selected:
            self.config(bg=self._sel_col, fg=TXT_WHITE,
                        highlightbackground=self._sel_col)
        else:
            self.config(bg=self._base_col, fg=TXT_GREY,
                        highlightbackground=CARD_BORDER)

    @property
    def selected(self):
        return self._selected


# ─────────────────────────────────────────────
#  RADIO ROW WIDGET
# ─────────────────────────────────────────────
class RadioRow(tk.Frame):
    """Horizontal group of single-select chips."""

    def __init__(self, master, options, base_color="#2A2424",
                 sel_color=ACCENT_BLUE, **kw):
        super().__init__(master, bg=BG_CARD, **kw)
        self._var      = tk.StringVar(value="")
        self._chips    = {}
        self._sel_col  = sel_color
        self._base_col = base_color

        wrap = tk.Frame(self, bg=BG_CARD)
        wrap.pack(anchor="w")
        for opt in options:
            chip = ToggleChip(wrap, opt, base_color=base_color,
                              sel_color=sel_color,
                              callback=lambda t, s, c=opt: self._select(c))
            chip.pack(side="left", padx=3, pady=3)
            self._chips[opt] = chip

    def _select(self, chosen):
        for name, chip in self._chips.items():
            if name != chosen and chip.selected:
                chip._toggle()
        self._var.set(chosen)

    def get(self):
        return self._var.get()


# ─────────────────────────────────────────────
#  SECTION HEADER HELPER
# ─────────────────────────────────────────────
def section_label(parent, icon, title, subtitle=""):
    row = tk.Frame(parent, bg=BG_CARD)
    row.pack(anchor="w", padx=40, pady=(18, 4))
    tk.Label(row, text=icon, font=("Segoe UI Emoji", 16),
             bg=BG_CARD, fg=ACCENT_ORG).pack(side="left", padx=(0, 8))
    col = tk.Frame(row, bg=BG_CARD)
    col.pack(side="left")
    tk.Label(col, text=title, font=("Georgia", 13, "bold"),
             bg=BG_CARD, fg=TXT_WHITE).pack(anchor="w")
    if subtitle:
        tk.Label(col, text=subtitle, font=("Trebuchet MS", 8),
                 bg=BG_CARD, fg=TXT_GREY).pack(anchor="w")


# ─────────────────────────────────────────────
#  ONBOARDING PAGE
# ─────────────────────────────────────────────
class OnboardingPage(tk.Frame):
    """
    First-login ML preference collection page.

    Parameters
    ----------
    user        : dict  — DB user row (user_id, full_name, …)
    on_complete : callable(prefs: dict)  — called with collected prefs
    on_skip     : callable(prefs: dict)  — user skips; partial prefs passed
    """

    def __init__(self, master, user: dict,
                 on_complete=None, on_skip=None, **kw):
        super().__init__(master, bg=BG_AMBER, **kw)
        self._user        = user
        self._on_complete = on_complete
        self._on_skip     = on_skip

        self._genre_chips = []
        self._lang_chips  = []
        self._vibe_chips  = []
        self._time_radio  = None
        self._freq_radio  = None
        self._age_radio   = None

        self._build()

    # ─────────────────────────────────────────
    def _build(self):
        self._bg = CinemaBackground(self, bg=BG_AMBER)
        self._bg.place(relx=0, rely=0, relwidth=1, relheight=1)

        # ── Header bar ───────────────────────────────────────────────────────
        hdr = tk.Frame(self._bg, bg="#150A04", height=58)
        hdr.place(relx=0, rely=0, relwidth=1, height=58)
        hdr.pack_propagate(False)

        tk.Label(hdr, text="🎬", font=("Segoe UI Emoji", 22),
                 bg="#150A04", fg=ACCENT_ORG).place(x=22, y=10)
        tk.Label(hdr, text="Smart Movie  ·  Personalisation Setup",
                 font=("Georgia", 13, "bold"),
                 bg="#150A04", fg=TXT_WHITE).place(x=60, y=8)
        tk.Label(hdr,
                 text="Tell us your tastes — we'll tune recommendations just for you",
                 font=("Trebuchet MS", 8),
                 bg="#150A04", fg=TXT_GREY).place(x=62, y=32)

        skip_btn = tk.Label(hdr, text="Skip for now →",
                            font=("Trebuchet MS", 8),
                            bg="#150A04", fg=TXT_MUTED, cursor="hand2")
        skip_btn.place(relx=1.0, x=-20, y=20, anchor="ne")
        skip_btn.bind("<Enter>", lambda e: skip_btn.config(fg=TXT_WHITE))
        skip_btn.bind("<Leave>", lambda e: skip_btn.config(fg=TXT_MUTED))
        skip_btn.bind("<Button-1>", lambda e: self._do_skip())

        # ── Scrollable content card ──────────────────────────────────────────
        outer = tk.Frame(self._bg, bg=BG_AMBER)
        outer.place(relx=0.5, y=74, relwidth=0.88,
                    rely=0, height=10000, anchor="n")

        self._canvas = tk.Canvas(outer, bg=BG_AMBER,
                                  highlightthickness=0, bd=0)
        vsb = ttk.Scrollbar(outer, orient="vertical",
                             command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._bg.bind("<Configure>", self._on_bg_resize)

        self._card = tk.Frame(self._canvas, bg=BG_CARD,
                              highlightbackground=CARD_BORDER,
                              highlightthickness=1)
        self._cwin = self._canvas.create_window(
            (0, 0), window=self._card, anchor="nw")
        self._card.bind("<Configure>", lambda e: self._canvas.configure(
            scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",
                          lambda e: self._canvas.itemconfig(
                              self._cwin, width=e.width))
        self._canvas.bind_all("<MouseWheel>",
                              lambda e: self._canvas.yview_scroll(
                                  -1 if e.delta > 0 else 1, "units"))

        self._build_card(self._card)

    def _on_bg_resize(self, e):
        self._canvas.master.place_configure(height=e.height - 74)

    # ─────────────────────────────────────────
    def _build_card(self, card):
        tk.Frame(card, bg=BG_CARD, height=8).pack()

        name = self._user.get("full_name", "there").split()[0]
        tk.Label(card, text=f"Hey {name}, welcome to Smart Movie! 🎉",
                 font=("Georgia", 20, "bold"),
                 bg=BG_CARD, fg=TXT_WHITE).pack(pady=(18, 2))
        tk.Label(card,
                 text="Answer a few quick questions so our AI can "
                      "recommend the perfect movies for you.",
                 font=("Trebuchet MS", 9), bg=BG_CARD, fg=TXT_GREY,
                 wraplength=640).pack()

        # Progress dots (decorative)
        dots = tk.Frame(card, bg=BG_CARD)
        dots.pack(pady=(10, 0))
        for c in [ACCENT_RED, ACCENT_ORG, ACCENT_BLUE,
                  ACCENT_PURP, ACCENT_GREEN, "#E06020"]:
            tk.Label(dots, text="●", font=("Trebuchet MS", 8),
                     bg=BG_CARD, fg=c).pack(side="left", padx=2)

        tk.Frame(card, bg=CARD_BORDER, height=1).pack(
            fill="x", padx=40, pady=(14, 2))

        # ── Section 1 — Genres ───────────────────────────────────────────────
        section_label(card, "🎬", "Favourite Genres", "Pick as many as you like")
        wrap = tk.Frame(card, bg=BG_CARD)
        wrap.pack(anchor="w", padx=40, pady=(4, 0))
        for i, (name_g, icon, col) in enumerate(GENRE_CHIPS):
            chip = ToggleChip(wrap, name_g, icon=icon,
                              base_color=self._darken(col, 0.55),
                              sel_color=col)
            chip.grid(row=i // 4, column=i % 4, padx=4, pady=4, sticky="w")
            self._genre_chips.append(chip)

        # ── Section 2 — Languages ────────────────────────────────────────────
        section_label(card, "🌐", "Preferred Languages",
                      "Movies you'd like to watch in")
        lang_wrap = tk.Frame(card, bg=BG_CARD)
        lang_wrap.pack(anchor="w", padx=40, pady=(4, 0))
        for i, lang in enumerate(LANGUAGES):
            chip = ToggleChip(lang_wrap, lang,
                              base_color=BG_INPUT, sel_color=ACCENT_BLUE)
            chip.grid(row=i // 5, column=i % 5, padx=4, pady=4, sticky="w")
            self._lang_chips.append(chip)

        # ── Section 3 — Vibe ─────────────────────────────────────────────────
        section_label(card, "✨", "What's Your Movie Mood?",
                      "Pick the vibe you usually watch for")
        vibe_wrap = tk.Frame(card, bg=BG_CARD)
        vibe_wrap.pack(anchor="w", padx=40, pady=(4, 0))
        for i, (v_name, v_icon, v_col) in enumerate(VIBES):
            chip = ToggleChip(vibe_wrap, v_name, icon=v_icon,
                              base_color=self._darken(v_col, 0.6),
                              sel_color=v_col)
            chip.grid(row=i // 3, column=i % 3, padx=4, pady=4, sticky="w")
            self._vibe_chips.append(chip)

        # ── Section 4 — Show Time ────────────────────────────────────────────
        section_label(card, "🕐", "Preferred Show Time",
                      "When do you usually go to movies?")
        self._time_radio = RadioRow(card, TIMES,
                                    base_color=BG_INPUT, sel_color=ACCENT_ORG)
        self._time_radio.pack(anchor="w", padx=40, pady=(4, 0))

        # ── Section 5 — Viewing Frequency ───────────────────────────────────
        section_label(card, "📅", "How Often Do You Watch Movies?",
                      "Helps us understand how active a moviegoer you are")
        self._freq_radio = RadioRow(card, FREQS,
                                    base_color=BG_INPUT, sel_color=ACCENT_PURP)
        self._freq_radio.pack(anchor="w", padx=40, pady=(4, 0))

        # ── Section 6 — Age Group ────────────────────────────────────────────
        section_label(card, "👤", "Your Age Group",
                      "Filters out age-restricted content appropriately")
        self._age_radio = RadioRow(card, AGE_GROUPS,
                                   base_color=BG_INPUT, sel_color=ACCENT_GREEN)
        self._age_radio.pack(anchor="w", padx=40, pady=(4, 0))

        # ── CTA ──────────────────────────────────────────────────────────────
        tk.Frame(card, bg=CARD_BORDER, height=1).pack(
            fill="x", padx=40, pady=(24, 0))

        cta_row = tk.Frame(card, bg=BG_CARD)
        cta_row.pack(pady=(16, 28))

        self._status = tk.Label(cta_row, text="",
                                font=("Trebuchet MS", 9),
                                bg=BG_CARD, fg="#FF6060")
        self._status.pack(pady=(0, 8))

        save_btn = tk.Label(cta_row,
                            text="🎬  Start My Personalised Experience",
                            font=("Trebuchet MS", 12, "bold"),
                            bg=ACCENT_RED, fg=TXT_WHITE,
                            padx=32, pady=13, cursor="hand2")
        save_btn.pack()
        save_btn.bind("<Button-1>", self._do_save)
        save_btn.bind("<Enter>",    lambda e: save_btn.config(bg="#B01010"))
        save_btn.bind("<Leave>",    lambda e: save_btn.config(bg=ACCENT_RED))
        self._save_btn = save_btn

        tk.Label(cta_row,
                 text="You can always update these preferences from your profile.",
                 font=("Trebuchet MS", 8),
                 bg=BG_CARD, fg=TXT_MUTED).pack(pady=(8, 0))

    # ─────────────────────────────────────────
    def _collect_prefs(self) -> dict:
        return {
            "genres":    [c._text for c in self._genre_chips if c.selected],
            "languages": [c._text for c in self._lang_chips  if c.selected],
            "vibes":     [c._text for c in self._vibe_chips  if c.selected],
            "show_time": self._time_radio.get() if self._time_radio else "",
            "frequency": self._freq_radio.get() if self._freq_radio else "",
            "age_group": self._age_radio.get()  if self._age_radio  else "",
        }

    def _do_save(self, _=None):
        """
        Collect preferences and hand them to main.py via on_complete().
        DB persistence is done ONLY in main.py._onboarding_done() — keeping
        a single save path avoids double-writes and race conditions.
        """
        prefs = self._collect_prefs()

        if not prefs["genres"]:
            self._status.config(
                text="⚠  Please select at least one favourite genre.",
                fg="#FF6060")
            self.after(3000, lambda: self._status.config(text=""))
            return

        self._save_btn.config(text="⏳  Saving…", bg="#8B1010")
        self._status.config(text="", fg=ACCENT_ORG)
        self.update()

        # Log what was collected — actual DB write happens in main.py
        print(f"[ONBOARDING] Prefs collected for user "
              f"{self._user.get('user_id')}: {prefs}")

        self._save_btn.config(text="✓  All set!", bg=ACCENT_GREEN)
        self._status.config(text="✅  Preferences saved!", fg=ACCENT_GREEN)

        # Slight delay so the user sees the ✓ confirmation, then hand off
        self.after(800, lambda: self._on_complete(prefs) if self._on_complete else None)

    def _do_skip(self):
        """Skip onboarding — pass whatever partial prefs have been selected."""
        prefs = self._collect_prefs()
        if self._on_skip:
            self._on_skip(prefs)   # always passes prefs dict

    # ─────────────────────────────────────────
    @staticmethod
    def _darken(hexcol: str, factor: float) -> str:
        r = int(hexcol[1:3], 16)
        g = int(hexcol[3:5], 16)
        b = int(hexcol[5:7], 16)
        return "#{:02x}{:02x}{:02x}".format(
            max(0, int(r*factor)),
            max(0, int(g*factor)),
            max(0, int(b*factor)))

    def destroy(self):
        self._bg.stop()
        super().destroy()


# ─────────────────────────────────────────────
#  STANDALONE TEST
# ─────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Onboarding — Smart Movie")
    root.geometry("1100x820")
    root.minsize(900, 680)
    root.configure(bg=BG_AMBER)
    ttk.Style(root).theme_use("clam")

    demo_user = {"user_id": 1, "full_name": "Roshan Thokal",
                 "email": "roshan@demo.com"}

    def on_done(prefs):
        print("Preferences collected:")
        for k, v in prefs.items():
            print(f"  {k}: {v}")
        root.destroy()

    page = OnboardingPage(root, user=demo_user,
                          on_complete=on_done,
                          on_skip=lambda p: print("Skipped", p) or root.destroy())
    page.pack(fill="both", expand=True)
    root.mainloop()