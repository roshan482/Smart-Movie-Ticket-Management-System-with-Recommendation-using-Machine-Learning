"""
setup_ml.py
===========
Run this script ONCE to initialise the entire ML pipeline:

    python setup_ml.py

It will:
  1. Check/install required packages (scikit-learn, pandas, numpy, scipy)
  2. Generate the synthetic movie + interaction dataset (ml/data/)
  3. Train the hybrid recommendation model   (ml/models/)
  4. Run a smoke-test to verify the engine works

After this, the dashboard will automatically load the trained model
and serve real ML recommendations on every login.
"""

import subprocess, sys, os

ROOT = os.path.dirname(os.path.abspath(__file__))


def _banner(msg):
    print("\n" + "=" * 62)
    print(f"  {msg}")
    print("=" * 62)


# ── Step 0: Dependencies ──────────────────────────────────────────────────────
_banner("Step 0 / 3 — Checking Python dependencies")
REQUIRED = ["scikit-learn", "pandas", "numpy", "scipy"]
for pkg in REQUIRED:
    try:
        __import__(pkg.replace("-", "_").split("_")[0])
        print(f"  ✓  {pkg}")
    except ImportError:
        print(f"  ⬇  Installing {pkg} …")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", pkg,
            "--break-system-packages", "-q"
        ])
        print(f"  ✓  {pkg} installed")


# ── Step 1: Generate dataset ──────────────────────────────────────────────────
_banner("Step 1 / 3 — Generating synthetic dataset")
result = subprocess.run(
    [sys.executable, os.path.join(ROOT, "generate_dataset.py")],
    capture_output=False
)
if result.returncode != 0:
    print("[ERROR] Dataset generation failed.")
    sys.exit(1)


# ── Step 2: Train model ───────────────────────────────────────────────────────
_banner("Step 2 / 3 — Training ML models")
result = subprocess.run(
    [sys.executable, os.path.join(ROOT, "train_model.py")],
    capture_output=False
)
if result.returncode != 0:
    print("[ERROR] Model training failed.")
    sys.exit(1)


# ── Step 3: Smoke-test ────────────────────────────────────────────────────────
_banner("Step 3 / 3 — Smoke-testing the recommender engine")
sys.path.insert(0, os.path.join(ROOT, "ml"))
from recommender import get_recommendations, get_trending, get_similar

test_prefs = {
    "genres":    ["Action", "Sci-Fi"],
    "languages": ["English"],
    "vibes":     ["Thrills & Chills"],
    "age_group": "18–25",
}

recs = get_recommendations(test_prefs, n=5)
print(f"\n  🎯 Top 5 recommendations for Action/Sci-Fi fan:")
for i, m in enumerate(recs, 1):
    print(f"     {i}. [{m['ml_confidence']:6s}] {m['title']:30s}  "
          f"score={m['ml_score']:.3f}")

trending = get_trending(n=3)
print(f"\n  📈 Trending now:")
for m in trending:
    print(f"     ⭐ {m['rating']}  {m['title']}")

similar = get_similar(5, n=3)
print(f"\n  🔗 Movies similar to 'Cosmic Drift':")
for m in similar:
    print(f"     sim={m.get('similarity','?')}  {m['title']}")

_banner("✅  ML setup complete!  Launch the app with:  python main.py")
print("""
  The dashboard will now serve real ML recommendations powered by:
  ┌─────────────────────────────────────────────────────────────┐
  │  Content-Based Filtering  (cosine similarity on features)   │
  │  Collaborative Filtering  (NMF matrix factorisation)        │
  │  User-Preference Scorer   (onboarding prefs → score)        │
  │  Genre Affinity Matrix    (trained from interaction data)    │
  │  HYBRID SCORE = 0.35×content + 0.30×CF + 0.35×pref         │
  └─────────────────────────────────────────────────────────────┘
""")