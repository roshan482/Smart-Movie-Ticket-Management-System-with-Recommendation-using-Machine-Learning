from db import get_connection


TABLES = ["users", "movies", "shows", "seats", "bookings", "booking_seats", "ratings"]


conn = get_connection()
if not conn:
    print("DB_CONNECTION_FAILED")
    raise SystemExit(1)

cur = conn.cursor()
for table in TABLES:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"{table}:{count}")
    except Exception as exc:
        print(f"{table}:ERROR:{exc}")

conn.close()
