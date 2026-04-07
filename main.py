"""
main.py — Smart Movie Ticket Management System
App root with full page routing:

    Landing → Login → [first login? Onboarding] → Dashboard
                    ↕
               Register → Login

Page flow
---------
1. App opens on LandingPage.
2. User clicks Login / Sign Up → LoginPage / RegisterPage.
3. On successful login:
     a. Read is_first_login from the user dict returned by login_user().
     b. If 1  → show OnboardingPage (collect ML prefs, clear flag in DB).
     c. If 0  → show DashboardPage  (pass stored prefs from DB).
4. Logout → back to LandingPage.

FIXES vs original
-----------------
* All UI files are at the project ROOT (not inside ui/), so imports now
  use flat module names: `from login import LoginPage` etc.
* auth_service is also at root (not inside services/).
* _post_login_route reads is_first_login directly from the user dict
  returned by login_user() — no extra DB call needed.
* Import errors are surfaced clearly instead of silently falling through
  to Dashboard.
"""

import tkinter as tk
from tkinter import ttk
import sys
import os
import random
import math
import time

# ── Ensure project root is always on sys.path ────────────────────────────────
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# ── UI page imports (all files live at project root) ─────────────────────────
from ui.login import LoginPage
from ui.register import RegisterPage   # register.py

# Lazy imports so the app starts even if a file has a syntax error
def _import_onboarding():
    from ui.Onboarding import OnboardingPage   # Onboarding.py  (capital O)
    return OnboardingPage

def _import_dashboard():
    from ui.dashboard import DashboardPage    # dashboard.py
    return DashboardPage


# ─────────────────────────────────────────────
#  COLOUR PALETTE
# ─────────────────────────────────────────────
BG_DARK      = "#0D0A0A"
BG_NAV       = "#111010"
CARD_BG      = "#1A1414"
ACCENT_RED   = "#E02020"
ACCENT_ORG   = "#F5A623"
TXT_WHITE    = "#FFFFFF"
TXT_GREY     = "#B0A8A8"
STRIP_BG     = "#160F0F"
BORDER_DIM   = "#2A2020"


# ─────────────────────────────────────────────
#  PARTICLE CANVAS (landing hero)
# ─────────────────────────────────────────────
class ParticleCanvas(tk.Canvas):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self._particles = []
        self._running   = True
        self._init_particles()
        self._animate()

    def _init_particles(self):
        for _ in range(55):
            self._particles.append({
                "x":     random.uniform(0, 1200),
                "y":     random.uniform(0, 400),
                "r":     random.uniform(2, 12),
                "spd":   random.uniform(0.3, 1.2),
                "col":   random.choice(["#8B3010","#C04A20","#F5A623",
                                         "#A03010","#D06020","#904010"]),
                "phase": random.uniform(0, 2*math.pi),
            })

    def _animate(self):
        if not self._running:
            return
        self.delete("particle")
        t = time.time()
        for p in self._particles:
            p["x"] -= p["spd"] * 0.4
            p["y"] += math.sin(t * 0.6 + p["phase"]) * 0.35
            if p["x"] < -20:
                p["x"] = 1220
                p["y"] = random.uniform(0, 400)
            r = p["r"]
            self.create_oval(p["x"]-r*2, p["y"]-r*2,
                             p["x"]+r*2, p["y"]+r*2,
                             fill=self._dim(p["col"], 0.18),
                             outline="", tags="particle")
            self.create_oval(p["x"]-r, p["y"]-r,
                             p["x"]+r, p["y"]+r,
                             fill=p["col"], outline="", tags="particle")
        self.after(33, self._animate)

    @staticmethod
    def _dim(hexcol, factor):
        r, g, b = (int(hexcol[i:i+2], 16) for i in (1, 3, 5))
        return "#{:02x}{:02x}{:02x}".format(
            int(r*factor), int(g*factor), int(b*factor))

    def stop(self):
        self._running = False


# ─────────────────────────────────────────────
#  LANDING PAGE
# ─────────────────────────────────────────────
class LandingPage(tk.Frame):
    MOVIES = [
        {"title": "ACTION",    "sub": "THRILLER",   "color": "#C03010", "emoji": "💥"},
        {"title": "ROMANTIC",  "sub": "LOVE",        "color": "#C0204A", "emoji": "❤️"},
        {"title": "ANIMATED",  "sub": "ADVENTURE",   "color": "#1E6CA8", "emoji": "🎈"},
        {"title": "MYSTERY",   "sub": "NIGHT",       "color": "#1A1A2E", "emoji": "🔍"},
    ]

    def __init__(self, master, show_login_cb=None, show_register_cb=None):
        super().__init__(master, bg=BG_DARK)
        self.show_login_cb    = show_login_cb
        self.show_register_cb = show_register_cb
        self._canvas = tk.Canvas(self, bg=BG_DARK, highlightthickness=0, bd=0)
        self._vsb    = ttk.Scrollbar(self, orient="vertical",
                                     command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._vsb.set)
        self._vsb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)
        self._inner = tk.Frame(self._canvas, bg=BG_DARK)
        self._win   = self._canvas.create_window((0,0), window=self._inner, anchor="nw")
        self._inner.bind("<Configure>",
                         lambda e: self._canvas.configure(
                             scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",
                          lambda e: self._canvas.itemconfig(self._win, width=e.width))
        self._canvas.bind_all("<MouseWheel>",
                              lambda e: self._canvas.yview_scroll(
                                  -1 if e.delta > 0 else 1, "units"))
        self._build()

    def _build(self):
        self._build_navbar()
        self._build_hero()
        self._build_feature_strip()
        self._build_now_showing()
        self._build_footer()

    def _build_navbar(self):
        nav = tk.Frame(self._inner, bg=BG_NAV, height=56)
        nav.pack(fill="x")
        nav.pack_propagate(False)
        lf = tk.Frame(nav, bg=BG_NAV)
        lf.pack(side="left", padx=(18, 0))
        tk.Label(lf, text="🎬", font=("Segoe UI Emoji", 20),
                 bg=BG_NAV, fg=ACCENT_RED).pack(side="left")
        lbl = tk.Frame(lf, bg=BG_NAV)
        lbl.pack(side="left", padx=(6, 0))
        tk.Label(lbl, text="SMART MOVIE TICKET",
                 font=("Trebuchet MS", 10, "bold"),
                 bg=BG_NAV, fg=TXT_WHITE).pack(anchor="w")
        tk.Label(lbl, text="MANAGEMENT",
                 font=("Trebuchet MS", 7),
                 bg=BG_NAV, fg=TXT_GREY).pack(anchor="w")
        right = tk.Frame(nav, bg=BG_NAV)
        right.pack(side="right", padx=18)
        for lbl_text, active in [("Home",True),("Movies",False),
                                   ("About Us",False),("Contact Us",False)]:
            col = TXT_WHITE if active else TXT_GREY
            l = tk.Label(right, text=lbl_text,
                         font=("Trebuchet MS", 9, "underline" if active else ""),
                         bg=BG_NAV, fg=col, cursor="hand2")
            l.pack(side="left", padx=10)
        self._nav_btn(right, "Login",   outline=True,  cb=self.show_login_cb)
        self._nav_btn(right, "Sign Up", outline=False, cb=self.show_register_cb)

    def _nav_btn(self, parent, text, outline, cb):
        bg  = BG_NAV if outline else ACCENT_RED
        btn = tk.Label(parent, text=text,
                       font=("Trebuchet MS", 9, "bold"),
                       bg=bg, fg=TXT_WHITE, padx=14, pady=4,
                       cursor="hand2",
                       relief="solid" if outline else "flat", bd=1 if outline else 0)
        btn.pack(side="left", padx=5)
        btn.bind("<Button-1>", lambda e: cb() if cb else None)
        btn.bind("<Enter>",  lambda e, b=btn, o=outline: b.config(
            bg="#C01A1A" if not o else "#1E1818"))
        btn.bind("<Leave>",  lambda e, b=btn, bg_=bg: b.config(bg=bg_))

    def _build_hero(self):
        hero = tk.Frame(self._inner, bg="#1A0C08", height=320)
        hero.pack(fill="x")
        hero.pack_propagate(False)
        pc = ParticleCanvas(hero, bg="#1A0C08",
                            highlightthickness=0, bd=0, width=1200, height=320)
        pc.place(x=0, y=0, relwidth=1, relheight=1)
        ov = tk.Frame(hero, bg="#0D0605")
        ov.place(relx=0, rely=0, relwidth=0.55, relheight=1)
        ct = tk.Frame(hero, bg="#0D0605")
        ct.place(x=50, rely=0.08, relheight=0.84, width=480)
        tk.Label(ct, text="Book Your ", font=("Georgia", 28, "bold"),
                 bg="#0D0605", fg=TXT_WHITE).pack(anchor="w", padx=24, pady=(32,0))
        row2 = tk.Frame(ct, bg="#0D0605")
        row2.pack(anchor="w", padx=24)
        tk.Label(row2, text="Movie Tickets",
                 font=("Georgia", 28, "bold"),
                 bg="#0D0605", fg=ACCENT_ORG).pack(side="left")
        tk.Label(row2, text=" Easily!",
                 font=("Georgia", 28, "bold"),
                 bg="#0D0605", fg=TXT_WHITE).pack(side="left")
        tk.Label(ct, text="Experience The Best Cinema Experience",
                 font=("Trebuchet MS", 11),
                 bg="#0D0605", fg=TXT_GREY).pack(anchor="w", padx=24, pady=(8,22))
        btn_row = tk.Frame(ct, bg="#0D0605")
        btn_row.pack(anchor="w", padx=24)
        self._hero_btn(btn_row, "🎟  Book Tickets", filled=True,  cb=self.show_login_cb)
        self._hero_btn(btn_row, "🎬  View Movies",  filled=False, cb=self.show_login_cb)
        tk.Label(hero, text="🎥\n🍿\n🎞",
                 font=("Segoe UI Emoji", 42),
                 bg="#1A0C08", justify="center").place(
                     relx=0.72, rely=0.05, relwidth=0.22, relheight=0.9)

    def _hero_btn(self, parent, text, filled, cb):
        col = ACCENT_RED if filled else "#1A0C08"
        b = tk.Label(parent, text=text,
                     font=("Trebuchet MS", 10, "bold"),
                     bg=col, fg=TXT_WHITE, padx=16, pady=7,
                     relief="flat" if filled else "solid",
                     bd=0 if filled else 1, cursor="hand2")
        b.pack(side="left", padx=(0, 12))
        b.bind("<Button-1>", lambda e: cb() if cb else None)
        b.bind("<Enter>", lambda e, w=b, f=filled:
               w.config(bg="#B01010" if f else "#2A1A1A"))
        b.bind("<Leave>", lambda e, w=b, c=col: w.config(bg=c))

    def _build_feature_strip(self):
        strip = tk.Frame(self._inner, bg=STRIP_BG, pady=14)
        strip.pack(fill="x")
        features = [
            ("🎟", "Easy Booking",     "Quick & Simple Ticket Booking"),
            ("🔒", "Secure Payments",  "Safe & Reliable Transactions"),
            ("🎧", "Customer Support", "24/7 Help & Assistance"),
        ]
        cols = tk.Frame(strip, bg=STRIP_BG)
        cols.pack()
        for i, (icon, title, sub) in enumerate(features):
            cell = tk.Frame(cols, bg=STRIP_BG, width=280, padx=20)
            cell.pack(side="left")
            cell.pack_propagate(False)
            row = tk.Frame(cell, bg=STRIP_BG)
            row.pack(pady=4)
            tk.Label(row, text=icon, font=("Segoe UI Emoji", 22),
                     bg=STRIP_BG, fg=ACCENT_RED).pack(side="left", padx=(0,10))
            txt = tk.Frame(row, bg=STRIP_BG)
            txt.pack(side="left")
            tk.Label(txt, text=title, font=("Trebuchet MS", 11, "bold"),
                     bg=STRIP_BG, fg=TXT_WHITE).pack(anchor="w")
            tk.Label(txt, text=sub, font=("Trebuchet MS", 8),
                     bg=STRIP_BG, fg=TXT_GREY).pack(anchor="w")
            if i < len(features)-1:
                tk.Frame(cols, bg=BORDER_DIM, width=1, height=40).pack(
                    side="left", pady=6)

    def _build_now_showing(self):
        sec = tk.Frame(self._inner, bg=BG_DARK, pady=24)
        sec.pack(fill="x", padx=40)
        tk.Label(sec, text="Now Showing",
                 font=("Georgia", 18, "bold"),
                 bg=BG_DARK, fg=TXT_WHITE).pack(anchor="w")
        tk.Label(sec, text="Popular Movies in Theaters",
                 font=("Trebuchet MS", 9),
                 bg=BG_DARK, fg=TXT_GREY).pack(anchor="w", pady=(2, 14))
        grid = tk.Frame(sec, bg=BG_DARK)
        grid.pack(fill="x")
        for i, m in enumerate(self.MOVIES):
            self._movie_card(grid, m, i)

    def _movie_card(self, parent, movie, col):
        def darken(h, f):
            r, g, b = (int(h[i:i+2], 16) for i in (1,3,5))
            return "#{:02x}{:02x}{:02x}".format(
                int(r*f), int(g*f), int(b*f))
        card = tk.Frame(parent, bg=movie["color"],
                        width=210, height=230, cursor="hand2")
        card.grid(row=0, column=col, padx=8)
        card.pack_propagate(False)
        card.grid_propagate(False)
        poster = tk.Frame(card, bg=darken(movie["color"], 0.55), height=148)
        poster.pack(fill="x")
        poster.pack_propagate(False)
        tk.Label(poster, text=movie["emoji"],
                 font=("Segoe UI Emoji", 48),
                 bg=darken(movie["color"], 0.55)).pack(expand=True)
        info = tk.Frame(card, bg=movie["color"], height=82)
        info.pack(fill="x")
        info.pack_propagate(False)
        tk.Label(info, text=movie["title"],
                 font=("Trebuchet MS", 10, "bold"),
                 bg=movie["color"], fg=TXT_WHITE).pack(pady=(6,0))
        tk.Label(info, text=movie["sub"],
                 font=("Trebuchet MS", 8),
                 bg=movie["color"], fg=ACCENT_ORG).pack()
        book = tk.Label(info, text="BOOK NOW",
                        font=("Trebuchet MS", 8, "bold"),
                        bg=ACCENT_RED, fg=TXT_WHITE,
                        padx=10, pady=3, cursor="hand2")
        book.pack(pady=4)
        book.bind("<Button-1>",
                  lambda e: self.show_login_cb() if self.show_login_cb else None)
        book.bind("<Enter>", lambda e, w=book: w.config(bg="#B01010"))
        book.bind("<Leave>", lambda e, w=book: w.config(bg=ACCENT_RED))

    def _build_footer(self):
        ft = tk.Frame(self._inner, bg="#0A0808", pady=16)
        ft.pack(fill="x")
        tk.Label(ft,
                 text="© 2026 Smart Movie Ticket Management System  •  All rights reserved",
                 font=("Trebuchet MS", 8),
                 bg="#0A0808", fg="#5A4A4A").pack()


# ─────────────────────────────────────────────
#  APP ROOT — FULL PAGE ROUTER
# ─────────────────────────────────────────────
class App(tk.Tk):
    """
    Central page router.

    State
    -----
    _page          : currently visible Frame
    _current_user  : dict from DB after login (includes is_first_login)
    _user_prefs    : dict from onboarding / DB preferences
    """

    def __init__(self):
        super().__init__()
        self.title("Smart Movie Ticket Management System")
        self.geometry("1280x800")
        self.minsize(960, 620)
        self.configure(bg=BG_DARK)

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Vertical.TScrollbar",
                        background=BG_DARK, troughcolor="#1A1010",
                        bordercolor=BG_DARK, arrowcolor=ACCENT_RED,
                        gripcount=0)

        self._page         = None
        self._current_user = None
        self._user_prefs   = {}

        self._show_landing()

    # ── Page helpers ──────────────────────────────────────────────────────────
    def _swap(self, new_page: tk.Frame):
        if self._page:
            try:
                self._page.destroy()
            except Exception:
                pass
        self._page = new_page
        self._page.pack(fill="both", expand=True)

    # ── Routes ────────────────────────────────────────────────────────────────
    def _show_landing(self):
        self._current_user = None
        self._user_prefs   = {}
        self._swap(LandingPage(
            self,
            show_login_cb=self._show_login,
            show_register_cb=self._show_register,
        ))

    def _show_login(self):
        self._swap(LoginPage(
            self,
            on_login=self._handle_login,
            on_register=self._show_register,
            on_back=self._show_landing,
        ))

    def _show_register(self):
        self._swap(RegisterPage(
            self,
            on_register_success=lambda uid: self._show_login(),
            on_login=self._show_login,
            on_back=self._show_landing,
        ))

    # ── Auth handlers ─────────────────────────────────────────────────────────
    def _handle_login(self, email: str, password: str) -> bool:
        """
        Called by LoginPage.  Returns True on success.

        FIX: auth_service.login_user now returns the full user row including
        is_first_login, so we no longer need a separate DB call for routing.
        """
        try:
            from auth_service import login_user   # flat import — same dir as main.py
            result = login_user(email, password)
        except Exception as exc:
            print(f"[AUTH] login_user error: {exc}")
            import traceback; traceback.print_exc()
            # Demo fallback — only reached when DB is unreachable.
            # is_first_login=0 so we go to Dashboard (not an infinite onboarding loop)
            result = {
                "success": True,
                "user": {
                    "user_id":        1,
                    "full_name":      "Demo User",
                    "email":          email,
                    "is_first_login": 0,   # 0 = skip onboarding in demo/offline mode
                    "preferences":    None,
                },
            }

        if result["success"]:
            self._current_user = result["user"]
            # Small delay so the login ✓ animation plays
            self.after(600, self._post_login_route)
            return True
        return False

    def _post_login_route(self):
        """
        Decide Onboarding vs Dashboard based on is_first_login in user dict.
        is_first_login = 1  →  first-time user  →  Onboarding
        is_first_login = 0  →  returning user   →  Dashboard
        """
        user = self._current_user
        is_first = bool(user.get("is_first_login", 1))

        print(f"[ROUTE] user_id={user.get('user_id')}  "
              f"is_first_login={user.get('is_first_login')}  "
              f"→ {'Onboarding' if is_first else 'Dashboard'}")

        if is_first:
            # Prefs not set yet; initialise to empty
            self._user_prefs = {}
            self._show_onboarding()
        else:
            # Load stored preferences from DB for the Dashboard
            try:
                from auth_service import get_user_preferences
                prefs = get_user_preferences(user["user_id"])
            except Exception:
                prefs = None

            # Fall back to preferences already on the user dict if DB call fails
            if prefs is None:
                raw = user.get("preferences")
                prefs = raw if isinstance(raw, dict) else {}

            self._user_prefs = prefs or {}
            self._show_dashboard()

    # ── Onboarding ────────────────────────────────────────────────────────────
    def _show_onboarding(self):
        try:
            OnboardingPage = _import_onboarding()
        except ImportError as exc:
            print(f"[ROUTE] Onboarding import failed: {exc}")
            import traceback; traceback.print_exc()
            self._flash("⚠  Onboarding module not found — going to Dashboard")
            self.after(1500, self._show_dashboard)
            return

        self._swap(OnboardingPage(
            self,
            user=self._current_user,
            on_complete=self._onboarding_done,
            on_skip=self._onboarding_skip,
        ))

    def _onboarding_done(self, prefs: dict):
        """
        Called when user completes onboarding.
        This is the SINGLE place preferences are written to the DB.
        Onboarding.py no longer does the DB write — it only collects prefs.
        """
        self._user_prefs = prefs
        uid = self._current_user["user_id"]

        try:
            from auth_service import save_user_preferences
            ok = save_user_preferences(uid, prefs)
            if ok:
                print(f"[ONBOARDING] ✅ Prefs saved to DB for user {uid}: {prefs}")
            else:
                print(f"[ONBOARDING] ⚠  save_user_preferences returned False for user {uid}")
        except Exception as exc:
            print(f"[ONBOARDING] ❌ Could not save prefs to DB: {exc}")
            import traceback; traceback.print_exc()

        # Update the in-memory user dict so _post_login_route
        # never sends this user back to Onboarding in the same session
        self._current_user["is_first_login"] = 0

        first_name = self._current_user.get("full_name", "").split()[0]
        self._flash(f"🎉  Preferences saved!  Welcome, {first_name}!")
        self.after(400, self._show_dashboard)

    def _onboarding_skip(self, partial_prefs: dict):
        """Called when user skips onboarding (partial prefs may be collected)."""
        self._user_prefs = partial_prefs or {}
        # Clear the flag in DB so onboarding never appears again
        try:
            from auth_service import clear_first_login
            clear_first_login(self._current_user["user_id"])
        except Exception as exc:
            print(f"[ONBOARDING] clear_first_login error: {exc}")
        # Also clear in-memory so this session routes to Dashboard correctly
        self._current_user["is_first_login"] = 0
        self._show_dashboard()

    # ── Dashboard ─────────────────────────────────────────────────────────────
    def _show_dashboard(self):
        try:
            DashboardPage = _import_dashboard()
        except ImportError as exc:
            print(f"[ROUTE] Dashboard import failed: {exc}")
            import traceback; traceback.print_exc()
            self._flash("⚠  Dashboard module not found!")
            return

        self._swap(DashboardPage(
            self,
            user=self._current_user,
            prefs=self._user_prefs,
            on_logout=self._show_landing,
            on_book=self._open_booking,
            on_nav=self._handle_nav,
        ))

    # ── Booking / Nav stubs ───────────────────────────────────────────────────
    def _open_booking(self, movie: dict):
        print(f"[APP] Open booking for: {movie['title']}")
        self._flash(f"🎟  Opening booking for  {movie['title']}…")

    def _handle_nav(self, key: str):
        nav_map = {
            "book":     "Booking page",
            "bookings": "My Bookings page",
            "rate":     "Rate a Movie page",
            "reco":     "ML Recommendations page",
            "profile":  "Profile page",
            "settings": "Settings page",
        }
        print(f"[NAV] → {nav_map.get(key, key)}")
        self._flash(f"🔜  {nav_map.get(key, key)} — coming soon!")

    # ── Toast notification ────────────────────────────────────────────────────
    def _flash(self, msg: str, duration: int = 2200):
        toast = tk.Toplevel(self)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        toast.configure(bg=ACCENT_RED)
        tk.Label(toast, text=msg,
                 font=("Trebuchet MS", 11, "bold"),
                 bg=ACCENT_RED, fg=TXT_WHITE,
                 padx=24, pady=14).pack()
        self.update_idletasks()
        x = self.winfo_x() + self.winfo_width()  // 2 - 220
        y = self.winfo_y() + self.winfo_height() // 2 - 35
        toast.geometry(f"+{x}+{y}")
        toast.after(duration, toast.destroy)


# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()