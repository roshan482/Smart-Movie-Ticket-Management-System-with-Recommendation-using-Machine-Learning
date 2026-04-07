"""
ml/recommender.py
=================
Live inference engine for the Smart Movie recommendation system.

Public API
----------
    get_recommendations(user_prefs, user_id=None, n=5, exclude_ids=None)
        → list of movie dicts sorted by hybrid score

    explain_recommendation(movie_id, user_prefs)
        → str explanation for the dashboard badge

    get_trending(n=5)
        → top-n movies by popularity score

    get_similar(movie_id, n=5)
        → content-similar movies

Algorithm
---------
HYBRID SCORE = α × content_score  +  β × cf_score  +  γ × pref_score

  content_score   — average cosine similarity to user's liked genres/moods
  cf_score        — NMF predicted rating for this movie
  pref_score      — explicit onboarding preference match score

Weights default: α=0.35, β=0.30, γ=0.35
If no CF user data: α=0.45, β=0.10, γ=0.45 (cold-start mode)
"""

import os, sys, json, pickle, warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

_THIS     = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(_THIS, "models")
DATA_DIR  = os.path.join(_THIS, "data")

# ── Global lazy-loaded state ──────────────────────────────────────────────────
_SIM_MATRIX   = None   # (n × n) cosine similarity
_NMF          = None   # fitted NMF model
_W            = None   # user latent factors
_H            = None   # item latent factors
_MID2IDX      = None   # movie_id (int) → matrix col index
_IDX2MID      = None   # matrix col index → movie_id (int)
_MOVIE_META   = None   # str(movie_id) → metadata dict
_MOVIES_DF    = None   # full movies DataFrame
_GENRE_AFF    = None   # genre affinity DataFrame
_STATS        = None   # model training stats
_LOADED       = False


def _load_artefacts():
    global _SIM_MATRIX, _NMF, _W, _H, _MID2IDX, _IDX2MID
    global _MOVIE_META, _MOVIES_DF, _GENRE_AFF, _STATS, _LOADED

    if _LOADED:
        return True

    try:
        _SIM_MATRIX = np.load(os.path.join(MODEL_DIR, "content_similarity.npy"))
        _W          = np.load(os.path.join(MODEL_DIR, "nmf_user_factors.npy"))
        _H          = np.load(os.path.join(MODEL_DIR, "nmf_item_factors.npy"))

        with open(os.path.join(MODEL_DIR, "nmf_model.pkl"), "rb") as f:
            _NMF = pickle.load(f)

        with open(os.path.join(MODEL_DIR, "movie_index.json"), "r") as f:
            idx_data = json.load(f)
            _MID2IDX = {int(k): v for k, v in idx_data["mid2idx"].items()}
            _IDX2MID = {int(k): v for k, v in idx_data["idx2mid"].items()}

        with open(os.path.join(MODEL_DIR, "movie_meta.json"), "r") as f:
            _MOVIE_META = json.load(f)

        with open(os.path.join(MODEL_DIR, "model_stats.json"), "r") as f:
            _STATS = json.load(f)

        movies_path = os.path.join(DATA_DIR, "movies.csv")
        _MOVIES_DF = pd.read_csv(movies_path) if os.path.exists(movies_path) else None

        aff_path = os.path.join(MODEL_DIR, "genre_affinity.csv")
        if os.path.exists(aff_path):
            _GENRE_AFF = pd.read_csv(aff_path, index_col=0)

        _LOADED = True
        print(f"[ML] Recommender loaded: {len(_MOVIE_META)} movies, "
              f"sim={_SIM_MATRIX.shape}, H={_H.shape}")
        return True

    except Exception as exc:
        print(f"[ML] WARNING — could not load model artefacts: {exc}")
        print("[ML] Falling back to rule-based recommendations.")
        _LOADED = True   # set True to avoid repeated load attempts
        return False


# ─────────────────────────────────────────────
#  PREFERENCE SCORE  (onboarding → score)
# ─────────────────────────────────────────────
GENRE_SCORE_MAP = {g: i for i, g in enumerate([
    "Action", "Romance", "Comedy", "Thriller", "Horror",
    "Sci-Fi", "Animation", "Drama", "Mystery", "Fantasy",
    "Biography", "Sports"
])}

MOOD_GENRE = {
    "Chill & Relax":    ["Romance", "Animation", "Comedy", "Drama"],
    "Thrills & Chills": ["Action", "Thriller", "Horror", "Sci-Fi", "Mystery"],
    "Feel Good":        ["Comedy", "Animation", "Romance", "Sports", "Biography"],
    "Mind-Bending":     ["Sci-Fi", "Thriller", "Mystery", "Fantasy"],
    "Emotional Ride":   ["Drama", "Romance", "Biography", "Sports"],
    "Laugh Out Loud":   ["Comedy", "Animation", "Sports"],
}


def _pref_score(movie_meta: dict, user_prefs: dict) -> float:
    """
    Score 0.0–1.0 based on explicit user onboarding preferences.
    """
    score = 0.0

    genres    = user_prefs.get("genres", [])
    languages = user_prefs.get("languages", [])
    vibes     = user_prefs.get("vibes", [])
    age_group = user_prefs.get("age_group", "")

    m_genre = movie_meta.get("genre", "")
    m_lang  = movie_meta.get("language", "")
    m_mood  = movie_meta.get("primary_mood", "")

    # Genre match (highest weight)
    if m_genre in genres:
        score += 0.45
    elif genres:
        score += 0.05   # partial credit — not penalised

    # Language match
    if m_lang in languages:
        score += 0.25
    elif languages:
        score += 0.03

    # Vibe / mood match
    vibe_genres = set()
    for vibe in vibes:
        vibe_genres.update(MOOD_GENRE.get(vibe, []))
    if m_genre in vibe_genres:
        score += 0.15
    elif m_mood in vibes:
        score += 0.10

    # Rating bonus (scaled 0–0.15)
    rating = movie_meta.get("rating", 7.0)
    score += min(0.15, (rating - 6.0) / 10.0 * 0.15 * 3)

    return min(1.0, score)


# ─────────────────────────────────────────────
#  CONTENT SCORE
# ─────────────────────────────────────────────
def _content_score(movie_id: int, user_prefs: dict) -> float:
    """
    Average similarity between this movie and movies that match user's
    genre/language preferences using the content similarity matrix.
    """
    if _SIM_MATRIX is None or _MID2IDX is None:
        return 0.0

    liked_genres = user_prefs.get("genres", [])
    liked_langs  = user_prefs.get("languages", [])

    # Find movies the user would definitely like (genre + lang match)
    anchor_indices = []
    for mid_str, meta in _MOVIE_META.items():
        mid = int(mid_str)
        if meta["genre"] in liked_genres and meta["language"] in liked_langs:
            idx = _MID2IDX.get(mid)
            if idx is not None:
                anchor_indices.append(idx)

    # Fallback: just genre match
    if not anchor_indices:
        for mid_str, meta in _MOVIE_META.items():
            mid = int(mid_str)
            if meta["genre"] in liked_genres:
                idx = _MID2IDX.get(mid)
                if idx is not None:
                    anchor_indices.append(idx)

    if not anchor_indices:
        return 0.5   # no info — neutral

    target_idx = _MID2IDX.get(movie_id)
    if target_idx is None:
        return 0.0

    sims = [_SIM_MATRIX[target_idx, ai] for ai in anchor_indices]
    return float(np.mean(sims))


# ─────────────────────────────────────────────
#  COLLABORATIVE FILTERING SCORE
# ─────────────────────────────────────────────
def _cf_score(movie_id: int, user_prefs: dict) -> float:
    """
    Use NMF item factors + a pseudo user vector built from prefs.
    Real DB users could be looked up in W if we store user_id mappings.
    """
    if _H is None or _MID2IDX is None:
        return 0.0

    target_idx = _MID2IDX.get(movie_id)
    if target_idx is None:
        return 0.0

    # Build a pseudo-user latent vector from genre affinities
    liked_genres = user_prefs.get("genres", [])
    liked_langs  = user_prefs.get("languages", [])

    # Average item factors of "anchor" movies
    anchor_factors = []
    for mid_str, meta in _MOVIE_META.items():
        mid = int(mid_str)
        if meta["genre"] in liked_genres:
            idx = _MID2IDX.get(mid)
            if idx is not None:
                anchor_factors.append(_H[:, idx])

    if not anchor_factors:
        return 0.5

    pseudo_user = np.mean(anchor_factors, axis=0)  # (k,)
    predicted   = float(pseudo_user @ _H[:, target_idx])

    # NMF predictions are in raw rating space; normalise to [0,1]
    # (training ratings are 1–10, so divide by 10)
    return min(1.0, max(0.0, predicted / 10.0))


# ─────────────────────────────────────────────
#  GENRE AFFINITY BOOST
# ─────────────────────────────────────────────
def _genre_affinity_boost(movie_id: int, user_prefs: dict) -> float:
    if _GENRE_AFF is None:
        return 0.0
    liked_genres = user_prefs.get("genres", [])
    if not liked_genres:
        return 0.0
    meta = _MOVIE_META.get(str(movie_id))
    if not meta:
        return 0.0
    m_genre = meta["genre"]
    boosts = []
    for pg in liked_genres:
        if pg in _GENRE_AFF.index and m_genre in _GENRE_AFF.columns:
            val = _GENRE_AFF.loc[pg, m_genre]
            boosts.append((val - 5.0) / 5.0)   # scale: 5=neutral→0, 10→1
    return float(np.mean(boosts)) if boosts else 0.0


# ─────────────────────────────────────────────
#  HYBRID SCORER
# ─────────────────────────────────────────────
def _hybrid_score(movie_id: int, user_prefs: dict,
                  alpha=0.35, beta=0.30, gamma=0.35) -> float:
    """Weighted combination of all three signals."""
    c = _content_score(movie_id, user_prefs)
    f = _cf_score(movie_id, user_prefs)
    p = _pref_score(_MOVIE_META.get(str(movie_id), {}), user_prefs)
    g = _genre_affinity_boost(movie_id, user_prefs)

    # Cold-start: boost pref/content if CF signal is weak
    if f < 0.1:
        alpha, beta, gamma = 0.45, 0.10, 0.45

    return alpha * c + beta * f + gamma * p + 0.05 * g


# ─────────────────────────────────────────────
#  DASHBOARD MOVIE CATALOGUE  (fallback when DB offline)
# ─────────────────────────────────────────────
DASHBOARD_MOVIES = [
    {"id": 1,  "title": "Inferno Rising",  "genre": "Action",    "lang": "English",
     "rating": 8.4, "emoji": "🔥", "color": "#C03010",
     "show": "7:00 PM  •  IMAX",    "seats": 42, "tag": "PG-13  •  2h 18m", "price": 280},
    {"id": 2,  "title": "Eternal Bloom",   "genre": "Romance",   "lang": "Hindi",
     "rating": 7.9, "emoji": "🌸", "color": "#C0204A",
     "show": "6:30 PM  •  Hall 2",  "seats": 78, "tag": "PG  •  2h 02m",    "price": 220},
    {"id": 3,  "title": "Pixel Quest",     "genre": "Animation", "lang": "English",
     "rating": 8.7, "emoji": "🎮", "color": "#1E6CA8",
     "show": "3:00 PM  •  Hall 1",  "seats": 15, "tag": "PG  •  1h 52m",    "price": 200},
    {"id": 4,  "title": "Shadow Protocol", "genre": "Thriller",  "lang": "English",
     "rating": 8.1, "emoji": "🕵️", "color": "#1A1A3E",
     "show": "9:30 PM  •  Hall 3",  "seats": 30, "tag": "R  •  2h 11m",     "price": 250},
    {"id": 5,  "title": "Cosmic Drift",    "genre": "Sci-Fi",    "lang": "English",
     "rating": 9.0, "emoji": "🚀", "color": "#0A3A6A",
     "show": "8:00 PM  •  IMAX",    "seats": 8,  "tag": "PG-13  •  2h 35m", "price": 350},
    {"id": 6,  "title": "Hasi Ke Rang",    "genre": "Comedy",    "lang": "Hindi",
     "rating": 7.5, "emoji": "😂", "color": "#C07010",
     "show": "4:30 PM  •  Hall 2",  "seats": 55, "tag": "U/A  •  1h 58m",   "price": 180},
    {"id": 7,  "title": "Whisper in Dark", "genre": "Horror",    "lang": "English",
     "rating": 7.8, "emoji": "👻", "color": "#2A0A2A",
     "show": "11:00 PM  •  Hall 3", "seats": 22, "tag": "A  •  1h 44m",     "price": 210},
    {"id": 8,  "title": "Yaar Mera",       "genre": "Drama",     "lang": "Marathi",
     "rating": 8.2, "emoji": "🎭", "color": "#4A2A6A",
     "show": "5:15 PM  •  Hall 1",  "seats": 67, "tag": "U/A  •  2h 08m",   "price": 190},
    {"id": 19, "title": "Kantara",         "genre": "Drama",     "lang": "Kannada",
     "rating": 9.1, "emoji": "🌿", "color": "#2A4A2A",
     "show": "6:00 PM  •  Hall 2",  "seats": 35, "tag": "A  •  2h 30m",     "price": 240},
    {"id": 20, "title": "RRR",             "genre": "Action",    "lang": "Telugu",
     "rating": 8.8, "emoji": "⚡", "color": "#8B1A10",
     "show": "7:30 PM  •  IMAX",    "seats": 20, "tag": "U/A  •  3h 02m",   "price": 300},
    {"id": 29, "title": "Oppenheimer",     "genre": "Biography", "lang": "English",
     "rating": 9.0, "emoji": "💥", "color": "#3A3010",
     "show": "5:00 PM  •  Hall 1",  "seats": 45, "tag": "R  •  3h 00m",     "price": 280},
    {"id": 31, "title": "Interstellar",    "genre": "Sci-Fi",    "lang": "English",
     "rating": 8.7, "emoji": "🌌", "color": "#0A2A4A",
     "show": "8:30 PM  •  IMAX",    "seats": 18, "tag": "PG-13  •  2h 49m", "price": 320},
    {"id": 35, "title": "3 Idiots",        "genre": "Comedy",    "lang": "Hindi",
     "rating": 9.0, "emoji": "🎓", "color": "#1A4A1A",
     "show": "4:00 PM  •  Hall 3",  "seats": 60, "tag": "PG  •  2h 50m",    "price": 200},
    {"id": 36, "title": "Dangal",          "genre": "Sports",    "lang": "Hindi",
     "rating": 8.8, "emoji": "🤼", "color": "#4A3010",
     "show": "5:45 PM  •  Hall 2",  "seats": 50, "tag": "PG  •  2h 41m",    "price": 210},
    {"id": 57, "title": "Andhadhun",       "genre": "Thriller",  "lang": "Hindi",
     "rating": 8.7, "emoji": "🎹", "color": "#1A1A2A",
     "show": "9:00 PM  •  Hall 1",  "seats": 28, "tag": "A  •  2h 19m",     "price": 230},
]

# Build a lookup by id
_DASH_MOVIE_MAP = {m["id"]: m for m in DASHBOARD_MOVIES}


# ─────────────────────────────────────────────
#  PUBLIC API
# ─────────────────────────────────────────────
def get_recommendations(user_prefs: dict, user_id: int = None,
                        n: int = 5, exclude_ids: list = None) -> list:
    """
    Main recommendation function.

    Parameters
    ----------
    user_prefs   : dict from onboarding (genres, languages, vibes, …)
    user_id      : int or None (future: look up in DB)
    n            : number of recommendations to return
    exclude_ids  : movie ids to exclude (e.g. already booked)

    Returns
    -------
    list of movie dicts (same shape as ALL_MOVIES in dashboard.py),
    sorted best-first, each augmented with:
      - ml_score       float  hybrid recommendation score
      - ml_confidence  str    "High" / "Medium" / "Low"
      - ml_reason      str    human-readable explanation
    """
    _load_artefacts()
    exclude = set(exclude_ids or [])

    # Determine candidate movies
    if _MOVIE_META and len(_MOVIE_META) > 0:
        candidates = [
            int(mid_str) for mid_str in _MOVIE_META
            if int(mid_str) not in exclude
        ]
    else:
        candidates = [m["id"] for m in DASHBOARD_MOVIES if m["id"] not in exclude]

    # Score every candidate
    scored = []
    for mid in candidates:
        if _MOVIE_META and str(mid) in _MOVIE_META:
            meta = _MOVIE_META[str(mid)]
        else:
            # Fallback: use dashboard catalogue
            dash = _DASH_MOVIE_MAP.get(mid)
            if not dash:
                continue
            meta = {
                "movie_id": mid, "title": dash["title"],
                "genre": dash["genre"], "language": dash["lang"],
                "rating": dash["rating"], "price": dash["price"],
                "seats_left": dash.get("seats", 30),
                "primary_mood": "Chill & Relax",
            }

        if _LOADED and _SIM_MATRIX is not None:
            score = _hybrid_score(mid, user_prefs)
        else:
            # Rule-based fallback
            score = _pref_score(meta, user_prefs)

        scored.append((mid, score, meta))

    # Sort descending
    scored.sort(key=lambda x: x[1], reverse=True)

    # Build result list in dashboard movie dict format
    results = []
    for mid, score, meta in scored[:n]:
        # Map back to a dashboard-compatible dict
        dash_m = _DASH_MOVIE_MAP.get(mid)

        if dash_m:
            movie_dict = dict(dash_m)
        else:
            # Construct from ML metadata
            genre_emoji = {
                "Action": "🔥", "Romance": "🌸", "Comedy": "😂",
                "Thriller": "🕵️", "Horror": "👻", "Sci-Fi": "🚀",
                "Animation": "🎮", "Drama": "🎭", "Mystery": "🔍",
                "Fantasy": "🧙", "Biography": "📖", "Sports": "⚽",
            }
            genre_color = {
                "Action": "#C03010", "Romance": "#C0204A", "Comedy": "#C07010",
                "Thriller": "#1A1A3E", "Horror": "#2A0A2A", "Sci-Fi": "#0A3A6A",
                "Animation": "#1E6CA8", "Drama": "#4A2A6A", "Mystery": "#1A3A1A",
                "Fantasy": "#3A1A4A", "Biography": "#3A3010", "Sports": "#0A3A20",
            }
            movie_dict = {
                "id":     mid,
                "title":  meta["title"],
                "genre":  meta["genre"],
                "lang":   meta["language"],
                "rating": meta["rating"],
                "emoji":  genre_emoji.get(meta["genre"], "🎬"),
                "color":  genre_color.get(meta["genre"], "#2A2424"),
                "show":   "Check schedule",
                "seats":  meta.get("seats_left", 30),
                "tag":    "—",
                "price":  meta["price"],
            }

        # Augment with ML metadata
        movie_dict["ml_score"]      = round(score, 4)
        movie_dict["ml_confidence"] = ("High"   if score >= 0.65 else
                                       "Medium" if score >= 0.40 else "Low")
        movie_dict["ml_reason"]     = _explain(meta, user_prefs, score)
        results.append(movie_dict)

    return results


def _explain(meta: dict, user_prefs: dict, score: float) -> str:
    """Generate a short human-readable explanation for the recommendation."""
    genres    = user_prefs.get("genres", [])
    languages = user_prefs.get("languages", [])
    vibes     = user_prefs.get("vibes", [])

    genre_match = meta.get("genre", "") in genres
    lang_match  = meta.get("language", "") in languages

    if genre_match and lang_match:
        return f"Matches your {meta['genre']} genre & {meta['language']} preference"
    elif genre_match:
        return f"Matches your favourite genre: {meta['genre']}"
    elif lang_match:
        return f"Available in your preferred language: {meta['language']}"
    elif score >= 0.5:
        vibe_str = vibes[0] if vibes else "your vibe"
        return f"Highly rated — fits your '{vibe_str}' mood"
    else:
        return f"Trending with ⭐ {meta.get('rating', '?')} rating"


def get_trending(n: int = 5) -> list:
    """Return top-n movies by global popularity (rating × bookings)."""
    _load_artefacts()
    if not _MOVIE_META:
        return sorted(DASHBOARD_MOVIES, key=lambda m: m["rating"], reverse=True)[:n]

    scored = []
    for mid_str, meta in _MOVIE_META.items():
        # Popularity = rating (6–10) × seat scarcity (fewer = more popular)
        rating   = meta.get("rating", 7.0)
        seats    = meta.get("seats_left", 50)
        pop_score = rating * (1 + (90 - seats) / 90 * 0.3)
        scored.append((int(mid_str), pop_score, meta))

    scored.sort(key=lambda x: x[1], reverse=True)
    results = []
    for mid, _, meta in scored[:n]:
        dash_m = _DASH_MOVIE_MAP.get(mid)
        results.append(dash_m if dash_m else {
            "id": mid, "title": meta["title"], "genre": meta["genre"],
            "lang": meta["language"], "rating": meta["rating"],
            "emoji": "🎬", "color": "#2A2424",
            "show": "—", "seats": meta["seats_left"],
            "tag": "—", "price": meta["price"],
        })
    return results


def get_similar(movie_id: int, n: int = 5) -> list:
    """Return n movies most similar to the given movie (content-based)."""
    _load_artefacts()
    if _SIM_MATRIX is None or _MID2IDX is None:
        return []

    target_idx = _MID2IDX.get(movie_id)
    if target_idx is None:
        return []

    sims = _SIM_MATRIX[target_idx]   # (n_movies,)
    top_indices = np.argsort(sims)[::-1]

    results = []
    for idx in top_indices:
        mid = _IDX2MID.get(idx)
        if mid == movie_id or mid is None:
            continue
        dash_m = _DASH_MOVIE_MAP.get(mid)
        if dash_m:
            d = dict(dash_m)
            d["similarity"] = round(float(sims[idx]), 3)
            results.append(d)
        if len(results) >= n:
            break
    return results


def get_model_stats() -> dict:
    """Return training stats dict for display in dashboard."""
    _load_artefacts()
    return _STATS or {}


# ─────────────────────────────────────────────
#  QUICK TEST
# ─────────────────────────────────────────────
if __name__ == "__main__":
    test_prefs = {
        "genres":    ["Action", "Sci-Fi", "Thriller"],
        "languages": ["English", "Hindi"],
        "vibes":     ["Thrills & Chills", "Mind-Bending"],
        "show_time": "Night (8PM–12AM)",
        "frequency": "2–3 times/week",
        "age_group": "18–25",
    }

    print("=== Recommendations for Action/Sci-Fi fan ===")
    recs = get_recommendations(test_prefs, n=5)
    for i, m in enumerate(recs, 1):
        print(f"  {i}. [{m['ml_confidence']:6s}] {m['title']:30s}"
              f"  score={m['ml_score']:.3f}  reason: {m['ml_reason']}")

    print("\n=== Trending ===")
    for m in get_trending(n=4):
        print(f"  ⭐ {m['rating']}  {m['title']}")

    print("\n=== Similar to movie_id=5 (Cosmic Drift) ===")
    for m in get_similar(5, n=3):
        print(f"  sim={m.get('similarity','?')}  {m['title']}")