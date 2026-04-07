"""
ml/train_model.py
=================
Trains a HYBRID recommendation model combining:

  1. Content-Based Filtering  (TF-IDF / cosine similarity on movie features)
  2. Collaborative Filtering  (NMF matrix factorisation on user–item ratings)
  3. User-Preference Scorer   (weights items by onboarding prefs)

Outputs serialised artefacts to ml/models/:
  ├── content_similarity.npy   — (n_movies × n_movies) cosine sim matrix
  ├── nmf_model.pkl            — fitted NMF model
  ├── nmf_user_factors.npy     — W matrix (user latent factors)
  ├── nmf_item_factors.npy     — H matrix (item latent factors)
  ├── movie_index.json         — movie_id → matrix row mapping
  ├── movie_meta.json          — movie_id → metadata dict
  ├── model_stats.json         — training stats for display
  └── scaler.pkl               — StandardScaler for content features

Run:
    python ml/train_model.py
"""

import os, sys, json, pickle, warnings
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, normalize
from sklearn.decomposition import NMF
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split

warnings.filterwarnings("ignore")

_THIS   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR  = os.path.join(_THIS, "data")
MODEL_DIR = os.path.join(_THIS, "models")
os.makedirs(MODEL_DIR, exist_ok=True)


# ─────────────────────────────────────────────
#  STEP 1 — CONTENT-BASED MODEL
# ─────────────────────────────────────────────
def train_content_model(movies_df: pd.DataFrame):
    """
    Build a (n_movies × n_movies) cosine similarity matrix from
    one-hot genre / language / mood features + normalised rating & price.
    """
    print("\n[1/3] Training Content-Based Filtering …")

    # Collect feature columns
    genre_cols = [c for c in movies_df.columns if c.startswith("genre_")]
    lang_cols  = [c for c in movies_df.columns if c.startswith("lang_")]
    mood_cols  = [c for c in movies_df.columns if c.startswith("mood_")]

    feature_df = movies_df[genre_cols + lang_cols + mood_cols].copy()

    # Add scaled numeric features
    scaler = StandardScaler()
    num_features = scaler.fit_transform(
        movies_df[["rating", "price"]].values.astype(float)
    )
    feature_df["rating_scaled"] = num_features[:, 0]
    feature_df["price_scaled"]  = num_features[:, 1]

    feature_matrix = feature_df.values.astype(float)

    # L2-normalise so cosine_similarity = dot product
    feature_matrix_norm = normalize(feature_matrix, norm="l2")

    # (n × n) cosine similarity
    sim_matrix = cosine_similarity(feature_matrix_norm)

    # Save
    np.save(os.path.join(MODEL_DIR, "content_similarity.npy"), sim_matrix)
    with open(os.path.join(MODEL_DIR, "scaler.pkl"), "wb") as f:
        pickle.dump(scaler, f)

    print(f"  ✓ Feature matrix: {feature_matrix.shape}")
    print(f"  ✓ Similarity matrix: {sim_matrix.shape}")
    print(f"  ✓ Avg similarity: {sim_matrix.mean():.4f}")
    return sim_matrix, scaler


# ─────────────────────────────────────────────
#  STEP 2 — COLLABORATIVE FILTERING (NMF)
# ─────────────────────────────────────────────
def train_cf_model(interactions_df: pd.DataFrame, movies_df: pd.DataFrame):
    """
    Build a user–item rating matrix and factorise with NMF.
    Synthetic users 1-150.  Real DB users get handled in recommender.py.
    """
    print("\n[2/3] Training Collaborative Filtering (NMF) …")

    # Map movie_ids to consecutive indices
    movie_ids = sorted(movies_df["movie_id"].tolist())
    mid2idx   = {mid: i for i, mid in enumerate(movie_ids)}
    idx2mid   = {i: mid for mid, i in mid2idx.items()}

    user_ids  = sorted(interactions_df["user_id"].unique().tolist())
    uid2idx   = {uid: i for i, uid in enumerate(user_ids)}

    n_users = len(user_ids)
    n_items = len(movie_ids)

    # Build rating matrix (filled with 0 where unobserved)
    R = np.zeros((n_users, n_items), dtype=np.float32)
    for _, row in interactions_df.iterrows():
        ui = uid2idx[row["user_id"]]
        mi = mid2idx.get(int(row["movie_id"]))
        if mi is not None:
            R[ui, mi] = row["rating"]

    print(f"  Rating matrix: {R.shape}  sparsity={100*(R==0).mean():.1f}%")

    # Train / test split on observed ratings
    obs_mask = R > 0
    R_train  = R.copy()
    R_test   = np.zeros_like(R)

    for ui in range(n_users):
        obs_cols = np.where(obs_mask[ui])[0]
        if len(obs_cols) >= 4:
            test_cols = np.random.choice(obs_cols, size=max(1, len(obs_cols)//5),
                                         replace=False)
            R_train[ui, test_cols] = 0
            R_test[ui, test_cols]  = R[ui, test_cols]

    # Fit NMF
    nmf = NMF(
        n_components=15,
        init="nndsvda",
        max_iter=500,
        random_state=42,
        beta_loss="frobenius",
        solver="mu",
        alpha_W=0.01,
        alpha_H=0.01,
    )
    W = nmf.fit_transform(R_train)   # user factors  (n_users × k)
    H = nmf.components_              # item factors  (k × n_items)

    # Evaluate RMSE on held-out ratings
    R_pred = W @ H
    test_obs = R_test > 0
    if test_obs.sum() > 0:
        rmse = np.sqrt(mean_squared_error(R_test[test_obs], R_pred[test_obs]))
        print(f"  ✓ NMF RMSE on held-out: {rmse:.4f}")

    # Save
    np.save(os.path.join(MODEL_DIR, "nmf_user_factors.npy"), W)
    np.save(os.path.join(MODEL_DIR, "nmf_item_factors.npy"), H)
    with open(os.path.join(MODEL_DIR, "nmf_model.pkl"), "wb") as f:
        pickle.dump(nmf, f)

    # Save index mappings
    with open(os.path.join(MODEL_DIR, "movie_index.json"), "w") as f:
        json.dump({"mid2idx": mid2idx, "idx2mid": {str(k): v for k,v in idx2mid.items()}}, f)

    print(f"  ✓ NMF components: {nmf.n_components_}")
    print(f"  ✓ Reconstruction error: {nmf.reconstruction_err_:.4f}")
    return nmf, W, H, mid2idx, idx2mid


# ─────────────────────────────────────────────
#  STEP 3 — MOVIE METADATA STORE
# ─────────────────────────────────────────────
def build_meta_store(movies_df: pd.DataFrame):
    """Persist a clean metadata dict for each movie — used by the dashboard."""
    print("\n[3/3] Building movie metadata store …")

    meta = {}
    for _, row in movies_df.iterrows():
        mid = int(row["movie_id"])
        meta[str(mid)] = {
            "movie_id": mid,
            "title":    row["title"],
            "genre":    row["genre"],
            "language": row["language"],
            "rating":   float(row["rating"]),
            "price":    int(row["price"]),
            "seats_left": int(row["seats_left"]),
            "primary_mood": row["primary_mood"],
        }

    with open(os.path.join(MODEL_DIR, "movie_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    print(f"  ✓ Metadata stored for {len(meta)} movies")
    return meta


# ─────────────────────────────────────────────
#  STEP 4 — GENRE / LANG PREFERENCE PROFILE
# ─────────────────────────────────────────────
def build_genre_profiles(interactions_df: pd.DataFrame,
                         movies_df: pd.DataFrame):
    """
    Compute average rating per (pref_genre, movie_genre) pair.
    Used by the hybrid scorer in recommender.py.
    """
    merged = interactions_df.merge(
        movies_df[["movie_id","genre","language","rating"]],
        on="movie_id", suffixes=("_user","_movie")
    )

    # Explode pref_genres
    rows = []
    for _, r in merged.iterrows():
        for pg in str(r["pref_genres"]).split("|"):
            rows.append({
                "pref_genre":   pg.strip(),
                "movie_genre":  r["genre"],
                "rating_user":  r["rating_user"],
            })
    profile_df = pd.DataFrame(rows)
    genre_affinity = (profile_df.groupby(["pref_genre","movie_genre"])
                                ["rating_user"].mean()
                                .unstack(fill_value=5.0))

    genre_affinity.to_csv(os.path.join(MODEL_DIR, "genre_affinity.csv"))
    print(f"  ✓ Genre affinity matrix: {genre_affinity.shape}")
    return genre_affinity


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  Smart Movie — ML Model Training Pipeline")
    print("=" * 60)

    # Load datasets
    movies_path = os.path.join(DATA_DIR, "movies.csv")
    inter_path  = os.path.join(DATA_DIR, "interactions.csv")

    if not os.path.exists(movies_path):
        print("[ERROR] movies.csv not found. Run generate_dataset.py first.")
        sys.exit(1)

    movies_df       = pd.read_csv(movies_path)
    interactions_df = pd.read_csv(inter_path)

    print(f"\nLoaded {len(movies_df)} movies, {len(interactions_df)} interactions")

    # Train
    sim_matrix, scaler     = train_content_model(movies_df)
    nmf, W, H, mid2idx, _  = train_cf_model(interactions_df, movies_df)
    meta                   = build_meta_store(movies_df)
    _                      = build_genre_profiles(interactions_df, movies_df)

    # Save model stats
    stats = {
        "n_movies":        len(movies_df),
        "n_interactions":  len(interactions_df),
        "n_users_train":   int(interactions_df["user_id"].nunique()),
        "nmf_components":  int(nmf.n_components_),
        "nmf_error":       float(nmf.reconstruction_err_),
        "content_features": sim_matrix.shape[1],
        "avg_sim":         float(sim_matrix.mean()),
        "genres_covered":  sorted(movies_df["genre"].unique().tolist()),
        "langs_covered":   sorted(movies_df["language"].unique().tolist()),
    }
    with open(os.path.join(MODEL_DIR, "model_stats.json"), "w") as f:
        json.dump(stats, f, indent=2)

    print("\n" + "=" * 60)
    print("  ✅ Training complete! Artefacts saved to ml/models/")
    print("=" * 60)
    for fname in sorted(os.listdir(MODEL_DIR)):
        sz = os.path.getsize(os.path.join(MODEL_DIR, fname))
        print(f"  {fname:40s}  {sz/1024:.1f} KB")


if __name__ == "__main__":
    main()