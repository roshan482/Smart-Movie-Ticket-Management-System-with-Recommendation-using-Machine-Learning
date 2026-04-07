"""
Smart Movie Ticket Management System
Login Page — ui/login.py

Cinematic warm-amber background with animated spotlight, film-reel
decorations, glassy dark card, icon-prefixed inputs, and social login.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import math
import time
import random


# ─────────────────────────────────────────────
#  PALETTE  (matches landing page + mockup)
# ─────────────────────────────────────────────
BG_AMBER     = "#3B1E08"   # warm dark amber bg
BG_CARD      = "#1E1A1A"   # glassy login card
BG_INPUT     = "#2A2424"   # input field bg
BG_INPUT_FOC = "#342A2A"   # focused input
ACCENT_RED   = "#E02020"
ACCENT_ORG   = "#F5A623"
ACCENT_BLUE  = "#4A90D9"
TXT_WHITE    = "#FFFFFF"
TXT_GREY     = "#9A8888"
TXT_MUTED    = "#6A5A5A"
CARD_BORDER  = "#3A2E2E"
STRIPE_DARK  = "#2A1008"


# ─────────────────────────────────────────────
#  ANIMATED SPOTLIGHT CANVAS
# ─────────────────────────────────────────────
class CinemaBackground(tk.Canvas):
    """Draws the warm cinema background: gradient stripes + animated spotlight."""

    def __init__(self, master, **kw):
        super().__init__(master, highlightthickness=0, bd=0, **kw)
        self._t = 0.0
        self._running = True
        self._particles = self._make_particles()
        self.bind("<Configure>", lambda e: self._draw_static())
        self._draw_static()
        self._animate()

    def _make_particles(self):
        particles = []
        for _ in range(40):
            particles.append({
                "x": random.uniform(0, 1200),
                "y": random.uniform(0, 900),
                "r": random.uniform(1, 6),
                "spd": random.uniform(0.2, 0.8),
                "phase": random.uniform(0, 2 * math.pi),
                "col": random.choice([
                    "#7A3010", "#A04818", "#C06020",
                    "#8B3A12", "#C08030"
                ])
            })
        return particles

    def _draw_static(self):
        self.delete("static")
        w = self.winfo_width() or 900
        h = self.winfo_height() or 800

        # Base background gradient (simulated with bands)
        bands = 30
        for i in range(bands):
            t  = i / bands
            r  = int(0x3B + (0x20 - 0x3B) * t)
            g  = int(0x1E + (0x0A - 0x1E) * t)
            b  = int(0x08 + (0x04 - 0x08) * t)
            col = "#{:02x}{:02x}{:02x}".format(
                max(0, min(255, r)),
                max(0, min(255, g)),
                max(0, min(255, b))
            )
            y0 = int(i * h / bands)
            y1 = int((i + 1) * h / bands) + 1
            self.create_rectangle(0, y0, w, y1, fill=col, outline="", tags="static")

        # Film strip decorations — left side
        self._film_strip(0, 0, w, h, side="left")
        # Film strip decorations — right side
        self._film_strip(0, 0, w, h, side="right")

        # Cinema seat silhouettes at bottom
        self._seat_row(w, h)

    def _film_strip(self, x0, y0, w, h, side):
        strip_w = 55
        x = 0 if side == "left" else w - strip_w

        # Strip background
        self.create_rectangle(x, 0, x + strip_w, h,
                              fill="#1A0C06", outline="", tags="static")

        # Sprocket holes
        hole_h, gap = 18, 28
        for y in range(8, h, gap):
            hx = x + 10
            self.create_rectangle(hx, y, hx + strip_w - 20, y + hole_h,
                                  fill="#0A0604", outline="#2A1A10",
                                  width=1, tags="static")

        # Amber vertical stripe on inner edge
        inner_x = x + strip_w if side == "left" else x - 2
        self.create_rectangle(inner_x, 0, inner_x + 3, h,
                              fill="#7A3C10", outline="", tags="static")

    def _seat_row(self, w, h):
        """Draw silhouette cinema seats at the bottom."""
        seat_y  = h - 120
        seat_w  = 60
        seat_gap = 12
        count   = w // (seat_w + seat_gap) + 2
        for i in range(count):
            x = i * (seat_w + seat_gap) - 10
            # seat back
            self.create_rectangle(x, seat_y, x + seat_w, seat_y + 70,
                                  fill="#2A0E08", outline="", tags="static")
            # seat top curve (approximate)
            self.create_oval(x - 4, seat_y - 10, x + seat_w + 4, seat_y + 20,
                             fill="#3A1410", outline="", tags="static")
            # armrest
            self.create_rectangle(x - 6, seat_y + 10, x + 2, seat_y + 40,
                                  fill="#200C06", outline="", tags="static")
            self.create_rectangle(x + seat_w - 2, seat_y + 10,
                                  x + seat_w + 6, seat_y + 40,
                                  fill="#200C06", outline="", tags="static")

        # Floor
        self.create_rectangle(0, h - 55, w, h,
                              fill="#150804", outline="", tags="static")

    def _animate(self):
        if not self._running:
            return
        self.delete("anim")
        w = self.winfo_width() or 900
        h = self.winfo_height() or 800
        self._t += 0.02

        # Spotlight cone from top-right
        sx = w - 60
        sy = 0
        angle_base = math.pi * 1.35
        swing = math.sin(self._t * 0.4) * 0.12
        angle = angle_base + swing

        cone_len = h * 1.1
        spread   = 0.22

        tx1 = sx + math.cos(angle - spread) * cone_len
        ty1 = sy + math.sin(angle - spread) * cone_len
        tx2 = sx + math.cos(angle + spread) * cone_len
        ty2 = sy + math.sin(angle + spread) * cone_len

        # Outer soft glow
        self.create_polygon(sx, sy, tx1, ty1, tx2, ty2,
                            fill="#7A4A10", outline="", tags="anim",
                            stipple="gray12")
        # Inner cone
        inner_s = spread * 0.5
        ix1 = sx + math.cos(angle - inner_s) * cone_len
        iy1 = sy + math.sin(angle - inner_s) * cone_len
        ix2 = sx + math.cos(angle + inner_s) * cone_len
        iy2 = sy + math.sin(angle + inner_s) * cone_len
        self.create_polygon(sx, sy, ix1, iy1, ix2, iy2,
                            fill="#C06A20", outline="", tags="anim",
                            stipple="gray25")

        # Spotlight lamp glow
        lr = 18 + math.sin(self._t * 2) * 3
        self.create_oval(sx - lr, sy - lr, sx + lr, sy + lr,
                         fill="#F5C060", outline="#FFE090", width=2,
                         tags="anim")
        # Inner bright spot
        self.create_oval(sx - 8, sy - 8, sx + 8, sy + 8,
                         fill="#FFFFFF", outline="", tags="anim")

        # Second spotlight (left, static-ish)
        sx2  = 55
        a2   = math.pi * 0.55 + math.sin(self._t * 0.25) * 0.08
        tx2a = sx2 + math.cos(a2 - spread) * cone_len
        ty2a = sy  + math.sin(a2 - spread) * cone_len
        tx2b = sx2 + math.cos(a2 + spread) * cone_len
        ty2b = sy  + math.sin(a2 + spread) * cone_len
        self.create_polygon(sx2, 0, tx2a, ty2a, tx2b, ty2b,
                            fill="#7A4A10", outline="", tags="anim",
                            stipple="gray12")
        lr2 = 14 + math.sin(self._t * 1.7 + 1) * 2
        self.create_oval(sx2 - lr2, -lr2, sx2 + lr2, lr2,
                         fill="#F5C060", outline="#FFE090", width=1,
                         tags="anim")

        # Floating bokeh particles
        for p in self._particles:
            p["x"] -= p["spd"] * 0.3
            p["y"] += math.sin(self._t + p["phase"]) * 0.4
            if p["x"] < -10:
                p["x"] = w + 10
                p["y"] = random.uniform(0, h)
            r = p["r"]
            try:
                col = p["col"][:7]  # strip alpha if present
                self.create_oval(p["x"] - r, p["y"] - r,
                                 p["x"] + r, p["y"] + r,
                                 fill=col, outline="", tags="anim")
            except Exception:
                pass

        self.after(40, self._animate)   # ~25 fps

    def stop(self):
        self._running = False


# ─────────────────────────────────────────────
#  CUSTOM STYLED ENTRY
# ─────────────────────────────────────────────
class IconEntry(tk.Frame):
    """
    Dark rounded-style input with an emoji icon prefix and placeholder.
    Optional right-side widget (e.g. 'Forgot Password?' label).
    """

    def __init__(self, master, icon, placeholder, show=None,
                 right_widget=None, **kw):
        super().__init__(master, bg=BG_INPUT,
                         highlightbackground=CARD_BORDER,
                         highlightthickness=1, bd=0)
        self._placeholder = placeholder
        self._show        = show          # "*" for password
        self._has_text    = False

        # Icon label
        tk.Label(self, text=icon, font=("Segoe UI Emoji", 14),
                 bg=BG_INPUT, fg=TXT_GREY,
                 padx=8, pady=0).pack(side="left")

        # Separator line
        tk.Frame(self, bg=CARD_BORDER, width=1,
                 height=22).pack(side="left", pady=6)

        # Entry widget
        self.var   = tk.StringVar()
        self.entry = tk.Entry(self, textvariable=self.var,
                              font=("Trebuchet MS", 11),
                              bg=BG_INPUT, fg=TXT_GREY,
                              insertbackground=TXT_WHITE,
                              relief="flat", bd=0,
                              highlightthickness=0)
        self.entry.pack(side="left", fill="x", expand=True,
                        padx=(8, 0), pady=10)
        self.entry.insert(0, placeholder)

        if right_widget:
            right_widget.pack(side="right", padx=12)

        # Focus bindings
        self.entry.bind("<FocusIn>",  self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Button-1>", lambda e: self.entry.focus_set())

        # Hover
        self.bind("<Enter>", lambda e: self._set_border(ACCENT_RED))
        self.bind("<Leave>", lambda e: self._set_border(CARD_BORDER)
                  if not self.entry == self.focus_get() else None)

    def _on_focus_in(self, _):
        self.config(bg=BG_INPUT_FOC, highlightbackground=ACCENT_RED)
        self.entry.config(bg=BG_INPUT_FOC)
        if not self._has_text:
            self.entry.delete(0, "end")
            self.entry.config(fg=TXT_WHITE,
                              show=self._show if self._show else "")

    def _on_focus_out(self, _):
        self._set_border(CARD_BORDER)
        self.config(bg=BG_INPUT)
        self.entry.config(bg=BG_INPUT)
        if not self.entry.get():
            self._has_text = False
            self.entry.config(show="", fg=TXT_GREY)
            self.entry.insert(0, self._placeholder)
        else:
            self._has_text = True

    def _set_border(self, col):
        self.config(highlightbackground=col)

    def get(self):
        val = self.var.get()
        return "" if val == self._placeholder else val

    def clear(self):
        self.entry.delete(0, "end")
        self._has_text = False
        self.entry.config(show="", fg=TXT_GREY)
        self.entry.insert(0, self._placeholder)


# ─────────────────────────────────────────────
#  SOCIAL BUTTON
# ─────────────────────────────────────────────
class SocialBtn(tk.Label):
    def __init__(self, master, icon, bg_col, hover_col, cb=None, **kw):
        super().__init__(master, text=icon,
                         font=("Segoe UI Emoji", 18),
                         bg=bg_col, fg=TXT_WHITE,
                         width=3, pady=8,
                         cursor="hand2",
                         relief="flat", bd=0)
        self._bg    = bg_col
        self._hover = hover_col
        self._cb    = cb
        self.bind("<Enter>",    lambda e: self.config(bg=self._hover))
        self.bind("<Leave>",    lambda e: self.config(bg=self._bg))
        self.bind("<Button-1>", lambda e: self._cb() if self._cb else None)


# ─────────────────────────────────────────────
#  LOGIN PAGE
# ─────────────────────────────────────────────
class LoginPage(tk.Frame):
    """
    Full-screen login page.

    Callbacks:
        on_login(email, password) -> bool   : validate & proceed
        on_register()                        : switch to register page
        on_back()                            : back to landing
    """

    def __init__(self, master,
                 on_login=None,
                 on_register=None,
                 on_back=None,
                 **kw):
        super().__init__(master, bg=BG_AMBER, **kw)
        self._on_login    = on_login
        self._on_register = on_register
        self._on_back     = on_back
        self._build()

    # ── BUILD ─────────────────────────────────────────────────────────────────
    def _build(self):
        # Full-window animated background
        self._bg = CinemaBackground(self, bg=BG_AMBER)
        self._bg.place(relx=0, rely=0, relwidth=1, relheight=1)

        # ── Back button (top-left) ──────────────────────────────────────────
        back = tk.Label(self._bg, text="← Back",
                        font=("Trebuchet MS", 9),
                        bg=BG_AMBER, fg=TXT_GREY, cursor="hand2")
        back.place(x=70, y=14)
        back.bind("<Button-1>",
                  lambda e: self._on_back() if self._on_back else None)
        back.bind("<Enter>", lambda e: back.config(fg=TXT_WHITE))
        back.bind("<Leave>", lambda e: back.config(fg=TXT_GREY))

        # ── Logo (top-centre) ──────────────────────────────────────────────
        logo_frame = tk.Frame(self._bg, bg=BG_AMBER)
        logo_frame.place(relx=0.5, y=30, anchor="n")

        tk.Label(logo_frame, text="🎬",
                 font=("Segoe UI Emoji", 28),
                 bg=BG_AMBER, fg=ACCENT_ORG).pack(side="left", padx=(0, 6))

        lbl_wrap = tk.Frame(logo_frame, bg=BG_AMBER)
        lbl_wrap.pack(side="left")

        title_row = tk.Frame(lbl_wrap, bg=BG_AMBER)
        title_row.pack(anchor="w")
        tk.Label(title_row, text="Smart ",
                 font=("Georgia", 20, "bold"),
                 bg=BG_AMBER, fg=TXT_WHITE).pack(side="left")
        tk.Label(title_row, text="Movie",
                 font=("Georgia", 20, "bold italic"),
                 bg=BG_AMBER, fg=ACCENT_ORG).pack(side="left")

        tk.Label(lbl_wrap, text="T I C K E T  M A N A G E M E N T  S Y S T E M",
                 font=("Trebuchet MS", 7, "bold"),
                 bg=BG_AMBER, fg=ACCENT_BLUE).pack(anchor="w")

        # ── Login Card ─────────────────────────────────────────────────────
        self._card = tk.Frame(self._bg, bg=BG_CARD,
                              highlightbackground=CARD_BORDER,
                              highlightthickness=1, bd=0)
        self._card.place(relx=0.5, rely=0.5,
                         anchor="center",
                         width=440, height=490)

        self._build_card(self._card)

    def _build_card(self, card):
        pad = 38

        # ── Welcome heading ─────────────────────────────────────────────────
        tk.Label(card, text="Welcome Back!",
                 font=("Georgia", 22, "bold"),
                 bg=BG_CARD, fg=TXT_WHITE).pack(pady=(36, 4))

        tk.Label(card, text="Please sign in to your account",
                 font=("Trebuchet MS", 9),
                 bg=BG_CARD, fg=TXT_GREY).pack()

        # Divider
        tk.Frame(card, bg=CARD_BORDER, height=1).pack(
            fill="x", padx=pad, pady=(16, 20))

        # ── Email Field ─────────────────────────────────────────────────────
        self._email = IconEntry(card, "👤", "Email Address")
        self._email.pack(fill="x", padx=pad, ipady=2)

        # ── Password Field ──────────────────────────────────────────────────
        forgot = tk.Label(card, text="Forgot Password?",
                          font=("Trebuchet MS", 8),
                          bg=BG_INPUT, fg=ACCENT_BLUE, cursor="hand2")
        forgot.bind("<Enter>", lambda e: forgot.config(fg=TXT_WHITE))
        forgot.bind("<Leave>", lambda e: forgot.config(fg=ACCENT_BLUE))

        self._password = IconEntry(card, "🔒", "Password",
                                   show="*", right_widget=forgot)
        self._password.pack(fill="x", padx=pad, pady=(10, 0), ipady=2)

        # ── Sign In Button ──────────────────────────────────────────────────
        self._signin_btn = tk.Label(
            card, text="Sign In",
            font=("Trebuchet MS", 12, "bold"),
            bg=ACCENT_RED, fg=TXT_WHITE,
            cursor="hand2", pady=12
        )
        self._signin_btn.pack(fill="x", padx=pad, pady=(22, 0))
        self._signin_btn.bind("<Button-1>", self._handle_login)
        self._signin_btn.bind("<Enter>",
                              lambda e: self._signin_btn.config(bg="#C01010"))
        self._signin_btn.bind("<Leave>",
                              lambda e: self._signin_btn.config(bg=ACCENT_RED))

        # Loading indicator (hidden by default)
        self._loading = tk.Label(card, text="",
                                 font=("Trebuchet MS", 9),
                                 bg=BG_CARD, fg=ACCENT_ORG)
        self._loading.pack(pady=(4, 0))

        # ── Social divider ──────────────────────────────────────────────────
        div_row = tk.Frame(card, bg=BG_CARD)
        div_row.pack(fill="x", padx=pad, pady=(16, 0))
        tk.Frame(div_row, bg=CARD_BORDER, height=1).pack(
            side="left", fill="x", expand=True)
        tk.Label(div_row, text="  Or sign in with  ",
                 font=("Trebuchet MS", 8),
                 bg=BG_CARD, fg=TXT_MUTED).pack(side="left")
        tk.Frame(div_row, bg=CARD_BORDER, height=1).pack(
            side="left", fill="x", expand=True)

        # ── Social Buttons ──────────────────────────────────────────────────
        soc_row = tk.Frame(card, bg=BG_CARD)
        soc_row.pack(pady=(14, 0))

        SocialBtn(soc_row, "f", "#1877F2", "#1056B8").pack(
            side="left", padx=8, ipadx=6)
        SocialBtn(soc_row, "G", "#DB4437", "#A83028").pack(
            side="left", padx=8, ipadx=6)
        SocialBtn(soc_row, "🐦", "#1DA1F2", "#0D7AB8").pack(
            side="left", padx=8, ipadx=6)

        # ── Sign Up link ────────────────────────────────────────────────────
        signup_row = tk.Frame(card, bg=BG_CARD)
        signup_row.pack(pady=(20, 0))
        tk.Label(signup_row, text="Don't have an account? ",
                 font=("Trebuchet MS", 9),
                 bg=BG_CARD, fg=TXT_GREY).pack(side="left")
        signup_link = tk.Label(signup_row, text="Sign Up",
                               font=("Trebuchet MS", 9, "bold", "underline"),
                               bg=BG_CARD, fg=ACCENT_ORG, cursor="hand2")
        signup_link.pack(side="left")
        signup_link.bind("<Button-1>",
                         lambda e: self._on_register() if self._on_register else None)
        signup_link.bind("<Enter>",
                         lambda e: signup_link.config(fg=TXT_WHITE))
        signup_link.bind("<Leave>",
                         lambda e: signup_link.config(fg=ACCENT_ORG))

    # ── LOGIN HANDLER ─────────────────────────────────────────────────────────
    def _handle_login(self, _=None):
        email    = self._email.get().strip()
        password = self._password.get().strip()

        # Basic validation
        if not email or not password:
            self._show_error("Please fill in all fields.")
            return

        if "@" not in email or "." not in email:
            self._show_error("Please enter a valid email address.")
            return

        if len(password) < 4:
            self._show_error("Password must be at least 4 characters.")
            return

        # Show loading animation
        self._signin_btn.config(text="Signing in...", bg="#8B1010")
        self._loading.config(text="⏳  Please wait…")
        self.update()

        # Delegate to callback
        if self._on_login:
            success = self._on_login(email, password)
            if not success:
                self._signin_btn.config(text="Sign In", bg=ACCENT_RED)
                self._loading.config(text="")
                self._show_error("Invalid email or password. Please try again.")
        else:
            # Demo mode — simulate success
            self.after(800, self._demo_success)

    def _demo_success(self):
        self._signin_btn.config(text="✓ Welcome!", bg="#1A8040")
        self._loading.config(text="")

    def _show_error(self, msg):
        self._signin_btn.config(text="Sign In", bg=ACCENT_RED)
        self._loading.config(text=f"⚠  {msg}", fg="#FF6060")
        self.after(3500, lambda: self._loading.config(text="", fg=ACCENT_ORG))

    def destroy(self):
        self._bg.stop()
        super().destroy()


# ─────────────────────────────────────────────
#  STANDALONE TEST RUNNER
# ─────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Smart Movie Ticket Management — Login")
    root.geometry("900x750")
    root.minsize(700, 620)
    root.configure(bg=BG_AMBER)

    style = ttk.Style(root)
    style.theme_use("clam")

    def fake_login(email, password):
        # Accept demo@demo.com / demo1234
        return email == "demo@demo.com" and password == "demo1234"

    page = LoginPage(
        root,
        on_login=fake_login,
        on_register=lambda: print("→ Navigate to Register"),
        on_back=lambda: print("→ Navigate to Landing"),
    )
    page.pack(fill="both", expand=True)
    root.mainloop()