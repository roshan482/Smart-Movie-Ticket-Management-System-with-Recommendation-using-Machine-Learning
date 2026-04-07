"""
ui/register.py — Registration Page
Cinematic dark design matching login.py style.

FIX: import changed from `services.auth_service` to `auth_service`
     because all files live at the project root (flat layout).
"""

import tkinter as tk
from tkinter import ttk
import math, time, random, sys, os

# ── Ensure project root is on sys.path ───────────────────────────────────────
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from services.auth_service import register_user   # auth_service.py is at project root

# ── Palette (identical to login.py) ──────────────────────────────────────────
BG_AMBER     = "#3B1E08"
BG_CARD      = "#1E1A1A"
BG_INPUT     = "#2A2424"
BG_INPUT_FOC = "#342A2A"
ACCENT_RED   = "#E02020"
ACCENT_ORG   = "#F5A623"
ACCENT_BLUE  = "#4A90D9"
ACCENT_GREEN = "#27AE60"
TXT_WHITE    = "#FFFFFF"
TXT_GREY     = "#9A8888"
TXT_MUTED    = "#6A5A5A"
CARD_BORDER  = "#3A2E2E"


# ── Animated cinema background (same style as login) ─────────────────────────
class CinemaBackground(tk.Canvas):
    def __init__(self, master, **kw):
        super().__init__(master, highlightthickness=0, bd=0, **kw)
        self._t = 0.0
        self._running = True
        self._particles = [
            {"x": random.uniform(0, 1200), "y": random.uniform(0, 900),
             "r": random.uniform(1, 6),    "spd": random.uniform(0.2, 0.8),
             "phase": random.uniform(0, 2*math.pi),
             "col": random.choice(["#7A3010","#A04818","#C06020","#8B3A12"])}
            for _ in range(40)
        ]
        self.bind("<Configure>", lambda e: self._draw_static())
        self._draw_static()
        self._animate()

    def _draw_static(self):
        self.delete("static")
        w = self.winfo_width() or 900
        h = self.winfo_height() or 900
        bands = 30
        for i in range(bands):
            t   = i / bands
            r   = int(0x3B + (0x20 - 0x3B) * t)
            g   = int(0x1E + (0x0A - 0x1E) * t)
            b   = int(0x08 + (0x04 - 0x08) * t)
            col = "#{:02x}{:02x}{:02x}".format(
                max(0,min(255,r)), max(0,min(255,g)), max(0,min(255,b)))
            y0 = int(i * h / bands)
            y1 = int((i + 1) * h / bands) + 1
            self.create_rectangle(0, y0, w, y1, fill=col, outline="", tags="static")
        for side in ("left", "right"):
            sw = 55
            x  = 0 if side == "left" else w - sw
            self.create_rectangle(x, 0, x+sw, h, fill="#1A0C06", outline="", tags="static")
            for y in range(8, h, 28):
                hx = x + 10
                self.create_rectangle(hx, y, hx+sw-20, y+18,
                                      fill="#0A0604", outline="#2A1A10", width=1, tags="static")

    def _animate(self):
        if not self._running:
            return
        self.delete("anim")
        w = self.winfo_width() or 900
        h = self.winfo_height() or 900
        self._t += 0.02
        sx, sy  = w - 60, 0
        angle   = math.pi * 1.35 + math.sin(self._t * 0.4) * 0.12
        cone_l  = h * 1.1
        spread  = 0.22
        tx1 = sx + math.cos(angle - spread) * cone_l
        ty1 = sy + math.sin(angle - spread) * cone_l
        tx2 = sx + math.cos(angle + spread) * cone_l
        ty2 = sy + math.sin(angle + spread) * cone_l
        self.create_polygon(sx, sy, tx1, ty1, tx2, ty2,
                            fill="#7A4A10", outline="", tags="anim", stipple="gray12")
        lr = 18 + math.sin(self._t * 2) * 3
        self.create_oval(sx-lr, sy-lr, sx+lr, sy+lr,
                         fill="#F5C060", outline="#FFE090", width=2, tags="anim")
        self.create_oval(sx-8, sy-8, sx+8, sy+8, fill="#FFFFFF", outline="", tags="anim")
        for p in self._particles:
            p["x"] -= p["spd"] * 0.3
            p["y"] += math.sin(self._t + p["phase"]) * 0.4
            if p["x"] < -10:
                p["x"] = w + 10
                p["y"] = random.uniform(0, h)
            r = p["r"]
            self.create_oval(p["x"]-r, p["y"]-r, p["x"]+r, p["y"]+r,
                             fill=p["col"], outline="", tags="anim")
        self.after(40, self._animate)

    def stop(self):
        self._running = False


# ── Custom styled entry (matches login.py) ────────────────────────────────────
class IconEntry(tk.Frame):
    def __init__(self, master, icon, placeholder, show=None, **kw):
        super().__init__(master, bg=BG_INPUT,
                         highlightbackground=CARD_BORDER,
                         highlightthickness=1, bd=0)
        self._placeholder = placeholder
        self._show        = show
        self._has_text    = False

        tk.Label(self, text=icon, font=("Segoe UI Emoji", 14),
                 bg=BG_INPUT, fg=TXT_GREY, padx=8).pack(side="left")
        tk.Frame(self, bg=CARD_BORDER, width=1, height=22).pack(side="left", pady=6)

        self.var   = tk.StringVar()
        self.entry = tk.Entry(self, textvariable=self.var,
                              font=("Trebuchet MS", 11),
                              bg=BG_INPUT, fg=TXT_GREY,
                              insertbackground=TXT_WHITE,
                              relief="flat", bd=0, highlightthickness=0)
        self.entry.pack(side="left", fill="x", expand=True, padx=(8,0), pady=10)
        self.entry.insert(0, placeholder)

        self.entry.bind("<FocusIn>",  self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Button-1>", lambda e: self.entry.focus_set())
        self.bind("<Enter>", lambda e: self.config(highlightbackground=ACCENT_RED))
        self.bind("<Leave>", lambda e: self.config(highlightbackground=CARD_BORDER))

    def _on_focus_in(self, _):
        self.config(bg=BG_INPUT_FOC, highlightbackground=ACCENT_RED)
        self.entry.config(bg=BG_INPUT_FOC)
        if not self._has_text:
            self.entry.delete(0, "end")
            self.entry.config(fg=TXT_WHITE, show=self._show or "")

    def _on_focus_out(self, _):
        self.config(bg=BG_INPUT, highlightbackground=CARD_BORDER)
        self.entry.config(bg=BG_INPUT)
        if not self.entry.get():
            self._has_text = False
            self.entry.config(show="", fg=TXT_GREY)
            self.entry.insert(0, self._placeholder)
        else:
            self._has_text = True

    def get(self):
        val = self.var.get()
        return "" if val == self._placeholder else val

    def clear(self):
        self.entry.delete(0, "end")
        self._has_text = False
        self.entry.config(show="", fg=TXT_GREY)
        self.entry.insert(0, self._placeholder)


# ─────────────────────────────────────────────
#  REGISTER PAGE
# ─────────────────────────────────────────────
class RegisterPage(tk.Frame):
    """
    Full-screen registration page.

    Callbacks
    ---------
    on_register_success(user_id) — after successful registration
    on_login()                   — switch to login page
    on_back()                    — back to landing
    """
    def __init__(self, master, on_register_success=None,
                 on_login=None, on_back=None, **kw):
        super().__init__(master, bg=BG_AMBER, **kw)
        self._on_success = on_register_success
        self._on_login   = on_login
        self._on_back    = on_back
        self._build()

    def _build(self):
        self._bg = CinemaBackground(self, bg=BG_AMBER)
        self._bg.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Back button
        back = tk.Label(self._bg, text="← Back", font=("Trebuchet MS", 9),
                        bg=BG_AMBER, fg=TXT_GREY, cursor="hand2")
        back.place(x=70, y=14)
        back.bind("<Button-1>", lambda e: self._on_back() if self._on_back else None)
        back.bind("<Enter>", lambda e: back.config(fg=TXT_WHITE))
        back.bind("<Leave>", lambda e: back.config(fg=TXT_GREY))

        # Logo
        logo_frame = tk.Frame(self._bg, bg=BG_AMBER)
        logo_frame.place(relx=0.5, y=22, anchor="n")
        tk.Label(logo_frame, text="🎬", font=("Segoe UI Emoji", 24),
                 bg=BG_AMBER, fg=ACCENT_ORG).pack(side="left", padx=(0,6))
        lw = tk.Frame(logo_frame, bg=BG_AMBER)
        lw.pack(side="left")
        tr = tk.Frame(lw, bg=BG_AMBER)
        tr.pack(anchor="w")
        tk.Label(tr, text="Smart ", font=("Georgia", 16, "bold"),
                 bg=BG_AMBER, fg=TXT_WHITE).pack(side="left")
        tk.Label(tr, text="Movie", font=("Georgia", 16, "bold italic"),
                 bg=BG_AMBER, fg=ACCENT_ORG).pack(side="left")
        tk.Label(lw, text="TICKET MANAGEMENT SYSTEM",
                 font=("Trebuchet MS", 7, "bold"),
                 bg=BG_AMBER, fg=ACCENT_BLUE).pack(anchor="w")

        # Card
        card = tk.Frame(self._bg, bg=BG_CARD,
                        highlightbackground=CARD_BORDER,
                        highlightthickness=1, bd=0)
        card.place(relx=0.5, rely=0.52, anchor="center", width=460, height=560)
        self._build_card(card)

    def _build_card(self, card):
        pad = 38

        tk.Label(card, text="Create Account",
                 font=("Georgia", 20, "bold"),
                 bg=BG_CARD, fg=TXT_WHITE).pack(pady=(28, 3))
        tk.Label(card, text="Join us and start booking your movies!",
                 font=("Trebuchet MS", 9),
                 bg=BG_CARD, fg=TXT_GREY).pack()

        tk.Frame(card, bg=CARD_BORDER, height=1).pack(fill="x", padx=pad, pady=(14, 16))

        self._name     = IconEntry(card, "👤", "Full Name")
        self._name.pack(fill="x", padx=pad, ipady=2)

        self._email    = IconEntry(card, "✉️", "Email Address")
        self._email.pack(fill="x", padx=pad, pady=(10, 0), ipady=2)

        self._phone    = IconEntry(card, "📱", "Phone Number (optional)")
        self._phone.pack(fill="x", padx=pad, pady=(10, 0), ipady=2)

        self._password = IconEntry(card, "🔒", "Password", show="*")
        self._password.pack(fill="x", padx=pad, pady=(10, 0), ipady=2)

        self._confirm  = IconEntry(card, "🔒", "Confirm Password", show="*")
        self._confirm.pack(fill="x", padx=pad, pady=(10, 0), ipady=2)

        self._reg_btn = tk.Label(
            card, text="Create Account",
            font=("Trebuchet MS", 12, "bold"),
            bg=ACCENT_RED, fg=TXT_WHITE,
            cursor="hand2", pady=11
        )
        self._reg_btn.pack(fill="x", padx=pad, pady=(20, 0))
        self._reg_btn.bind("<Button-1>", self._handle_register)
        self._reg_btn.bind("<Enter>",  lambda e: self._reg_btn.config(bg="#C01010"))
        self._reg_btn.bind("<Leave>",  lambda e: self._reg_btn.config(bg=ACCENT_RED))

        self._status = tk.Label(card, text="",
                                font=("Trebuchet MS", 9),
                                bg=BG_CARD, fg=ACCENT_ORG)
        self._status.pack(pady=(5, 0))

        login_row = tk.Frame(card, bg=BG_CARD)
        login_row.pack(pady=(10, 0))
        tk.Label(login_row, text="Already have an account? ",
                 font=("Trebuchet MS", 9),
                 bg=BG_CARD, fg=TXT_GREY).pack(side="left")
        login_link = tk.Label(login_row, text="Sign In",
                              font=("Trebuchet MS", 9, "bold", "underline"),
                              bg=BG_CARD, fg=ACCENT_ORG, cursor="hand2")
        login_link.pack(side="left")
        login_link.bind("<Button-1>",
                        lambda e: self._on_login() if self._on_login else None)
        login_link.bind("<Enter>", lambda e: login_link.config(fg=TXT_WHITE))
        login_link.bind("<Leave>", lambda e: login_link.config(fg=ACCENT_ORG))

    def _handle_register(self, _=None):
        name     = self._name.get().strip()
        email    = self._email.get().strip()
        phone    = self._phone.get().strip()
        password = self._password.get()
        confirm  = self._confirm.get()

        if not name or not email or not password:
            self._show_error("Please fill in all required fields.")
            return

        if password != confirm:
            self._show_error("Passwords do not match.")
            return

        self._reg_btn.config(text="Creating account...", bg="#8B1010")
        self._status.config(text="⏳  Please wait…", fg=ACCENT_ORG)
        self.update()

        result = register_user(name, email, password, phone or None)

        if result["success"]:
            self._reg_btn.config(text="✓ Account Created!", bg=ACCENT_GREEN)
            self._status.config(
                text="✅  Welcome! Redirecting to login…", fg=ACCENT_GREEN)
            uid = result["user_id"]
            self.after(1500,
                       lambda: self._on_success(uid) if self._on_success else None)
        else:
            self._reg_btn.config(text="Create Account", bg=ACCENT_RED)
            self._show_error(result["error"])

    def _show_error(self, msg):
        self._status.config(text=f"⚠  {msg}", fg="#FF6060")
        self.after(4000, lambda: self._status.config(text=""))

    def destroy(self):
        self._bg.stop()
        super().destroy()