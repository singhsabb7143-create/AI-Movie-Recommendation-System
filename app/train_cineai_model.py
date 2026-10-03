from __future__ import annotations

from pathlib import Path
import argparse
import json
import time

from cineai_model import CineAIRecommender


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MOVIES = PROJECT_ROOT / "data" / "movies.csv"
DEFAULT_CREDITS = PROJECT_ROOT / "data" / "credits.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "models" / "cineai_model.joblib"


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the local CineAI movie recommendation model.")
    parser.add_argument("--movies", default=str(DEFAULT_MOVIES))
    parser.add_argument("--credits", default=str(DEFAULT_CREDITS))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--max-features", type=int, default=35000)
    parser.add_argument("--components", type=int, default=256)
    args = parser.parse_args()

    movies_path = Path(args.movies)
    credits_path = Path(args.credits)
    output_path = Path(args.output)

    if not movies_path.exists():
        raise FileNotFoundError(f"Movies CSV not found: {movies_path}")
    if not credits_path.exists():
        raise FileNotFoundError(f"Credits CSV not found: {credits_path}")

    started = time.perf_counter()
    print("\
🎬 CineAI local ML training started...\
")
    print(f"Movies CSV : {movies_path}")
    print(f"Credits CSV: {credits_path}")
    print(f"Max TF-IDF features: {args.max_features}")
    print(f"SVD components     : {args.components}\
")

    model = CineAIRecommender.train(
        movies_csv=movies_path,
        credits_csv=credits_path,
        max_features=args.max_features,
        n_components=args.components,
    )
    model.save(output_path)

    metadata = {
        "model_type": "CineAI TF-IDF + TruncatedSVD + cosine retrieval",
        "model_version": 2,
        "movies_indexed": int(len(model.movies)),
        "tfidf_features": int(model.feature_count),
        "latent_dimensions": int(model.embeddings.shape[1]),
        "genres_indexed": sorted(model.genre_indices.keys()),
        "training_seconds": round(float(model.trained_seconds), 3),
        "total_seconds": round(time.perf_counter() - started, 3),
    }

    metadata_path = output_path.with_suffix(".json")
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print("\
✅ Training complete")
    print(f"Movies indexed : {metadata['movies_indexed']}")
    print(f"TF-IDF features: {metadata['tfidf_features']}")
    print(f"Latent dims    : {metadata['latent_dimensions']}")
    print(f"Training time  : {metadata['training_seconds']} sec")
    print(f"Model saved to : {output_path}")
    print(f"Metadata saved : {metadata_path}\
")

    print("Example check:")
    for genre in ["Action", "Comedy", "Drama"]:
        recs = model.recommend_genre(genre, n=5)
        titles = recs["title"].tolist()
        print(f"  {genre}: {titles}")


if __name__ == "__main__":
    main()
