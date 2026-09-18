import json
import streamlit as st

st.set_page_config(
    page_title="Movie Details",
    page_icon="🎬",
    layout="wide"
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


st.markdown(
    """
    <style>
    .stApp {
        background-color: #111827;
    }

    h1, h2, h3, p, label {
        color: white !important;
    }

    .genre-badge {
        display: inline-block;
        background-color: #374151;
        color: #e5e7eb;
        padding: 5px 10px;
        margin: 3px;
        border-radius: 14px;
        font-size: 12px;
    }

    .detail-overview {
        color: #cbd5e1;
        font-size: 15px;
        line-height: 1.7;
    }

    .provider-badge {
        display: inline-block;
        background-color: #374151;
        color: #f9fafb;
        padding: 7px 12px;
        margin: 4px 4px 4px 0;
        border-radius: 16px;
        font-size: 13px;
        font-weight: 600;
    }

    .stButton > button {
        width: 100%;
        border-radius: 10px;
        font-size: 16px;
        font-weight: 700;
        color: #111827 !important;
        background-color: #ffffff !important;
        border: 1px solid #d1d5db !important;
    }

    .stButton > button p {
        color: #111827 !important;
    }

    .stButton > button:hover {
        color: #ffffff !important;
        background-color: #374151 !important;
        border-color: #4b5563 !important;
    }

    .stButton > button:hover p {
        color: #ffffff !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

if "selected_movie" not in st.session_state or not st.session_state.selected_movie:
    st.warning("Please select a movie from the recommendation page first.")

    if st.button("← Back to Recommendations"):
        st.switch_page("app.py")

    st.stop()

movie = st.session_state.selected_movie

title = movie.get("title", "Movie")
poster = movie.get("poster")
rating_text = movie.get("rating_text", "⭐ N/A")
genres = movie.get("genres", [])
overview = movie.get("overview", "No overview available.")
trailer_key = movie.get("trailer_key")
watch_providers = movie.get("watch_providers", [])

st.title(f"🎬 {title}")
st.markdown(f"### {rating_text}")

col1, col2 = st.columns([1, 2])

with col1:
    if poster:
        st.image(poster, width=300)
    else:
        st.caption("Poster not available")

with col2:
    st.subheader("Genres")

    genre_html = "".join(
        f"<span class='genre-badge'>{genre}</span>"
        for genre in genres
    )

    st.markdown(
        genre_html,
        unsafe_allow_html=True
    )

    st.subheader("Overview")

    st.markdown(
        f"<div class='detail-overview'>{overview}</div>",
        unsafe_allow_html=True
    )

    st.subheader("📺 Available on")

    if watch_providers:
        provider_html = "".join(
            f"<span class='provider-badge'>{provider}</span>"
            for provider in watch_providers
        )

        st.markdown(
            provider_html,
            unsafe_allow_html=True
        )
    else:
        st.info(
            "Streaming availability is not currently available for India."
        )

    favorites = load_favorites()

    if title in favorites:
        st.info("⭐ This movie is already in your Favorites.")
    else:
        if st.button(
            "⭐ Add to Favorites",
            key="add_favorite",
            use_container_width=True
        ):
            if title not in favorites:
                favorites.append(title)
                save_favorites(favorites)
                st.success("Added to favorites!")
                st.rerun()

st.divider()

st.subheader("🎬 Trailer")

if trailer_key:
    trailer_embed_url = (
        f"https://www.youtube.com/embed/{trailer_key}"
    )

    st.iframe(
        trailer_embed_url,
        height=500
    )
else:
    st.info("🎬 Trailer is not available for this movie.")

if st.button(
    "← Back to Recommendations",
    key="back_recommendations",
    use_container_width=True
):
    st.switch_page("app.py")
