"""
auth_service.py
Handles: login, register, session, user preferences (for ML onboarding).

Functions
---------
  register_user(full_name, email, password, phone) -> dict
  login_user(email, password)                      -> dict
  save_user_preferences(user_id, prefs)            -> bool
  get_user_preferences(user_id)                    -> dict | None
  clear_first_login(user_id)                       -> bool
"""

import json
import bcrypt
import sys
import os

# ── Make sure project root is on sys.path ─────────────────────────────────────
# auth_service.py lives at project root → __file__ is already at root
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from db import (
    get_connection,
    email_exists,
    create_user,
    get_user_by_email,
    save_preferences,
    get_preferences,
    clear_first_login_flag,
)


# ─────────────────────────────────────────────
#  SESSION  (in-memory; swap with JWT later)
# ─────────────────────────────────────────────
_current_user: dict | None = None


def get_current_user() -> dict | None:
    return _current_user


# ─────────────────────────────────────────────
#  REGISTER
# ─────────────────────────────────────────────
def register_user(full_name: str, email: str,
                  password: str, phone: str = None) -> dict:
    if not full_name.strip():
        return {"success": False, "error": "Full name is required."}
    if not email.strip() or "@" not in email or "." not in email:
        return {"success": False, "error": "Please enter a valid email address."}
    if len(password) < 6:
        return {"success": False, "error": "Password must be at least 6 characters."}
    if email_exists(email.strip()):
        return {"success": False, "error": "An account with this email already exists."}

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    uid    = create_user(
        full_name.strip(),
        email.strip(),
        hashed,
        phone.strip() if phone else None,
    )
    if uid is None:
        return {"success": False, "error": "Registration failed. Please try again."}

    return {"success": True, "user_id": uid}


# ─────────────────────────────────────────────
#  LOGIN
# ─────────────────────────────────────────────
def login_user(email: str, password: str) -> dict:
    """
    Verify credentials and return the full user row including
    is_first_login so main.py can route to Onboarding or Dashboard.

    Returns
    -------
    {"success": True,  "user": {user_id, full_name, email, phone,
                                 is_first_login, preferences}}
    {"success": False, "error": str}
    """
    global _current_user

    user = get_user_by_email(email.strip())
    if not user:
        return {"success": False, "error": "No account found with this email."}

    if not bcrypt.checkpw(password.encode(), user["password"].encode()):
        return {"success": False, "error": "Incorrect password."}

    # Strip password hash before handing to UI
    user_safe = {k: v for k, v in user.items() if k != "password"}
    _current_user = user_safe

    print(f"[AUTH] login_user: user_id={user_safe['user_id']} "
          f"is_first_login={user_safe.get('is_first_login')}")

    return {"success": True, "user": user_safe}


# ─────────────────────────────────────────────
#  PREFERENCES  (ML Onboarding)
# ─────────────────────────────────────────────
def save_user_preferences(user_id: int, prefs: dict) -> bool:
    """
    Persist the ML preference dict to DB.
    Also sets is_first_login = 0 atomically so onboarding never repeats.
    """
    ok = save_preferences(user_id, prefs)
    if ok:
        global _current_user
        if _current_user and _current_user.get("user_id") == user_id:
            _current_user["preferences"]    = prefs
            _current_user["is_first_login"] = 0
    return ok


def get_user_preferences(user_id: int) -> dict | None:
    return get_preferences(user_id)


def clear_first_login(user_id: int) -> bool:
    """
    Mark onboarding as done (is_first_login = 0) without changing preferences.
    Called when a user skips onboarding.
    """
    ok = clear_first_login_flag(user_id)
    if ok:
        global _current_user
        if _current_user and _current_user.get("user_id") == user_id:
            _current_user["is_first_login"] = 0
    return ok