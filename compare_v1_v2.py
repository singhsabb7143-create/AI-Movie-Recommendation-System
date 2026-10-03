import sys
from pathlib import Path

import numpy as np

# app folder ko Python path mein add karo
sys.path.insert(0, str(Path(__file__).parent / "app"))

from cineai_model import load_model


MODEL_PATH = Path("models/cineai_model.joblib")

GENRES = [
    "Action",
    "Adventure",
    "Animation",
    "Comedy",
    "Crime",
    "Drama",
    "Fantasy",
    "Horror",
    "Mystery",
    "Romance",
    "Thriller",
]


model = load_model(MODEL_PATH)


def rank_movies(model, genre, semantic_weight, quality_weight, specificity_weight, n=5):
    if genre not in model.genre_indices:
        return []

    candidate_idx = np.asarray(
        model.genre_indices[genre],
        dtype=np.int32
    )

    centroid = model.genre_centroids[genre]

    semantic = model.embeddings[candidate_idx] @ centroid

    # Same scoring logic, only weights change.
    base_scores = (
        semantic_weight * semantic
        + quality_weight * model.quality_score[candidate_idx]
        + specificity_weight * model.specificity_score[candidate_idx]
    )

    order = np.argsort(-base_scores, kind="stable")
    ordered_idx = candidate_idx[order]

    pool = list(ordered_idx[: min(80, len(ordered_idx))])

    selected = []
    remaining = set(pool)

    lambda_value = 0.88

    while remaining and len(selected) < n:
        best_idx = None
        best_value = -1e9

        for idx in remaining:
            semantic_value = float(
                model.embeddings[idx] @ centroid
            )

            base = (
                semantic_weight * semantic_value
                + quality_weight * float(model.quality_score[idx])
                + specificity_weight * float(model.specificity_score[idx])
            )

            if not selected:
                diversity_penalty = 0.0
            else:
                diversity_penalty = max(
                    float(model.embeddings[idx] @ model.embeddings[j])
                    for j in selected
                )

            mmr = (
                lambda_value * base
                - (1.0 - lambda_value) * diversity_penalty
            )

            if mmr > best_value:
                best_value = mmr
                best_idx = idx

        selected.append(int(best_idx))
        remaining.remove(int(best_idx))

    return model.movies.iloc[selected]["title"].tolist()


print("=" * 70)
print("🎬 CineAI V1 vs V2 MODEL COMPARISON")
print("=" * 70)

v1_total_changes = 0

for genre in GENRES:

    v1 = rank_movies(
        model,
        genre,
        semantic_weight=0.80,
        quality_weight=0.15,
        specificity_weight=0.05,
    )

    v2 = rank_movies(
        model,
        genre,
        semantic_weight=0.75,
        quality_weight=0.20,
        specificity_weight=0.05,
    )

    same = v1 == v2

    if not same:
        v1_total_changes += 1

    print(f"\n🎬 {genre}")

    print("V1:")
    for i, title in enumerate(v1, start=1):
        print(f"  {i}. {title}")

    print("V2:")
    for i, title in enumerate(v2, start=1):
        print(f"  {i}. {title}")

    print(
        "Result:",
        "UNCHANGED" if same else "CHANGED"
    )


print("\n" + "=" * 70)
print("📊 COMPARISON SUMMARY")
print("=" * 70)

print(f"Genres tested : {len(GENRES)}")
print(f"Genres changed: {v1_total_changes}")
print(f"Genres same   : {len(GENRES) - v1_total_changes}")

print("\nV1 weights:")
print("  Semantic     = 80%")
print("  Quality      = 15%")
print("  Specificity  = 5%")

print("\nV2 weights:")
print("  Semantic     = 75%")
print("  Quality      = 20%")
print("  Specificity  = 5%")

print("=" * 70)