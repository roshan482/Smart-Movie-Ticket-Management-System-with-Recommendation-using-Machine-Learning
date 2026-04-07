from ui.dashboard import _fetch_movies_from_db


movies = _fetch_movies_from_db()
print(f"movies_loaded:{len(movies)}")
