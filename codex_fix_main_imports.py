from pathlib import Path


path = Path("main.py")
text = path.read_text(encoding="utf-8")
replacements = [
    ("from auth_service import login_user", "from services.auth_service import login_user"),
    ("from auth_service import get_user_preferences", "from services.auth_service import get_user_preferences"),
    ("from auth_service import save_user_preferences", "from services.auth_service import save_user_preferences"),
    ("from auth_service import clear_first_login", "from services.auth_service import clear_first_login"),
]

for old, new in replacements:
    text = text.replace(old, new)

path.write_text(text, encoding="utf-8")
print("updated main.py")
