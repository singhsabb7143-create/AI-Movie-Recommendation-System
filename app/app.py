import pandas as pd
import ast
import requests
import json
import random
import socket
import urllib3.util.connection as urllib3_connection
import streamlit as st

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from pathlib import Path

from cineai_model import load_model

st.set_page_config(
    page_title="CineAI — Movie Recommendation System",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

urllib3_connection.allowed_gai_family = lambda: socket.AF_INET


# TMDB API key
TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", "")


# Load data
movies = pd.read_csv("data/movies.csv")
credits = pd.read_csv("data/credits.csv")


# Convert genres and keywords
def convert(text):
    L = []

    for i in ast.literal_eval(text):
        L.append(i["name"])

    return L


movies["genres"] = movies["genres"].apply(convert)
movies["keywords"] = movies["keywords"].apply(convert)


# Convert cast
def convert_cast(text):
    L = []

    for i in ast.literal_eval(text):
        L.append(i["name"])

    return L[:3]


credits["cast"] = credits["cast"].apply(convert_cast)


# Handle missing overview
movies["overview"] = movies["overview"].fillna("")


# Merge datasets
movies = movies.merge(
    credits,
    left_on="id",
    right_on="movie_id"
)


# Keep required columns
movies = movies[
    ["movie_id", "title_x", "overview", "genres", "keywords", "cast"]
]

movies = movies.rename(
    columns={"title_x": "title"}
)


# Create tags
movies["tags"] = (
    movies["overview"]
    + movies["genres"].apply(lambda x: " ".join(x))
    + movies["keywords"].apply(lambda x: " ".join(x))
    + movies["cast"].apply(lambda x: " ".join(x))
)

movies["tags"] = movies["tags"].apply(
    lambda x: x.lower()
)


# Local ML recommendation model
MODEL_PATH = Path("models/cineai_model.joblib")


@st.cache_resource(show_spinner="Loading CineAI ML model...")
def get_recommender():
    return load_model(MODEL_PATH)


recommender = get_recommender()

# TMDB session with retry
tmdb_session = requests.Session()

retry_strategy = Retry(
    total=2,
    connect=2,
    read=2,
    backoff_factor=0.3,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)

adapter = HTTPAdapter(max_retries=retry_strategy)

tmdb_session.mount("https://", adapter)

tmdb_session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
})


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_poster(movie_id, movie_title):
    """
    Fetch a movie poster from TMDB.

    First tries the exact TMDB movie ID from the dataset.
    If that does not return a poster, falls back to title search.
    """

    if not TMDB_API_KEY:
        return None

    # 1. Exact TMDB movie ID lookup
    try:
        detail_url = f"https://api.themoviedb.org/3/movie/{int(movie_id)}"
        detail_params = {
            "api_key": TMDB_API_KEY
        }

        response = tmdb_session.get(
            detail_url,
            params=detail_params,
            timeout=5
        )

        if response.status_code == 200:
            poster_path = response.json().get("poster_path")

            if poster_path:
                return "https://image.tmdb.org/t/p/w500" + poster_path

    except (requests.exceptions.RequestException, ValueError, TypeError):
        pass

    # 2. Fallback: title search
    movie_title = str(movie_title).strip()
    search_title = movie_title

    if movie_title == "Alien³":
        search_title = "Alien 3"

    search_url = "https://api.themoviedb.org/3/search/movie"
    search_params = {
        "api_key": TMDB_API_KEY,
        "query": search_title,
        "include_adult": False
    }

    try:
        response = tmdb_session.get(
            search_url,
            params=search_params,
            timeout=20
        )

        if response.status_code != 200:
            return None

        results = response.json().get("results", [])

        # Exact title match first
        for result in results:
            result_title = str(result.get("title", "")).strip().lower()

            if result_title == search_title.lower():
                poster_path = result.get("poster_path")

                if poster_path:
                    return "https://image.tmdb.org/t/p/w500" + poster_path

        # Final fallback: first result that actually has a poster
        for result in results:
            poster_path = result.get("poster_path")

            if poster_path:
                return "https://image.tmdb.org/t/p/w500" + poster_path

    except requests.exceptions.RequestException:
        return None

    return None


def load_favorites():

    try:
        with open("favorites.json", "r") as file:
            return json.load(file)

    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_favorites(favorites):

    with open("favorites.json", "w") as file:
        json.dump(
            favorites,
            file,
            indent=4
        )

RECOMMENDATION_HISTORY_FILE = "recommendation_history.json"


def load_recommendation_history():
    try:
        with open(RECOMMENDATION_HISTORY_FILE, "r") as file:
            data = json.load(file)

        if isinstance(data, dict):
            return data

    except (FileNotFoundError, json.JSONDecodeError):
        pass

    return {}


def save_recommendation_history(history):
    with open(RECOMMENDATION_HISTORY_FILE, "w") as file:
        json.dump(
            history,
            file,
            indent=4
        )


def recommend_by_genre(selected_genre, generate_new=False):

    history_key = str(selected_genre)
    batch_key = f"recommendation_batch_{selected_genre}"

    # Load recommendation history from disk so it survives Streamlit refreshes.
    persistent_history = load_recommendation_history()
    stored_ids = persistent_history.get(history_key, [])

    if not isinstance(stored_ids, list):
        stored_ids = []

    # Keep current session state synchronized with the persistent history.
    st.session_state[f"used_movies_{selected_genre}"] = list(stored_ids)

    if generate_new or batch_key not in st.session_state:

        used_ids = {int(movie_id) for movie_id in stored_ids}

        # Core ranking comes entirely from the locally trained CineAI model.
        recommended_movies = recommender.recommend_genre(
            selected_genre,
            n=5,
            exclude_ids=used_ids
        )

        # If the category is exhausted, start a new cycle while avoiding only
        # the immediately previous batch.
        if len(recommended_movies) < 5:
            recent_ids = {int(movie_id) for movie_id in stored_ids[-5:]}

            recommended_movies = recommender.recommend_genre(
                selected_genre,
                n=5,
                exclude_ids=recent_ids
            )

            stored_ids = list(recent_ids)

        if recommended_movies.empty:
            st.warning(f"No locally ranked movies found for {selected_genre}.")
            st.session_state[batch_key] = []

            persistent_history[history_key] = stored_ids
            save_recommendation_history(persistent_history)
            return

        batch_ids = [
            int(movie_id)
            for movie_id in recommended_movies["movie_id"].tolist()
        ]

        # Store current batch in session.
        st.session_state[batch_key] = batch_ids

        # Persist history to disk so refresh/restart does not repeat prior batches.
        stored_ids.extend(batch_ids)
        persistent_history[history_key] = stored_ids
        save_recommendation_history(persistent_history)

    else:

        batch_ids = st.session_state[batch_key]

        recommended_movies = recommender.movies[
            recommender.movies["movie_id"].isin(batch_ids)
        ].copy()

        order_map = {movie_id: i for i, movie_id in enumerate(batch_ids)}
        recommended_movies["_batch_order"] = recommended_movies["movie_id"].map(order_map)
        recommended_movies = recommended_movies.sort_values("_batch_order")

    st.subheader(f"🎬 {selected_genre} Movie Recommendations")

    cols = st.columns(5)

    for index, row in enumerate(recommended_movies.itertuples(index=False)):
        movie_title = row.title
        movie_id = row.movie_id
        genres = row.genres

        poster = fetch_poster(movie_id, movie_title)

        rating = row.vote_average if getattr(row, "vote_average", 0) else None
        overview = row.overview or "No overview available."

        rating_text = "⭐ N/A"
        if rating is not None and float(rating) > 0:
            rating_text = f"⭐ {float(rating):.1f}/10"

        with cols[index]:
            if poster:
                st.image(poster, width=220)
            else:
                st.caption("Poster not available")

            if st.button(
                movie_title,
                key=f"details_{movie_id}",
                use_container_width=True
            ):
                st.session_state.selected_movie = {
                    "title": movie_title,
                    "movie_id": movie_id,
                    "poster": poster,
                    "rating": rating,
                    "rating_text": rating_text,
                    "genres": genres,
                    "overview": overview,
                    # Loaded lazily on the details page from TMDB.
                    "trailer_key": None,
                    "watch_providers": [],
                }

                st.switch_page("pages/movie_details_ml.py")

            st.markdown(
                f"""
                <div style=\"
                    text-align:center;
                    color:#fbbf24;
                    font-size:14px;
                    font-weight:800;
                    margin-top:8px;
                    min-height:24px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                \">
                    {rating_text}
                </div>
                """,
                unsafe_allow_html=True
            )

st.markdown(
    """
    <style>
    /* ===== Global Netflix-inspired theme ===== */
    .stApp {
        background:
            radial-gradient(circle at 18% 18%, rgba(229, 9, 20, 0.16), transparent 28%),
            radial-gradient(circle at 86% 8%, rgba(123, 20, 28, 0.16), transparent 25%),
            linear-gradient(180deg, #070707 0%, #0d0d0f 42%, #111111 100%);
        color: #ffffff;
    }

    [data-testid="stHeader"] {
        background: rgba(0, 0, 0, 0.25);
    }

    #MainMenu, footer {
        visibility: hidden;
    }

    .block-container {
        max-width: 1320px;
        padding-top: 1rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3, p, label, span, div {
        color: #ffffff;
    }

    /* Top navigation */
    .cine-nav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.35rem 0 1rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.09);
        margin-bottom: 0.4rem;
    }

    .cine-brand {
        font-size: 1.45rem;
        font-weight: 900;
        letter-spacing: -0.5px;
    }

    .cine-brand .accent {
        color: #e50914;
    }

    .cine-nav-right {
        color: #bdbdbd;
        font-size: 0.88rem;
    }

    /* Hero section */
    .hero {
        position: relative;
        min-height: 430px;
        margin-top: 1rem;
        margin-bottom: 1.3rem;
        padding: 3.3rem 4rem;
        border-radius: 24px;
        overflow: hidden;
        background:
            linear-gradient(90deg, rgba(0,0,0,0.94) 0%, rgba(0,0,0,0.73) 44%, rgba(0,0,0,0.32) 75%, rgba(0,0,0,0.72) 100%),
            radial-gradient(circle at 80% 28%, rgba(229,9,20,0.52), transparent 30%),
            linear-gradient(135deg, #161616 0%, #25151a 48%, #090909 100%);
        box-shadow: 0 26px 80px rgba(0,0,0,0.45);
        border: 1px solid rgba(255,255,255,0.08);
    }

    .hero:after {
        content: "";
        position: absolute;
        inset: 0;
        background:
            linear-gradient(135deg, transparent 0 48%, rgba(255,255,255,0.025) 49% 50%, transparent 51%),
            linear-gradient(45deg, transparent 0 60%, rgba(229,9,20,0.08) 61% 62%, transparent 63%);
        pointer-events: none;
    }

    .hero-content {
        position: relative;
        z-index: 2;
        max-width: 710px;
    }

    .hero-kicker {
        color: #e50914;
        font-weight: 800;
        letter-spacing: 2.4px;
        text-transform: uppercase;
        font-size: 0.78rem;
        margin-bottom: 0.7rem;
    }

    .hero-title {
        font-size: clamp(2.7rem, 5vw, 5.4rem);
        font-weight: 900;
        line-height: 0.96;
        letter-spacing: -2.6px;
        margin: 0;
    }

    .hero-title .line2 {
        color: #e50914;
    }

    .hero-desc {
        color: #d4d4d4;
        font-size: 1.03rem;
        line-height: 1.65;
        max-width: 620px;
        margin-top: 1.1rem;
    }

    .hero-meta {
        color: #9e9e9e;
        font-size: 0.9rem;
        margin-top: 0.8rem;
    }

    .hero-pill {
        display: inline-block;
        margin-top: 1rem;
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.13);
        padding: 0.45rem 0.72rem;
        border-radius: 999px;
        font-size: 0.78rem;
        color: #ececec;
    }

    /* Selector area */
    .discover-box {
        background: linear-gradient(180deg, rgba(255,255,255,0.055), rgba(255,255,255,0.025));
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        padding: 1.25rem 1.35rem 1.35rem;
        margin-bottom: 1.6rem;
        box-shadow: 0 16px 50px rgba(0,0,0,0.18);
    }

    .discover-title {
        font-size: 1.18rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }

    .discover-subtitle {
        font-size: 0.87rem;
        color: #a8a8a8;
        margin-bottom: 0.9rem;
    }

    .stSelectbox label {
        color: #d6d6d6 !important;
        font-weight: 700 !important;
    }

    [data-baseweb="select"] > div {
        background-color: #181818 !important;
        border: 1px solid #353535 !important;
        border-radius: 12px !important;
        color: white !important;
    }

    [data-baseweb="select"] * {
        color: white !important;
    }

    /* Fix Streamlit dropdown menu: dark background + visible white options */
    [data-baseweb="popover"],
    [data-baseweb="menu"],
    [data-baseweb="listbox"],
    [role="listbox"] {
        background-color: #181818 !important;
        color: #ffffff !important;
        border: 1px solid #353535 !important;
        border-radius: 12px !important;
    }

    [data-baseweb="menu"] li,
    [data-baseweb="listbox"] li,
    [role="option"] {
        background-color: #181818 !important;
        color: #ffffff !important;
    }

    [data-baseweb="menu"] li:hover,
    [data-baseweb="listbox"] li:hover,
    [role="option"]:hover {
        background-color: #2a2a2a !important;
        color: #ffffff !important;
    }

    [aria-selected="true"] {
        background-color: #333333 !important;
        color: #ffffff !important;
    }

    /* Buttons */
    .stButton > button {
        border: 0 !important;
        border-radius: 10px !important;
        background: #e50914 !important;
        color: white !important;
        font-size: 0.98rem !important;
        font-weight: 800 !important;
        min-height: 46px !important;
        transition: all 0.18s ease !important;
        box-shadow: 0 8px 26px rgba(229,9,20,0.18) !important;
    }

    .stButton > button p {
        color: white !important;
        font-weight: 800 !important;
    }

    .stButton > button:hover {
        background: #f6121d !important;
        transform: translateY(-1px);
        box-shadow: 0 12px 30px rgba(229,9,20,0.28) !important;
    }

    /* Recommendation section */
    .section-heading {
        display: flex;
        align-items: end;
        justify-content: space-between;
        margin-top: 1rem;
        margin-bottom: 0.85rem;
        gap: 1rem;
    }

    .section-heading h2 {
        font-size: 1.5rem;
        margin: 0;
        font-weight: 850;
        letter-spacing: -0.4px;
    }

    .section-heading p {
        margin: 0;
        color: #8d8d8d !important;
        font-size: 0.82rem;
    }

    /* Movie cards */
    .stButton > button {
        min-height: 52px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        line-height: 1.15 !important;
        padding: 0.45rem 0.65rem !important;
    }

    .stButton > button p {
        width: 100% !important;
        text-align: center !important;
        line-height: 1.15 !important;
        margin: 0 !important;
    }

    [data-testid="stImage"] img {
        width: 220px !important;
        max-width: 100% !important;
        height: 330px !important;
        object-fit: cover !important;
        border-radius: 14px !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        box-shadow: 0 14px 34px rgba(0,0,0,0.32);
    }

    [data-testid="stImage"] img:hover {
        transform: scale(1.025);
        box-shadow: 0 20px 38px rgba(0,0,0,0.46);
    }

    /* Favorites */
    .fav-card {
        background: #171717;
        border: 1px solid #2a2a2a;
        border-radius: 12px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.55rem;
    }

    .footer-note {
        text-align: center;
        color: #666 !important;
        font-size: 0.78rem;
        margin-top: 3rem;
        padding-top: 1rem;
        border-top: 1px solid rgba(255,255,255,0.07);
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="cine-nav">
        <div class="cine-brand">Cine<span class="accent">AI</span></div>
        <div class="cine-nav-right">AI-powered movie discovery · TMDB data</div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <section class="hero">
        <div class="hero-content">
            <div class="hero-kicker">Your personal movie discovery space</div>
            <h1 class="hero-title">Find your next<br><span class="line2">favorite movie.</span></h1>
            <p class="hero-desc">
                Pick a category and CineAI will rank five movie options using its local ML model,
                then use TMDB only for poster and on-demand movie details.
            </p>
            <div class="hero-meta">Local ML ranking · TMDB metadata · Movie details · Favorites</div>
            <div class="hero-pill">🎬 Local ML model · Python · Streamlit · TMDB metadata</div>
        </div>
    </section>
    """,
    unsafe_allow_html=True
)

if "favorites" not in st.session_state:
    st.session_state.favorites = load_favorites()

st.markdown(
    """
    <div class="discover-box">
        <div class="discover-title">What do you feel like watching?</div>
        <div class="discover-subtitle">Choose a category, then press the button to generate a fresh batch.</div>
    """,
    unsafe_allow_html=True
)

genre_options = [
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
    "Thriller"
]

st.markdown(
    f'<div style="color:#9f9f9f;font-size:0.78rem;margin:-0.35rem 0 0.75rem;">🧠 Local ML engine · {len(recommender.movies):,} movies indexed · recommendations run without TMDB scoring</div>',
    unsafe_allow_html=True
)

selected_genre = st.selectbox(
    "Movie category",
    genre_options,
    label_visibility="visible"
)

if "show_recommendations" not in st.session_state:
    st.session_state.show_recommendations = False

if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = None

if "active_genre" not in st.session_state:
    st.session_state.active_genre = None

new_recommendation_requested = st.button(
    "▶  Recommend Movies",
    use_container_width=True
)

if new_recommendation_requested:
    st.session_state.show_recommendations = True
    st.session_state.selected_movie = None
    st.session_state.active_genre = selected_genre

st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.show_recommendations and st.session_state.active_genre:
    st.markdown(
        f"""
        <div class="section-heading">
            <div>
                <h2>Because you chose {st.session_state.active_genre}</h2>
                <p>Ranked by the locally trained CineAI ML model.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    recommend_by_genre(
        st.session_state.active_genre,
        generate_new=new_recommendation_requested
    )

if st.session_state.favorites:
    st.markdown(
        """
        <div class="section-heading" style="margin-top:2.1rem;">
            <div>
                <h2>My Favorites</h2>
                <p>Your saved movie picks.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    for favorite in st.session_state.favorites:
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(
                f'<div class="fav-card">🎬 {favorite}</div>',
                unsafe_allow_html=True
            )
        with col2:
            if st.button("Remove", key=f"remove_{favorite}", use_container_width=True):
                st.session_state.favorites.remove(favorite)
                save_favorites(st.session_state.favorites)
                st.rerun()

st.markdown(
    '<div class="footer-note">CineAI · Local ML Recommendation System · TMDB metadata for details</div>',
    unsafe_allow_html=True
)