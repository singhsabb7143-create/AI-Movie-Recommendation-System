import pandas as pd
import ast
import requests
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


@st.cache_data(ttl=3600)
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

# Recommendation function
def recommend(movie):

    index = movies[
        movies["title"] == movie
    ].index[0]

    distances = similarity[index]

    movie_list = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x: x[1]
    )[1:6]

    st.subheader("🎬 Recommended Movies")

    for i in movie_list:

        movie_title = movies.iloc[i[0]].title

        st.write(f"🎬 {movie_title}")

        poster = fetch_poster(movie_title)

        if poster:
            st.image(
                poster,
                width=200
            )
        else:
            st.write("🖼️ Poster not available")


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

.stButton > button:hover {
    color: white !important;
    background-color: #374151 !important;
}

.stButton > button p {
    color: #111827 !important;
}

.stButton > button:hover p {
    color: white !important;
}

    </style>
    """,
    unsafe_allow_html=True
)

# Title
st.markdown(
    "<h1 style='text-align: center;'>"
    "🎬 AI Movie Recommendation System"
    "</h1>",
    unsafe_allow_html=True
)


# Description
st.markdown(
    "<p style='text-align: center;'>"
    "Select a movie and get 5 similar movie recommendations."
    "</p>",
    unsafe_allow_html=True
)


# Movie selection
movie_name = st.selectbox(
    "🎬 Choose a movie:",
    movies["title"].values
)


# Recommendation button
if st.button("🎯 Recommend Movies"):
    recommend(movie_name)