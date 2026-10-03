import json
import html
import requests
import streamlit as st

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

st.set_page_config(
    page_title="CineAI — Movie Details",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", "")

tmdb_session = requests.Session()
retry_strategy = Retry(
    total=3,
    connect=3,
    read=3,
    backoff_factor=0.5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)
tmdb_session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
tmdb_session.headers.update({"User-Agent": "CineAI/1.0", "Accept": "application/json"})


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_trailer(movie_id):
    if not TMDB_API_KEY or not movie_id:
        return None
    url = f"https://api.themoviedb.org/3/movie/{int(movie_id)}/videos"
    try:
        response = tmdb_session.get(
            url,
            params={"api_key": TMDB_API_KEY, "language": "en-US"},
            timeout=12,
        )
        if response.status_code != 200:
            return None
        videos = response.json().get("results", [])
        youtube = [v for v in videos if v.get("site") == "YouTube" and v.get("key")]
        for kind, official in [("Trailer", True), ("Trailer", None), ("Teaser", True), ("Teaser", None)]:
            for video in youtube:
                if video.get("type") == kind and (official is None or video.get("official") is official):
                    return video.get("key")
        return youtube[0].get("key") if youtube else None
    except requests.RequestException:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_watch_providers(movie_id):
    if not TMDB_API_KEY or not movie_id:
        return []
    url = f"https://api.themoviedb.org/3/movie/{int(movie_id)}/watch/providers"
    try:
        response = tmdb_session.get(url, params={"api_key": TMDB_API_KEY}, timeout=12)
        if response.status_code != 200:
            return []
        india = response.json().get("results", {}).get("IN", {})
        providers = []
        for category in ["flatrate", "free", "ads", "rent", "buy"]:
            for item in india.get(category, []):
                name = item.get("provider_name")
                if name and name not in providers:
                    providers.append(name)
        return providers
    except requests.RequestException:
        return []



def load_favorites():
    try:
        with open("favorites.json", "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_favorites(favorites):
    with open("favorites.json", "w") as file:
        json.dump(favorites, file, indent=4)


# -----------------------
# CineAI theme
# -----------------------
st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at 82% 8%, rgba(229,9,20,0.18), transparent 28%),
            radial-gradient(circle at 10% 20%, rgba(116,16,22,0.16), transparent 25%),
            linear-gradient(180deg, #070707 0%, #101010 50%, #070707 100%);
        color: #fff;
    }

    [data-testid="stHeader"] { background: rgba(0,0,0,0.28); }
    #MainMenu, footer { visibility: hidden; }

    .block-container {
        max-width: 1280px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    h1, h2, h3, h4, p, label { color: #fff !important; }

    .cine-nav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.3rem;
    }

    .cine-logo {
        color: #e50914;
        font-size: 1.55rem;
        font-weight: 900;
        letter-spacing: -0.7px;
    }

    .cine-logo span {
        color: #fff;
        font-weight: 700;
    }

    .cine-nav-pill {
        padding: 0.42rem 0.8rem;
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 999px;
        background: rgba(255,255,255,0.04);
        color: #cfcfcf;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .detail-hero {
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 22px;
        padding: 2rem 2.2rem 1.8rem;
        margin-bottom: 1.5rem;
        background:
            linear-gradient(90deg, rgba(0,0,0,0.92) 0%, rgba(0,0,0,0.62) 58%, rgba(105,0,0,0.28) 100%);
        box-shadow: 0 18px 50px rgba(0,0,0,0.35);
    }

    .detail-kicker {
        color: #e50914 !important;
        font-size: 0.82rem;
        font-weight: 900;
        letter-spacing: 0.13em;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }

    .detail-title {
        margin: 0;
        font-size: clamp(2rem, 4vw, 3.6rem);
        line-height: 1.05;
        letter-spacing: -1.7px;
        font-weight: 900;
    }

    .detail-subtitle {
        margin-top: 0.8rem;
        color: #bdbdbd !important;
        font-size: 1rem;
    }

    .hero-rating {
        display: inline-block;
        margin-top: 1rem;
        padding: 0.42rem 0.78rem;
        border-radius: 999px;
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.13);
        color: #ffd54a !important;
        font-size: 0.95rem;
        font-weight: 800;
    }

    /* Native Streamlit bordered containers */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(180deg, rgba(255,255,255,0.045), rgba(255,255,255,0.018));
        border: 1px solid rgba(255,255,255,0.10) !important;
        border-radius: 22px !important;
        box-shadow: 0 18px 44px rgba(0,0,0,0.28);
    }

    .poster-shell {
        padding: 0.55rem;
        border-radius: 18px;
        background: linear-gradient(180deg, rgba(229,9,20,0.72), rgba(229,9,20,0.08));
        box-shadow: 0 18px 55px rgba(229,9,20,0.15);
    }

    .poster-shell img { border-radius: 14px !important; }

    .section-pill {
        display: inline-block;
        padding: 0.42rem 0.82rem;
        border-radius: 999px;
        border: 1px solid rgba(229,9,20,0.42);
        background: rgba(229,9,20,0.10);
        color: #ff5860 !important;
        font-size: 0.76rem;
        font-weight: 900;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 0.6rem;
    }

    .detail-heading {
        color: #fff !important;
        font-size: 1.25rem;
        font-weight: 850;
        margin-bottom: 0.65rem;
    }

    .detail-overview {
        color: #d0d0d0 !important;
        font-size: 0.98rem;
        line-height: 1.82;
    }

    .genre-badge, .provider-badge {
        display: inline-block;
        padding: 0.38rem 0.7rem;
        margin: 0.2rem 0.25rem 0.2rem 0;
        border-radius: 999px;
        font-size: 0.77rem;
        font-weight: 700;
    }

    .genre-badge {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.10);
        color: #eee;
    }

    .provider-badge {
        background: rgba(229,9,20,0.14);
        border: 1px solid rgba(229,9,20,0.32);
        color: #ffd7d9;
    }

    .availability-box, .preview-box {
        margin-top: 1rem;
        padding: 1rem;
        border-radius: 16px;
        background: rgba(0,0,0,0.24);
        border: 1px solid rgba(255,255,255,0.07);
    }

    .availability-title, .preview-title {
        color: #fff !important;
        font-weight: 800;
        margin-bottom: 0.35rem;
    }

    .availability-note, .trailer-note {
        color: #9f9f9f !important;
        font-size: 0.8rem;
        margin-top: 0.4rem;
    }

    .stButton > button {
        width: 100%;
        min-height: 48px;
        border-radius: 10px;
        font-size: 0.98rem;
        font-weight: 800;
        color: #fff !important;
        background: #e50914 !important;
        border: 1px solid #e50914 !important;
        box-shadow: 0 8px 22px rgba(229,9,20,0.18);
    }

    .stButton > button p { color: #fff !important; }

    .stButton > button:hover {
        background: #f6121d !important;
        border-color: #f6121d !important;
        color: #fff !important;
    }

    .secondary-wrap .stButton > button {
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.14) !important;
        box-shadow: none;
    }

    .secondary-wrap .stButton > button:hover {
        background: rgba(255,255,255,0.15) !important;
        border-color: rgba(255,255,255,0.24) !important;
    }

    .already-saved {
        padding: 0.75rem 0.9rem;
        border-radius: 11px;
        background: rgba(229,9,20,0.10);
        border: 1px solid rgba(229,9,20,0.22);
        color: #ffd9db;
        font-size: 0.9rem;
        font-weight: 700;
        margin-bottom: 0.8rem;
    }

    .footer-note {
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid rgba(255,255,255,0.08);
        color: #676767;
        text-align: center;
        font-size: 0.8rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# -----------------------
# Selected movie guard
# -----------------------
if "selected_movie" not in st.session_state or not st.session_state.selected_movie:
    with st.container(border=True):
        st.markdown('<div class="section-pill">CineAI</div>', unsafe_allow_html=True)
        st.markdown('<div class="detail-title">No movie selected.</div>', unsafe_allow_html=True)
        st.markdown('<div class="detail-subtitle">Choose a movie from your recommendations to open its full details.</div>', unsafe_allow_html=True)
        if st.button("← Back to Recommendations", use_container_width=True):
            st.switch_page("app.py")
    st.stop()


movie = st.session_state.selected_movie

title = str(movie.get("title", "Movie"))
poster = movie.get("poster")
rating_text = str(movie.get("rating_text", "⭐ N/A"))
genres = movie.get("genres", []) or []
overview = str(movie.get("overview", "No overview available."))
movie_id = movie.get("movie_id")
trailer_key = movie.get("trailer_key") or fetch_trailer(movie_id)
watch_providers = movie.get("watch_providers", []) or fetch_watch_providers(movie_id)

safe_title = html.escape(title)
safe_overview = html.escape(overview).replace("\n", "<br>")

# -----------------------
# Header / hero
# -----------------------
st.markdown(
    """
    <div class="cine-nav">
        <div class="cine-logo">CineAI<span> · MOVIE DISCOVERY</span></div>
        <div class="cine-nav-pill">Movie Details</div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <div class="detail-hero">
        <div class="detail-kicker">Now viewing</div>
        <div class="detail-title">{safe_title}</div>
        <div class="detail-subtitle">Explore the story, genres, India availability and trailer.</div>
        <div class="hero-rating">{html.escape(rating_text)}</div>
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------
# Details area
# -----------------------
col1, col2 = st.columns([0.85, 1.55], gap="large")

with col1:
    with st.container(border=True):
        if poster:
            st.markdown('<div class="poster-shell">', unsafe_allow_html=True)
            st.image(poster, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                "<div style='padding:5rem 1rem; text-align:center; color:#777;'>Poster not available</div>",
                unsafe_allow_html=True
            )

with col2:
    with st.container(border=True):
        st.markdown('<div class="section-pill">Movie Details</div>', unsafe_allow_html=True)
        st.markdown('<div class="detail-heading">Genres</div>', unsafe_allow_html=True)

        genre_html = "".join(
            f"<span class='genre-badge'>{html.escape(str(genre))}</span>"
            for genre in genres
        )
        st.markdown(
            genre_html or "<span class='genre-badge'>Genre not available</span>",
            unsafe_allow_html=True
        )

        st.markdown('<div class="section-pill" style="margin-top:1.1rem;">Story</div>', unsafe_allow_html=True)
        st.markdown(
            f"<div class='detail-overview'>{safe_overview}</div>",
            unsafe_allow_html=True
        )

        st.markdown('<div class="availability-box">', unsafe_allow_html=True)
        st.markdown('<div class="availability-title">📺 Available in India</div>', unsafe_allow_html=True)

        if watch_providers:
            provider_html = "".join(
                f"<span class='provider-badge'>{html.escape(str(provider))}</span>"
                for provider in watch_providers
            )
            st.markdown(provider_html, unsafe_allow_html=True)
            st.markdown(
                "<div class='availability-note'>Provider information is supplied by TMDB and may change over time.</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                "<div class='availability-note'>No India-region provider information was returned for this title.</div>",
                unsafe_allow_html=True
            )

        st.markdown('</div>', unsafe_allow_html=True)

        favorites = load_favorites()
        st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)

        if title in favorites:
            st.markdown(
                '<div class="already-saved">⭐ This movie is already in your Favorites.</div>',
                unsafe_allow_html=True
            )
        else:
            if st.button("⭐ Add to Favorites", key="add_favorite", use_container_width=True):
                if title not in favorites:
                    favorites.append(title)
                    save_favorites(favorites)
                    st.success("Added to Favorites!")
                    st.rerun()

        st.markdown('<div class="secondary-wrap">', unsafe_allow_html=True)
        if st.button("← Back to Recommendations", key="back_recommendations", use_container_width=True):
            st.switch_page("app.py")
        st.markdown('</div>', unsafe_allow_html=True)

# -----------------------
# Trailer / preview
# -----------------------
st.markdown('<div style="height:1.3rem;"></div>', unsafe_allow_html=True)

with st.container(border=True):
    st.markdown('<div class="section-pill">Watch Preview</div>', unsafe_allow_html=True)
    st.markdown('<div class="detail-heading">🎬 Trailer</div>', unsafe_allow_html=True)

    if trailer_key:
        trailer_embed_url = f"https://www.youtube.com/embed/{trailer_key}"
        st.iframe(trailer_embed_url, height=540)
    else:
        st.markdown(
            '<div class="trailer-note">🎬 Trailer is not available for this movie.</div>',
            unsafe_allow_html=True
        )

st.markdown(
    '<div class="footer-note">CineAI · Local ML Recommendation System · TMDB for live detail metadata</div>',
    unsafe_allow_html=True
)
