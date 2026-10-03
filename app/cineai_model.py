from __future__ import annotations

from pathlib import Path
from typing import Iterable

import ast
import json
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import normalize
from sklearn.decomposition import TruncatedSVD


MODEL_VERSION = 2


def _safe_list(value):
    if isinstance(value, list):
        return value
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return []
    try:
        parsed = ast.literal_eval(str(value))
        return parsed if isinstance(parsed, list) else []
    except (ValueError, SyntaxError, TypeError):
        return []


def _names(value, limit=None):
    items = _safe_list(value)
    names = []
    for item in items:
        if isinstance(item, dict) and item.get("name"):
            names.append(str(item["name"]).strip())
    if limit:
        names = names[:limit]
    return names


def _director(value):
    items = _safe_list(value)
    for item in items:
        if isinstance(item, dict) and item.get("job") == "Director" and item.get("name"):
            return str(item["name"]).strip()
    return ""


def _repeat(value: str, weight: int) -> str:
    value = (value or "").strip()
    return " ".join([value] * max(weight, 1)) if value else ""


def _minmax(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float32)
    lo = float(values.min()) if len(values) else 0.0
    hi = float(values.max()) if len(values) else 1.0
    if hi - lo < 1e-9:
        return np.zeros_like(values, dtype=np.float32)
    return (values - lo) / (hi - lo)


class CineAIRecommender:
    """Locally trained content-retrieval recommender for CineAI.

    Training:
    - TF-IDF over weighted movie text features
    - TruncatedSVD for compact latent features
    - cosine nearest-neighbour retrieval
    - genre centroids + quality signals for category ranking
    """

    def __init__(
        self,
        movies: pd.DataFrame,
        vectorizer: TfidfVectorizer,
        svd: TruncatedSVD,
        embeddings: np.ndarray,
        knn: NearestNeighbors,
        genre_indices: dict[str, np.ndarray],
        genre_centroids: dict[str, np.ndarray],
        quality_score: np.ndarray,
        specificity_score: np.ndarray,
        feature_count: int,
        trained_seconds: float,
    ) -> None:
        self.movies = movies.reset_index(drop=True)
        self.vectorizer = vectorizer
        self.svd = svd
        self.embeddings = embeddings.astype(np.float32, copy=False)
        self.knn = knn
        self.genre_indices = genre_indices
        self.genre_centroids = genre_centroids
        self.quality_score = quality_score.astype(np.float32, copy=False)
        self.specificity_score = specificity_score.astype(np.float32, copy=False)
        self.feature_count = int(feature_count)
        self.trained_seconds = float(trained_seconds)

    @classmethod
    def train(
        cls,
        movies_csv: str | Path,
        credits_csv: str | Path,
        max_features: int = 35000,
        n_components: int = 256,
    ) -> "CineAIRecommender":
        started = time.perf_counter()

        movies_raw = pd.read_csv(movies_csv)
        credits = pd.read_csv(credits_csv)

        # Clean credit fields. The standard TMDB-5000 file contains JSON-like strings.
        credits = credits.copy()
        credits["cast_names"] = credits["cast"].map(lambda x: _names(x, limit=5))
        credits["director"] = credits["crew"].map(_director)

        movies = movies_raw.merge(
            credits[["movie_id", "cast_names", "director"]],
            left_on="id",
            right_on="movie_id",
            how="inner",
        ).copy()

        movies["overview"] = movies["overview"].fillna("").astype(str)
        movies["tagline"] = movies.get("tagline", "").fillna("").astype(str) if "tagline" in movies else ""
        movies["title"] = movies["title"].fillna("").astype(str)
        movies["vote_average"] = pd.to_numeric(movies.get("vote_average", 0), errors="coerce").fillna(0.0)
        movies["vote_count"] = pd.to_numeric(movies.get("vote_count", 0), errors="coerce").fillna(0.0)
        movies["popularity"] = pd.to_numeric(movies.get("popularity", 0), errors="coerce").fillna(0.0)

        movies["genre_list"] = movies["genres"].map(lambda x: _names(x))
        movies["keyword_list"] = movies["keywords"].map(lambda x: _names(x))
        movies["cast_list"] = movies["cast_names"]
        movies["director"] = movies["director"].fillna("").astype(str)
        movies["original_language"] = movies.get("original_language", "").fillna("").astype(str)

        def make_text(row) -> str:
            parts = [
                _repeat(row["overview"], 3),
                _repeat(" ".join(row["genre_list"]), 5),
                _repeat(" ".join(row["keyword_list"]), 2),
                _repeat(" ".join(row["cast_list"]), 2),
                _repeat(row["director"], 4),
                _repeat(row["tagline"], 1),
                _repeat(row["title"], 1),
                _repeat(row["original_language"], 1),
            ]
            return " ".join(part for part in parts if part).lower()

        texts = movies.apply(make_text, axis=1)

        vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.95,
            sublinear_tf=True,
            strip_accents="unicode",
            stop_words="english",
            dtype=np.float32,
        )

        tfidf = vectorizer.fit_transform(texts)

        component_count = min(
            int(n_components),
            max(tfidf.shape[0] - 1, 2),
            max(tfidf.shape[1] - 1, 2),
        )

        svd = TruncatedSVD(n_components=component_count, random_state=42)
        embeddings = svd.fit_transform(tfidf)
        embeddings = normalize(embeddings, norm="l2", copy=False).astype(np.float32)

        knn = NearestNeighbors(
            n_neighbors=min(50, len(movies)),
            metric="cosine",
            algorithm="brute",
            n_jobs=-1,
        )
        knn.fit(embeddings)

        # IMDb-style weighted rating to reduce noise from tiny vote counts.
        ratings = movies["vote_average"].to_numpy(dtype=np.float32)
        counts = movies["vote_count"].to_numpy(dtype=np.float32)
        C = float(ratings.mean()) if len(ratings) else 0.0
        m = float(np.quantile(counts, 0.75)) if len(counts) else 0.0
        if m > 0:
            weighted = (counts / (counts + m)) * ratings + (m / (counts + m)) * C
        else:
            weighted = ratings

        popularity = np.log1p(movies["popularity"].to_numpy(dtype=np.float32))
        quality_score = (0.75 * _minmax(weighted)) + (0.25 * _minmax(popularity))

        genre_counts = movies["genre_list"].map(len).to_numpy(dtype=np.float32)
        specificity_score = 1.0 / np.maximum(genre_counts, 1.0)
        specificity_score = _minmax(specificity_score)

        genre_indices: dict[str, np.ndarray] = {}
        genre_centroids: dict[str, np.ndarray] = {}
        for idx, genres in enumerate(movies["genre_list"]):
            for genre in genres:
                genre_indices.setdefault(genre, []).append(idx)

        for genre, indices in list(genre_indices.items()):
            arr = np.asarray(indices, dtype=np.int32)
            genre_indices[genre] = arr
            centroid = embeddings[arr].mean(axis=0)
            norm = float(np.linalg.norm(centroid))
            if norm > 0:
                centroid = centroid / norm
            genre_centroids[genre] = centroid.astype(np.float32)

        keep_cols = [
            "movie_id", "title", "overview", "genre_list", "keyword_list",
            "cast_list", "director", "vote_average", "vote_count",
            "popularity", "release_date", "original_language", "tagline",
        ]
        for col in keep_cols:
            if col not in movies.columns:
                movies[col] = ""

        movie_table = movies[keep_cols].copy()
        movie_table = movie_table.rename(columns={"genre_list": "genres", "keyword_list": "keywords", "cast_list": "cast"})

        elapsed = time.perf_counter() - started
        return cls(
            movies=movie_table,
            vectorizer=vectorizer,
            svd=svd,
            embeddings=embeddings,
            knn=knn,
            genre_indices=genre_indices,
            genre_centroids=genre_centroids,
            quality_score=quality_score,
            specificity_score=specificity_score,
            feature_count=len(vectorizer.vocabulary_),
            trained_seconds=elapsed,
        )

    def recommend_genre(
        self,
        genre: str,
        n: int = 5,
        exclude_ids: Iterable[int] | None = None,
    ) -> pd.DataFrame:
        genre = str(genre).strip()
        if genre not in self.genre_indices:
            return self.movies.head(0).copy()

        exclude = {int(x) for x in (exclude_ids or [])}
        candidate_idx = [
            int(i)
            for i in self.genre_indices[genre]
            if int(self.movies.iloc[int(i)]["movie_id"]) not in exclude
        ]
        if not candidate_idx:
            return self.movies.head(0).copy()

        centroid = self.genre_centroids[genre]
        idx_array = np.asarray(candidate_idx, dtype=np.int32)

        semantic = self.embeddings[idx_array] @ centroid
        total_score = (
        0.75 * semantic
        + 0.20 * self.quality_score[idx_array]
        + 0.05 * self.specificity_score[idx_array]
        )

        # Small deterministic shuffle among very close scores improves variety
        # while keeping the ranking model-driven.
        order = np.argsort(-total_score, kind="stable")
        ordered_idx = idx_array[order]

        # MMR-style diversification for the final batch.
        pool = list(ordered_idx[: min(80, len(ordered_idx))])
        selected: list[int] = []
        remaining = set(pool)
        lambda_value = 0.88

        while remaining and len(selected) < n:
            best_idx = None
            best_value = -1e9
            for idx in remaining:
               base = float(
    0.75 * (self.embeddings[idx] @ centroid)
    + 0.20 * self.quality_score[idx]
    + 0.05 * self.specificity_score[idx]
)
            if not selected:
                    diversity_penalty = 0.0
            else:
                    diversity_penalty = max(
                        float(self.embeddings[idx] @ self.embeddings[j])
                        for j in selected
                    )
            mmr = lambda_value * base - (1.0 - lambda_value) * diversity_penalty
            if mmr > best_value:
                    best_value = mmr
                    best_idx = idx
            selected.append(int(best_idx))
            remaining.remove(int(best_idx))

        result = self.movies.iloc[selected].copy().reset_index(drop=True)
        return result

    def similar_movies(self, movie_id: int, n: int = 10) -> pd.DataFrame:
        matches = self.movies.index[self.movies["movie_id"] == movie_id].tolist()
        if not matches:
            return self.movies.head(0).copy()
        idx = matches[0]
        distances, indices = self.knn.kneighbors(self.embeddings[idx:idx + 1], n_neighbors=min(n + 1, len(self.movies)))
        result_indices = [int(i) for i in indices[0] if int(i) != idx][:n]
        return self.movies.iloc[result_indices].reset_index(drop=True)

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "version": MODEL_VERSION,
                "model": self,
            },
            path,
            compress=3,
        )

    @staticmethod
    def load(path: str | Path) -> "CineAIRecommender":
        payload = joblib.load(path)
        if isinstance(payload, dict) and "model" in payload:
            model = payload["model"]
        else:
            model = payload
        if not isinstance(model, CineAIRecommender):
            raise TypeError("Invalid CineAI model artifact.")
        return model


def load_model(path: str | Path) -> CineAIRecommender:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Model file not found: {path}. Run 'python app/train_cineai_model.py' first."
        )
    return CineAIRecommender.load(path)
