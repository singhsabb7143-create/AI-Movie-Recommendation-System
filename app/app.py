import pandas as pd
import ast
import requests
import json
import socket
import urllib3.util.connection as urllib3_connection
import streamlit as st

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

urllib3_connection.allowed_gai_family = lambda: socket.AF_INET


# TMDB API key
TMDB_API_KEY = st.secrets["TMDB_API_KEY"]


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


# Vectorization
cv = CountVectorizer(
    max_features=5000,
    stop_words="english"
)

vectors = cv.fit_transform(
    movies["tags"]
).toarray()


# Similarity matrix
similarity = cosine_similarity(vectors)


# TMDB session with retry
tmdb_session = requests.Session()

retry_strategy = Retry(
    total=5,
    connect=5,
    read=5,
    backoff_factor=1,
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
def fetch_poster(movie_title):

    movie_title = movie_title.strip()

    search_title = movie_title

    if movie_title == "Alien³":
        search_title = "Alien 3"

    url = "https://api.themoviedb.org/3/search/movie"

    params = {
        "api_key": TMDB_API_KEY,
        "query": search_title
    }

    try:
        response = tmdb_session.get(
            url,
            params=params,
            timeout=20
        )

        if response.status_code != 200:
            return None

        data = response.json()
        results = data.get("results", [])

        # Exact title match first
        for result in results:
            title = result.get("title", "").strip().lower()

            if title == search_title.lower():
                poster_path = result.get("poster_path")

                if poster_path:
                    return (
                        "https://image.tmdb.org/t/p/w500"
                        + poster_path
                    )

        # Fallback: first result with poster
        for result in results:
            poster_path = result.get("poster_path")

            if poster_path:
                return (
                    "https://image.tmdb.org/t/p/w500"
                    + poster_path
                )

    except requests.exceptions.RequestException:
        return None

    return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_rating(movie_title):

    movie_title = movie_title.strip()

    search_title = movie_title

    if movie_title == "Alien³":
        search_title = "Alien 3"

    url = "https://api.themoviedb.org/3/search/movie"

    params = {
        "api_key": TMDB_API_KEY,
        "query": search_title
    }

    try:
        response = tmdb_session.get(
            url,
            params=params,
            timeout=20
        )

        if response.status_code != 200:
            return None

        data = response.json()
        results = data.get("results", [])

        # Exact title match
        for result in results:
            title = result.get("title", "").strip().lower()

            if title == search_title.lower():
                return result.get("vote_average")

        # Fallback
        if results:
            return results[0].get("vote_average")

    except requests.exceptions.RequestException:
        return None

    return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_overview(movie_title):

    movie_title = movie_title.strip()

    search_title = movie_title

    if movie_title == "Alien³":
        search_title = "Alien 3"

    url = "https://api.themoviedb.org/3/search/movie"

    params = {
        "api_key": TMDB_API_KEY,
        "query": search_title
    }

    try:
        response = tmdb_session.get(
            url,
            params=params,
            timeout=20
        )

        if response.status_code != 200:
            return ""

        data = response.json()
        results = data.get("results", [])

        for result in results:
            title = result.get("title", "").strip().lower()

            if title == search_title.lower():
                return result.get("overview", "")

        if results:
            return results[0].get("overview", "")

    except requests.exceptions.RequestException:
        return ""

    return ""


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_trailer(movie_id):
    """
    Return a YouTube video key for the best available trailer.
    Preference order:
    1. Official YouTube trailer
    2. Any YouTube trailer
    3. Official YouTube teaser
    4. Any YouTube teaser
    5. Any YouTube video
    """
    url = (
        f"https://api.themoviedb.org/3/movie/"
        f"{int(movie_id)}/videos"
    )

    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US"
    }

    try:
        response = tmdb_session.get(
            url,
            params=params,
            timeout=20
        )

        if response.status_code != 200:
            return None

        videos = response.json().get("results", [])

        youtube_videos = [
            video
            for video in videos
            if video.get("site") == "YouTube"
            and video.get("key")
        ]

        for video in youtube_videos:
            if (
                video.get("type") == "Trailer"
                and video.get("official") is True
            ):
                return video.get("key")

        for video in youtube_videos:
            if video.get("type") == "Trailer":
                return video.get("key")

        for video in youtube_videos:
            if (
                video.get("type") == "Teaser"
                and video.get("official") is True
            ):
                return video.get("key")

        for video in youtube_videos:
            if video.get("type") == "Teaser":
                return video.get("key")

        if youtube_videos:
            return youtube_videos[0].get("key")

    except requests.exceptions.RequestException:
        return None

    return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_watch_providers(movie_id):

    url = (
        f"https://api.themoviedb.org/3/movie/"
        f"{int(movie_id)}/watch/providers"
    )

    params = {
        "api_key": TMDB_API_KEY
    }

    try:
        response = tmdb_session.get(
            url,
            params=params,
            timeout=20
        )

        if response.status_code != 200:
            return []

        data = response.json()

        india_data = (
            data.get("results", {})
            .get("IN", {})
        )

        providers = []

        for category in [
            "flatrate",
            "free",
            "ads",
            "rent",
            "buy"
        ]:

            for provider in india_data.get(
                category,
                []
            ):

                provider_name = provider.get(
                    "provider_name"
                )

                if (
                    provider_name
                    and provider_name not in providers
                ):
                    providers.append(provider_name)

        return providers

    except requests.exceptions.RequestException:
        return []


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


def recommend_by_genre(selected_genre):

    matching_movies = movies[
        movies["genres"].apply(
            lambda genre_list: selected_genre in genre_list
        )
    ]

    if matching_movies.empty:
        st.warning(f"No movies found for {selected_genre}.")
        return

    recommended_movies = matching_movies.head(5)

    st.subheader(f"🎬 {selected_genre} Movie Recommendations")

    cols = st.columns(5)

    for index, row in enumerate(
        recommended_movies.itertuples()
    ):

        movie_title = row.title
        movie_id = row.movie_id
        genres = row.genres

        poster = fetch_poster(movie_title)
        rating = fetch_rating(movie_title)
        overview = fetch_overview(movie_title)
        trailer_key = fetch_trailer(movie_id)
        watch_providers = fetch_watch_providers(movie_id)

        rating_text = "⭐ N/A"
        if rating is not None:
            rating_text = f"⭐ {rating:.1f}/10"

        with cols[index]:

            if poster:
                st.image(poster, width=170)
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
                    "overview": overview or "No overview available.",
                    "trailer_key": trailer_key,
                    "watch_providers": watch_providers,
                }

                st.switch_page("pages/movie_details.py")

            st.markdown(
                f"""
                <div style="
                    text-align:center;
                    color:#fbbf24;
                    font-size:14px;
                    font-weight:bold;
                    margin-top:6px;
                ">
                    {rating_text}
                </div>
                """,
                unsafe_allow_html=True
            )


st.markdown(
    """
    <style>
    .stApp {
        background-color: #111827;
    }

    h1, h2, h3, p, label {
        color: white !important;
    }

    .stSelectbox label {
        color: white !important;
        font-weight: bold;
    }

    .stButton > button {
        width: 100%;
        border-radius: 10px;
        font-size: 18px;
        font-weight: bold;
        color: #111827 !important;
        background-color: white !important;
    }

    .stButton > button p {
        color: #111827 !important;
    }

    .stButton > button:hover {
        color: white !important;
        background-color: #374151 !important;
    }

    .stButton > button:hover p {
        color: white !important;
    }

    .reco-title {
        text-align: center;
        font-weight: bold;
        color: white !important;
        margin-top: 8px;
        min-height: 72px;
        line-height: 1.4;
    }

    .genre-badge {
        display: inline-block;
        background-color: #374151;
        color: #e5e7eb;
        padding: 4px 8px;
        margin: 2px;
        border-radius: 12px;
        font-size: 11px;
    }

    .stImage img {
        border-radius: 12px;
        transition: transform 0.2s ease;
    }

    .stImage img:hover {
        transform: scale(1.05);
    }
    </style>
    """,
    unsafe_allow_html=True
)


st.markdown(
    "<h1 style='text-align: center;'>"
    "🎬 AI Movie Recommendation System"
    "</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<p style='text-align: center;'>"
    "Choose a movie type and get 5 recommendations based on your selected category."
    "</p>",
    unsafe_allow_html=True
)


if "favorites" not in st.session_state:
    st.session_state.favorites = load_favorites()


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

selected_genre = st.selectbox(
    "🎭 What type of movie do you want to watch?",
    genre_options
)


if "show_recommendations" not in st.session_state:
    st.session_state.show_recommendations = False


if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = None


if st.button("🎯 Recommend Movies"):
    st.session_state.show_recommendations = True
    st.session_state.selected_movie = None

if st.session_state.show_recommendations:
    recommend_by_genre(selected_genre)


if st.session_state.favorites:

    st.subheader("⭐ My Favorites")

    for favorite in st.session_state.favorites:

        col1, col2 = st.columns([4, 1])

        with col1:
            st.write(f"🎬 {favorite}")

        with col2:

            if st.button(
                "❌",
                key=f"remove_{favorite}"
            ):
                st.session_state.favorites.remove(
                    favorite
                )

                save_favorites(
                    st.session_state.favorites
                )

                st.rerun()