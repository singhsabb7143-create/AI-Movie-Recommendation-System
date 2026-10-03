import json
import html
import streamlit as st


st.set_page_config(
    page_title="CineAI — Movie Details",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def load_favorites():
    try:
        with open("favorites.json", "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_favorites(favorites):
    with open("favorites.json", "w") as file:
        json.dump(favorites, file, indent=4)


# =========================================================
# CineAI / Netflix-inspired theme
# =========================================================
st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at 82% 10%, rgba(229,9,20,0.18), transparent 28%),
            radial-gradient(circle at 12% 18%, rgba(112,18,24,0.15), transparent 24%),
            linear-gradient(180deg, #090909 0%, #101010 48%, #090909 100%);
        color: #ffffff;
    }

    [data-testid="stHeader"] {
        background: rgba(0,0,0,0.35);
    }

    #MainMenu, footer {
        visibility: hidden;
    }

    .block-container {
        max-width: 1280px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    h1, h2, h3, h4, p, label {
        color: #ffffff !important;
    }

    /* -----------------------------------------------------
       Top navigation
       ----------------------------------------------------- */
    .cine-nav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.25rem;
    }

    .cine-logo {
        color: #e50914;
        font-size: 1.55rem;
        font-weight: 900;
        letter-spacing: -0.8px;
    }

    .cine-logo span {
        color: #ffffff;
        font-weight: 700;
    }

    .cine-nav-pill {
        display: inline-block;
        padding: 0.42rem 0.8rem;
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 999px;
        background: rgba(255,255,255,0.045);
        color: #cfcfcf;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    /* -----------------------------------------------------
       Hero
       ----------------------------------------------------- */
    .detail-hero {
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 22px;
        padding: 2rem 2.2rem 1.8rem;
        margin-bottom: 1.5rem;
        background:
            linear-gradient(
                90deg,
                rgba(0,0,0,0.88) 0%,
                rgba(0,0,0,0.58) 56%,
                rgba(102,0,0,0.28) 100%
            );
        box-shadow: 0 18px 50px rgba(0,0,0,0.35);
    }

    .detail-kicker {
        color: #e50914 !important;
        font-size: 0.78rem;
        font-weight: 900;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    .detail-title {
        margin: 0.25rem 0 0;
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

    /* -----------------------------------------------------
       Main panels
       ----------------------------------------------------- */
    .poster-shell {
        padding: 0.55rem;
        border-radius: 20px;
        background: linear-gradient(
            180deg,
            rgba(229,9,20,0.72),
            rgba(229,9,20,0.06)
        );
        box-shadow: 0 18px 55px rgba(229,9,20,0.15);
    }

    .poster-shell img {
        border-radius: 15px !important;
    }

    /* New: dedicated Movie Details heading box */
    .details-title-box {
        margin-bottom: 0.9rem;
        padding: 0.85rem 1.05rem;
        border-radius: 15px;
        background:
            linear-gradient(
                90deg,
                rgba(229,9,20,0.22),
                rgba(255,255,255,0.035)
            );
        border: 1px solid rgba(229,9,20,0.40);
        box-shadow: 0 10px 30px rgba(229,9,20,0.10);
    }

    .details-title-box .title {
        color: #ffffff !important;
        font-size: 1.45rem;
        font-weight: 900;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        line-height: 1.1;
    }

    .details-title-box .bar {
        width: 72px;
        height: 4px;
        margin-top: 0.5rem;
        border-radius: 999px;
        background: #e50914;
    }

    /* Real Streamlit content boxes */
    .section-card {
        padding: 1.1rem 1.15rem;
        border-radius: 17px;
        background: linear-gradient(
            180deg,
            rgba(255,255,255,0.045),
            rgba(255,255,255,0.018)
        );
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 14px 36px rgba(0,0,0,0.22);
    }

    /* Highlighted section heading pills */
    .section-heading {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.45rem 0.72rem;
        margin-bottom: 0.7rem;
        border-radius: 10px;
        background: rgba(229,9,20,0.12);
        border: 1px solid rgba(229,9,20,0.32);
        color: #ff4b55 !important;
        font-size: 0.78rem;
        font-weight: 900;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    .section-heading-white {
        color: #ffffff !important;
        font-size: 1.28rem;
        font-weight: 850;
        margin-bottom: 0.7rem;
    }

    .detail-overview {
        color: #d0d0d0 !important;
        font-size: 0.98rem;
        line-height: 1.82;
    }

    .genre-badge,
    .provider-badge {
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
        color: #eeeeee;
    }

    .provider-badge {
        background: rgba(229,9,20,0.14);
        border: 1px solid rgba(229,9,20,0.32);
        color: #ffd7d9;
    }

    .availability-note,
    .trailer-note {
        color: #9f9f9f !important;
        font-size: 0.82rem;
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

    .trailer-heading {
        color: #ffffff !important;
        font-size: 1.25rem;
        font-weight: 850;
        margin-bottom: 0.85rem;
    }

    /* Buttons */
    .stButton > button {
        width: 100%;
        min-height: 48px;
        border-radius: 10px;
        font-size: 0.98rem;
        font-weight: 800;
        color: #ffffff !important;
        background: #e50914 !important;
        border: 1px solid #e50914 !important;
        box-shadow: 0 8px 22px rgba(229,9,20,0.18);
    }

    .stButton > button p {
        color: #ffffff !important;
    }

    .stButton > button:hover {
        background: #f6121d !important;
        border-color: #f6121d !important;
        color: #ffffff !important;
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
    unsafe_allow_html=True,
)


# =========================================================
# Selected movie guard
# =========================================================
if "selected_movie" not in st.session_state or not st.session_state.selected_movie:
    st.markdown(
        """
        <div class="detail-hero">
            <div class="detail-kicker">CineAI</div>
            <div class="detail-title">No movie selected.</div>
            <div class="detail-subtitle">
                Choose a movie from your recommendations to open its full details.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("← Back to Recommendations", use_container_width=True):
        st.switch_page("app.py")

    st.stop()


movie = st.session_state.selected_movie

title = str(movie.get("title", "Movie"))
poster = movie.get("poster")
rating_text = str(movie.get("rating_text", "⭐ N/A"))
genres = movie.get("genres", []) or []
overview = str(movie.get("overview", "No overview available."))
trailer_key = movie.get("trailer_key")
watch_providers = movie.get("watch_providers", []) or []

safe_title = html.escape(title)
safe_overview = html.escape(overview).replace("\n", "<br>")


# =========================================================
# Header
# =========================================================
st.markdown(
    """
    <div class="cine-nav">
        <div class="cine-logo">CineAI<span> · MOVIE DISCOVERY</span></div>
        <div class="cine-nav-pill">Movie Details</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Hero
# =========================================================
st.markdown(
    f"""
    <div class="detail-hero">
        <div class="detail-kicker">Now viewing</div>
        <div class="detail-title">{safe_title}</div>
        <div class="detail-subtitle">
            Explore the story, genres, India availability and trailer.
        </div>
        <div class="hero-rating">{html.escape(rating_text)}</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Main detail layout
# =========================================================
left_col, right_col = st.columns([0.85, 1.55], gap="large")


# Poster
with left_col:
    with st.container(border=True):
        if poster:
           st.markdown(
    """
    <div class="availability-box">
        <div class="availability-title">📺 Available in India</div>
    </div>
    """,
    unsafe_allow_html=True,
)
        else:
            st.caption("Poster not available")


# Details
with right_col:

    # Dedicated larger Movie Details box
    st.markdown(
        """
        <div class="details-title-box">
            <div class="title">Movie Details</div>
            <div class="bar"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Main information card
    with st.container(border=True):

        # Genres
        st.markdown(
            '<div class="section-heading">Genres</div>',
            unsafe_allow_html=True,
        )

        genre_html = "".join(
            f"<span class='genre-badge'>{html.escape(str(genre))}</span>"
            for genre in genres
        )

        st.markdown(
            genre_html or "<span class='genre-badge'>Genre not available</span>",
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:0.9rem;'></div>", unsafe_allow_html=True)

        # Story
        st.markdown(
            '<div class="section-heading">Story</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f"<div class='detail-overview'>{safe_overview}</div>",
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
       # India Availability heading ONLY
with st.container(border=True):
    st.markdown(
        '<div class="availability-title">📺 Available in India</div>',
        unsafe_allow_html=True,
    )

# Providers stay outside the heading box
if watch_providers:
    provider_html = "".join(
        f"<span class='provider-badge'>{html.escape(str(provider))}</span>"
        for provider in watch_providers
    )

    st.markdown(provider_html, unsafe_allow_html=True)

    st.markdown(
        """
        <div class="availability-note">
            Provider information is supplied by TMDB and may change over time.
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <div class="availability-note">
            No India-region provider information was returned for this title.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Favorites + Back buttons
    favorites = load_favorites()

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    if title in favorites:
        st.markdown(
            '<div class="already-saved">⭐ This movie is already in your Favorites.</div>',
            unsafe_allow_html=True,
        )
    else:
        if st.button(
            "⭐ Add to Favorites",
            key="add_favorite",
            use_container_width=True,
        ):
            if title not in favorites:
                favorites.append(title)
                save_favorites(favorites)
                st.rerun()

    if st.button(
        "← Back to Recommendations",
        key="back_recommendations",
        use_container_width=True,
    ):
        st.switch_page("app.py")


# =========================================================
# Watch Preview / Trailer
# =========================================================
with st.container(border=True):

    st.markdown(
        '<div class="section-heading">Watch Preview</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="trailer-heading">🎬 Trailer</div>',
        unsafe_allow_html=True,
    )

    if trailer_key:
        st.iframe(
            f"https://www.youtube.com/embed/{trailer_key}",
            height=540,
        )
    else:
        st.markdown(
            '<div class="trailer-note">🎬 Trailer is not available for this movie.</div>',
            unsafe_allow_html=True,
        )


st.markdown(
    '<div class="footer-note">CineAI · Movie Recommendation System · Powered by TMDB</div>',
    unsafe_allow_html=True,
)
