"""
db.py — Database connection + all helper functions used by auth_service.py
"""

import json
import mysql.connector
from mysql.connector import Error


def get_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Pass@123",
            database="smart_movie_db"
        )
        return conn
    except Error as e:
        print(f"[DB ERROR] {e}")
        return None


# ─────────────────────────────────────────────
#  USER HELPERS
# ─────────────────────────────────────────────

def email_exists(email: str) -> bool:
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE email = %s LIMIT 1", (email,))
        return cursor.fetchone() is not None
    except Error as e:
        print(f"[DB ERROR] email_exists: {e}")
        return False
    finally:
        conn.close()


def create_user(full_name: str, email: str,
                hashed_password: str, phone: str = None):
    """
    Insert a new user. is_first_login defaults to 1 via the column DEFAULT.
    Returns new user_id on success, None on failure.
    """
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO users (full_name, email, password, phone, is_first_login)
               VALUES (%s, %s, %s, %s, 1)""",
            (full_name, email, hashed_password, phone)
        )
        conn.commit()
        return cursor.lastrowid
    except Error as e:
        print(f"[DB ERROR] create_user: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def get_user_by_email(email: str):
    """
    Fetch a full user row by email — includes is_first_login and preferences
    so main.py can route to Onboarding or Dashboard correctly.

    Returns dict with keys:
        user_id, full_name, email, password, phone,
        is_first_login, preferences
    or None if not found.
    """
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT user_id, full_name, email, password, phone,
                      is_first_login, preferences
               FROM users
               WHERE email = %s
               LIMIT 1""",
            (email,)
        )
        row = cursor.fetchone()
        if row is None:
            return None

        # MySQL may return preferences as a string — parse it to dict
        raw = row.get("preferences")
        if isinstance(raw, str):
            try:
                row["preferences"] = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                row["preferences"] = None

        # Normalise is_first_login to plain int.
        # CRITICAL: must NOT use `or 1` — that turns 0 (returning user) into 1
        # (first-time user) because 0 is falsy.  Use explicit None check instead.
        raw_flag = row.get("is_first_login")
        row["is_first_login"] = int(raw_flag) if raw_flag is not None else 1

        return row
    except Error as e:
        print(f"[DB ERROR] get_user_by_email: {e}")
        return None
    finally:
        conn.close()


# ─────────────────────────────────────────────
#  PREFERENCE HELPERS
# ─────────────────────────────────────────────

def save_preferences(user_id: int, prefs: dict) -> bool:
    """
    Save ML preference dict to users.preferences (JSON column).
    Simultaneously clears is_first_login = 0 so onboarding never shows again.
    """
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE users
               SET preferences    = %s,
                   is_first_login = 0
               WHERE user_id = %s""",
            (json.dumps(prefs), user_id)
        )
        conn.commit()
        updated = cursor.rowcount > 0
        if updated:
            print(f"[DB] save_preferences: user {user_id} → is_first_login=0, prefs saved")
        else:
            print(f"[DB] save_preferences: no row updated for user_id={user_id}")
        return updated
    except Error as e:
        print(f"[DB ERROR] save_preferences: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def get_preferences(user_id: int):
    """
    Return stored preference dict for a user, or None if not yet set.
    """
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT preferences FROM users WHERE user_id = %s LIMIT 1",
            (user_id,)
        )
        row = cursor.fetchone()
        if not row or not row["preferences"]:
            return None
        data = row["preferences"]
        return json.loads(data) if isinstance(data, str) else data
    except Error as e:
        print(f"[DB ERROR] get_preferences: {e}")
        return None
    finally:
        conn.close()


def clear_first_login_flag(user_id: int) -> bool:
    """
    Set is_first_login = 0 without touching preferences.
    Called when a user skips onboarding.
    """
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET is_first_login = 0 WHERE user_id = %s",
            (user_id,)
        )
        conn.commit()
        print(f"[DB] clear_first_login_flag: user {user_id} → is_first_login=0")
        return True
    except Error as e:
        print(f"[DB ERROR] clear_first_login_flag: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()