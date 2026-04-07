from pathlib import Path


path = Path("main.py")
text = path.read_text(encoding="utf-8")
start = text.find('        except Exception as exc:')
if start == -1:
    raise SystemExit("except block not found")
end = text.find('        if result["success"]:', start)
if end == -1:
    raise SystemExit("success block not found")
new = """        except Exception as exc:
            print(f"[AUTH] login_user error: {exc}")
            import traceback; traceback.print_exc()
            return False

"""
path.write_text(text[:start] + new + text[end:], encoding="utf-8")
print("hardened main.py login fallback")
