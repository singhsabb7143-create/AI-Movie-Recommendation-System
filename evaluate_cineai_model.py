import sys
import time
from pathlib import Path

# app folder ko Python import path mein add karo
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


print("=" * 60)
print("🎬 CineAI ML MODEL EVALUATION")
print("=" * 60)

# Load trained model
start_load = time.perf_counter()

model = load_model(MODEL_PATH)

load_time = time.perf_counter() - start_load

print("\n✅ Model loaded successfully")
print(f"Movies indexed : {len(model.movies):,}")
print(f"TF-IDF features: {model.feature_count:,}")
print(f"Model load time : {load_time:.4f} sec")


print("\n" + "-" * 60)
print("GENRE RECOMMENDATION TEST")
print("-" * 60)

total_movies = 0
successful_genres = 0
latencies = []

for genre in GENRES:

    start = time.perf_counter()

    recommendations = model.recommend_genre(
        genre,
        5
    )

    elapsed = time.perf_counter() - start
    latencies.append(elapsed)

    count = len(recommendations)
    total_movies += count

    if count > 0:
        successful_genres += 1

    titles = recommendations["title"].tolist()

    print(f"\n{genre}")
    print(f"  Movies returned : {count}")
    print(f"  Response time   : {elapsed:.4f} sec")

    for i, title in enumerate(titles, start=1):
        print(f"    {i}. {title}")


average_latency = sum(latencies) / len(latencies)


print("\n" + "=" * 60)
print("📊 EVALUATION SUMMARY")
print("=" * 60)

print(f"Genres tested       : {len(GENRES)}")
print(f"Successful genres   : {successful_genres}/{len(GENRES)}")
print(f"Movies returned     : {total_movies}")
print(f"Average response    : {average_latency:.4f} sec")
print(f"Fastest response    : {min(latencies):.4f} sec")
print(f"Slowest response    : {max(latencies):.4f} sec")

print("\nNote:")
print(
    "This project does not contain a labelled ground-truth recommendation "
    "dataset, so accuracy/precision/recall are not reported. "
    "This test measures model loading, recommendation latency, "
    "and successful category retrieval."
)

print("=" * 60)