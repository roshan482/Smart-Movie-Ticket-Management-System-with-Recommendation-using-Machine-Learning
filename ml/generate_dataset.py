"""
ml/generate_dataset.py
======================
Generates two synthetic CSV datasets:

  movies.csv          — 60 movies with rich feature vectors
  interactions.csv    — 2000 simulated user–movie interactions
                        (ratings, bookings, watch-time)

Run once:
    python ml/generate_dataset.py

Outputs land in ml/data/.
"""

import os, random, math
import pandas as pd
import numpy as np

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

OUT_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Genre / Language / Mood taxonomy ─────────────────────────────────────────
GENRES = ["Action", "Romance", "Comedy", "Thriller", "Horror",
          "Sci-Fi", "Animation", "Drama", "Mystery", "Fantasy",
          "Biography", "Sports"]

LANGUAGES = ["Hindi", "English", "Marathi", "Tamil", "Telugu",
             "Bengali", "Kannada", "Malayalam"]

MOODS = ["Chill & Relax", "Thrills & Chills", "Feel Good",
         "Mind-Bending", "Emotional Ride", "Laugh Out Loud"]

AGE_GROUPS = ["Under 18", "18–25", "26–35", "36–50", "50+"]

SHOW_TIMES = ["Morning (9AM–12PM)", "Afternoon (12–4PM)",
              "Evening (4–8PM)", "Night (8PM–12AM)", "Late Night (12AM+)"]

# Genre → compatible moods mapping
GENRE_MOOD = {
    "Action":    ["Thrills & Chills", "Feel Good"],
    "Romance":   ["Chill & Relax", "Emotional Ride", "Feel Good"],
    "Comedy":    ["Laugh Out Loud", "Chill & Relax", "Feel Good"],
    "Thriller":  ["Thrills & Chills", "Mind-Bending"],
    "Horror":    ["Thrills & Chills"],
    "Sci-Fi":    ["Mind-Bending", "Thrills & Chills"],
    "Animation": ["Feel Good", "Laugh Out Loud", "Chill & Relax"],
    "Drama":     ["Emotional Ride", "Chill & Relax"],
    "Mystery":   ["Mind-Bending", "Thrills & Chills"],
    "Fantasy":   ["Feel Good", "Mind-Bending", "Chill & Relax"],
    "Biography": ["Emotional Ride", "Feel Good"],
    "Sports":    ["Feel Good", "Thrills & Chills", "Laugh Out Loud"],
}

# Genre → age group affinity weights  (index = AGE_GROUPS)
GENRE_AGE = {
    "Action":    [0.6, 0.9, 0.7, 0.5, 0.3],
    "Romance":   [0.5, 0.8, 0.9, 0.7, 0.6],
    "Comedy":    [0.8, 0.8, 0.7, 0.7, 0.6],
    "Thriller":  [0.3, 0.7, 0.9, 0.8, 0.5],
    "Horror":    [0.5, 0.9, 0.7, 0.4, 0.2],
    "Sci-Fi":    [0.5, 0.9, 0.8, 0.6, 0.4],
    "Animation": [0.9, 0.7, 0.5, 0.4, 0.4],
    "Drama":     [0.4, 0.6, 0.8, 0.9, 0.9],
    "Mystery":   [0.4, 0.7, 0.9, 0.8, 0.7],
    "Fantasy":   [0.7, 0.9, 0.7, 0.5, 0.3],
    "Biography": [0.3, 0.5, 0.7, 0.9, 0.8],
    "Sports":    [0.6, 0.9, 0.7, 0.6, 0.4],
}

MOVIE_TEMPLATES = [
    # (title, genre, language, base_rating, price_band)
    ("Inferno Rising",       "Action",    "English", 8.4, 3),
    ("Eternal Bloom",        "Romance",   "Hindi",   7.9, 2),
    ("Pixel Quest",          "Animation", "English", 8.7, 2),
    ("Shadow Protocol",      "Thriller",  "English", 8.1, 3),
    ("Cosmic Drift",         "Sci-Fi",    "English", 9.0, 4),
    ("Hasi Ke Rang",         "Comedy",    "Hindi",   7.5, 1),
    ("Whisper in Dark",      "Horror",    "English", 7.8, 2),
    ("Yaar Mera",            "Drama",     "Marathi", 8.2, 2),
    ("Dil Ki Baat",          "Romance",   "Hindi",   7.6, 1),
    ("Steel Storm",          "Action",    "English", 8.0, 3),
    ("Hasee Ke Haseen",      "Comedy",    "Hindi",   7.3, 1),
    ("Neon Shadows",         "Sci-Fi",    "English", 8.5, 3),
    ("Gumnaam Raat",         "Mystery",   "Hindi",   7.7, 2),
    ("Dragon Heart",         "Fantasy",   "English", 8.3, 3),
    ("Sachin: A Billion Dreams","Biography","English",8.6,2),
    ("Chennai Express",      "Comedy",    "Hindi",   7.4, 1),
    ("Raazi",                "Thriller",  "Hindi",   8.5, 2),
    ("Tumbbad",              "Horror",    "Marathi", 8.9, 2),
    ("Kantara",              "Drama",     "Kannada", 9.1, 2),
    ("RRR",                  "Action",    "Telugu",  8.8, 3),
    ("Vikram",               "Action",    "Tamil",   8.3, 3),
    ("Maharaja",             "Action",    "Tamil",   8.4, 2),
    ("Kalki 2898 AD",        "Sci-Fi",    "Telugu",  8.0, 3),
    ("Pushpa 2",             "Action",    "Telugu",  7.8, 2),
    ("Stree 2",              "Horror",    "Hindi",   8.2, 2),
    ("Munjya",               "Horror",    "Marathi", 7.6, 1),
    ("Gol Maal Again",       "Comedy",    "Hindi",   7.1, 1),
    ("Dune Part Two",        "Sci-Fi",    "English", 8.9, 4),
    ("Oppenheimer",          "Biography", "English", 9.0, 3),
    ("Barbie",               "Comedy",    "English", 7.8, 2),
    ("Interstellar",         "Sci-Fi",    "English", 8.7, 3),
    ("The Dark Knight",      "Thriller",  "English", 9.0, 3),
    ("Inception",            "Sci-Fi",    "English", 8.8, 3),
    ("PK",                   "Comedy",    "Hindi",   8.4, 2),
    ("3 Idiots",             "Comedy",    "Hindi",   9.0, 2),
    ("Dangal",               "Sports",    "Hindi",   8.8, 2),
    ("Sultan",               "Sports",    "Hindi",   7.9, 2),
    ("Chak De India",        "Sports",    "Hindi",   8.5, 2),
    ("Dhoom 3",              "Action",    "Hindi",   6.8, 2),
    ("War",                  "Action",    "Hindi",   7.6, 3),
    ("Spider-Man: NWH",      "Action",    "English", 8.5, 3),
    ("Avengers Endgame",     "Action",    "English", 8.4, 4),
    ("Doctor Strange MoM",   "Fantasy",   "English", 6.9, 3),
    ("Thor Love Thunder",    "Fantasy",   "English", 6.6, 3),
    ("Wakanda Forever",      "Action",    "English", 7.3, 3),
    ("Moana 2",              "Animation", "English", 7.8, 2),
    ("Inside Out 2",         "Animation", "English", 8.1, 2),
    ("Elemental",            "Animation", "English", 7.4, 2),
    ("Zara Hatke Zara Bachke","Romance",  "Hindi",   7.2, 1),
    ("Rocky Aur Rani",       "Romance",   "Hindi",   7.5, 2),
    ("Tum Bin 2",            "Romance",   "Hindi",   6.5, 1),
    ("Article 15",           "Drama",     "Hindi",   8.2, 2),
    ("Masaan",               "Drama",     "Hindi",   8.3, 1),
    ("Taare Zameen Par",     "Drama",     "Hindi",   8.6, 2),
    ("Queen",                "Drama",     "Hindi",   8.2, 2),
    ("Piku",                 "Drama",     "Hindi",   7.9, 1),
    ("Andhadhun",            "Thriller",  "Hindi",   8.7, 2),
    ("Kahaani",              "Mystery",   "Hindi",   8.2, 2),
    ("Drishyam 2",           "Mystery",   "Malayalam",8.1,2),
    ("Vikrant Rona",         "Fantasy",   "Kannada", 7.3, 2),
]


def _price(band: int) -> int:
    return {1: 180, 2: 220, 3: 280, 4: 350}.get(band, 220)


def _seats(rating: float) -> int:
    # Higher-rated movies have fewer seats left (more popular)
    base = int(100 - (rating - 6) * 15)
    return max(5, min(90, base + random.randint(-10, 10)))


# ── Build movies DataFrame ────────────────────────────────────────────────────
def build_movies() -> pd.DataFrame:
    rows = []
    for idx, (title, genre, lang, rating, price_band) in enumerate(MOVIE_TEMPLATES, 1):
        # Compatible moods for this genre
        mood_pool = GENRE_MOOD.get(genre, MOODS)
        primary_mood = random.choice(mood_pool)

        rows.append({
            "movie_id":     idx,
            "title":        title,
            "genre":        genre,
            "language":     lang,
            "rating":       rating,
            "price":        _price(price_band),
            "seats_left":   _seats(rating),
            "primary_mood": primary_mood,
            # One-hot genre features (12 genres)
            **{f"genre_{g.lower().replace('-','_').replace(' ','_')}":
               int(g == genre) for g in GENRES},
            # One-hot language features
            **{f"lang_{l.lower()}": int(l == lang) for l in LANGUAGES},
            # One-hot mood
            **{f"mood_{m.lower().replace(' ','_').replace('&','n')}":
               int(m == primary_mood) for m in MOODS},
        })
    return pd.DataFrame(rows)


# ── Build interactions DataFrame ──────────────────────────────────────────────
def build_interactions(movies_df: pd.DataFrame, n_users=120) -> pd.DataFrame:
    """
    Simulate user–movie interactions.
    Each synthetic user has:
      - preferred genres (2–4)
      - preferred languages (1–3)
      - age group
    Their ratings follow a biased normal distribution:
      liked genre/lang → rating drawn from N(8.2, 0.8)
      neutral          → N(6.5, 1.2)
      disliked         → N(4.5, 1.5)   (rare, 10% chance)
    """
    rows = []
    all_movie_ids = movies_df["movie_id"].tolist()

    for user_id in range(1, n_users + 1):
        pref_genres = random.sample(GENRES, k=random.randint(2, 4))
        pref_langs  = random.sample(LANGUAGES, k=random.randint(1, 3))
        age_idx     = random.randint(0, len(AGE_GROUPS) - 1)
        pref_time   = random.choice(SHOW_TIMES)

        # Each user rates 8–25 movies
        n_interactions = random.randint(8, 25)
        # Weight movies toward user preferences
        weights = []
        for _, m in movies_df.iterrows():
            w = 1.0
            if m["genre"] in pref_genres:
                w *= 3.0
            if m["language"] in pref_langs:
                w *= 2.0
            # Age affinity
            age_aff = GENRE_AGE.get(m["genre"], [0.5]*5)[age_idx]
            w *= age_aff
            weights.append(w)

        weights = np.array(weights, dtype=float)
        weights /= weights.sum()

        selected = np.random.choice(
            all_movie_ids,
            size=min(n_interactions, len(all_movie_ids)),
            replace=False,
            p=weights
        )

        for mid in selected:
            row = movies_df[movies_df["movie_id"] == mid].iloc[0]
            genre_liked = row["genre"] in pref_genres
            lang_liked  = row["language"] in pref_langs

            if genre_liked and lang_liked:
                base = 8.2
                std  = 0.7
            elif genre_liked or lang_liked:
                base = 7.2
                std  = 1.0
            elif random.random() < 0.10:   # dislike
                base = 4.5
                std  = 1.5
            else:
                base = 6.0
                std  = 1.2

            raw_rating = np.random.normal(base, std)
            rating = round(max(1.0, min(10.0, raw_rating)), 1)

            # Whether they booked vs just rated
            booked  = int(genre_liked or lang_liked or rating >= 7.0)
            watched = int(booked and random.random() > 0.25)

            rows.append({
                "user_id":        user_id,
                "movie_id":       int(mid),
                "rating":         rating,
                "booked":         booked,
                "watched":        watched,
                "pref_genres":    "|".join(pref_genres),
                "pref_langs":     "|".join(pref_langs),
                "age_group":      AGE_GROUPS[age_idx],
                "pref_show_time": pref_time,
            })

    return pd.DataFrame(rows)


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating movies dataset …")
    movies_df = build_movies()
    movies_path = os.path.join(OUT_DIR, "movies.csv")
    movies_df.to_csv(movies_path, index=False)
    print(f"  ✓ {len(movies_df)} movies → {movies_path}")

    print("Generating interactions dataset …")
    interactions_df = build_interactions(movies_df, n_users=150)
    inter_path = os.path.join(OUT_DIR, "interactions.csv")
    interactions_df.to_csv(inter_path, index=False)
    print(f"  ✓ {len(interactions_df)} interactions → {inter_path}")

    print("\nSample movies:")
    print(movies_df[["movie_id","title","genre","language","rating","price"]].head(10).to_string(index=False))
    print("\nSample interactions:")
    print(interactions_df[["user_id","movie_id","rating","booked","watched"]].head(8).to_string(index=False))