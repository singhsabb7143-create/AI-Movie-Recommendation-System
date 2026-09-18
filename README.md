# 🎬 AI Movie Recommendation System

A category-based movie discovery web application built with **Python, Streamlit, Pandas, scikit-learn, Requests, and the TMDB API**.

The final user-facing application lets a user choose a movie category and receive **5 matching movie recommendations**. Selecting a movie opens a dedicated details page with its poster, rating, genres, overview, trailer, India-region availability information, and persistent Favorites.

---

## 👥 Team Members

- **Maninder Singh**
- **Jashanjit Singh**
- **Prabhnoor Singh**
- **Akshit Bansal**

---

## 🌐 Live Application

The project is deployed on **Streamlit Community Cloud**.

> Add or update the live application URL here before final submission if required.

---

## 📌 Project Overview

Movie platforms contain large catalogues, which can make it difficult to decide what to watch.

This project focuses on a simple discovery flow:

```text
Select Movie Category
        ↓
Filter Matching Movies
        ↓
Show 5 Recommendations
        ↓
Poster + Movie Name + Rating
        ↓
Open Movie Details
        ↓
Genres + Overview + Trailer
        ↓
India Availability + Favorites
```

The main recommendation screen is intentionally concise. Detailed information is shown only after a movie is selected.

---

## ✨ Features

### 🎭 Category-Based Recommendations

The user can select one of the supported categories:

- Action
- Adventure
- Animation
- Comedy
- Crime
- Drama
- Fantasy
- Horror
- Mystery
- Romance
- Thriller

The application filters the local movie dataset by the selected genre and displays five matching movies.

### 🖼️ Movie Posters

Posters are retrieved from the TMDB API and displayed on the recommendation cards and movie details page.

### ⭐ Movie Ratings

TMDB ratings are fetched and displayed with each recommendation and on the movie details page.

### 📄 Movie Details Page

Clicking a movie title opens:

`app/pages/movie_details.py`

The details page provides:

- Movie title
- Rating
- Large poster
- Genres
- Full overview
- Trailer
- India-region availability
- Add to Favorites
- Back to Recommendations

### 🎬 Trailer Playback

Trailer/video information is fetched from TMDB.

The application prefers a YouTube trailer and falls back to a suitable YouTube teaser/video when available. The selected video is embedded on the Movie Details page.

### 📺 India Availability

The application reads TMDB watch-provider information for the **India (`IN`) region** and displays the provider names returned by the API.

Availability is title- and region-specific and may change over time.

### ⭐ Favorites

Users can:

- Add movies to Favorites
- See whether a movie is already saved
- Remove saved movies
- Restore saved Favorites after restarting the local application

Favorites are persisted using:

```text
favorites.json
```

---

## 🧠 Recommendation Methodology

### Current User-Facing Recommendation Logic

The final visible recommendation flow is **category/genre based**.

For a selected category:

1. The application checks the movie's genre list.
2. Matching movies are collected.
3. The first five matching records are displayed.
4. TMDB is used to enrich those records with poster, rating, overview, trailer, and provider information.

The core filtering concept is:

```python
matching_movies = movies[
    movies["genres"].apply(
        lambda genre_list: selected_genre in genre_list
    )
]

recommended_movies = matching_movies.head(5)
```

### Retained Content-Similarity Pipeline

The codebase also retains a content-representation pipeline built with:

- Movie overview
- Genres
- Keywords
- Top cast
- CountVectorizer
- Cosine similarity

This pipeline is retained as a foundation for future hybrid or similarity-based recommendation modes.

**Important:** the current visible recommendation interface uses direct genre/category filtering rather than a learned relevance ranking.

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| **Python** | Core application and data-processing language |
| **Streamlit** | Interactive web application and multipage UI |
| **Pandas** | Loading, merging, filtering, and transforming movie data |
| **scikit-learn** | CountVectorizer and cosine-similarity components |
| **Requests** | HTTP communication with TMDB |
| **TMDB API** | Posters, ratings, overviews, videos, and watch-provider data |
| **Git / GitHub** | Version control and source repository |
| **Streamlit Community Cloud** | Cloud deployment |

---

## 📂 Project Structure

```text
Movie-Recommendation-System/
│
├── .streamlit/
│   └── secrets.toml
│
├── app/
│   ├── app.py
│   ├── app_backup.py
│   └── pages/
│       └── movie_details.py
│
├── data/
│   ├── movies.csv
│   └── credits.csv
│
├── favorites.json
├── movies.pkl
├── similarity.pkl
├── requirements.txt
├── README.md
└── .gitignore
```

### Important Files

| File | Purpose |
|---|---|
| `app/app.py` | Main Streamlit application |
| `app/pages/movie_details.py` | Dedicated movie details page |
| `data/movies.csv` | Movie metadata |
| `data/credits.csv` | Cast/credits data |
| `favorites.json` | Persistent favorites |
| `movies.pkl` | Generated movie data/model artifact |
| `similarity.pkl` | Generated similarity matrix |
| `.streamlit/secrets.toml` | Local Streamlit secrets |
| `requirements.txt` | Python dependencies |

---

## ⚙️ How to Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/singhsabb7143-create/AI-Movie-Recommendation-System.git
cd AI-Movie-Recommendation-System
```

### 2. Create and activate a virtual environment

macOS / Linux:

```bash
python -m venv venv
source venv/bin/activate
```

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the TMDB API key

Create:

```text
.streamlit/secrets.toml
```

and add:

```toml
TMDB_API_KEY = "YOUR_TMDB_API_KEY"
```

Do not commit the secrets file to GitHub.

### 5. Start the application

```bash
streamlit run app/app.py
```

The application will open in the browser at the local Streamlit URL.

---

## 🔐 Security

The TMDB API key is loaded through Streamlit secrets:

```python
TMDB_API_KEY = st.secrets["TMDB_API_KEY"]
```

The secret configuration is excluded from version control using `.gitignore`.

The repository should never contain the real API key.

---

## 🌐 TMDB API Integration

TMDB is used to enrich the local dataset with live presentation and media information.

### Poster

Movie poster data is retrieved through the TMDB movie search endpoint.

### Rating

The TMDB `vote_average` value is used for the displayed movie rating.

### Overview

Movie summaries are retrieved from TMDB search results.

### Trailer

Movie video information is retrieved from the TMDB movie videos endpoint. The application selects a suitable YouTube video when available.

### Availability

Movie watch-provider information is retrieved for the India region:

```text
IN
```

Provider names are collected from streaming, free, ad-supported, rental, and purchase categories returned by TMDB.

---

## ⚡ Reliability and Performance Handling

The application uses a reusable Requests session with retry handling and timeouts.

Implemented measures include:

- HTTP session reuse
- Retry handling for transient HTTP failures
- Request timeouts
- Streamlit caching for repeated TMDB calls
- Poster fallback handling
- Graceful handling when trailers or providers are unavailable

Example retry status codes include:

```text
429
500
502
503
504
```

---

## ❤️ Favorites and Persistence

Favorites use two layers:

### Session State

Streamlit session state keeps favorites available during the current application interaction.

### JSON Persistence

The favorites list is written to:

```text
favorites.json
```

Typical flow:

```text
Add Favorite
    ↓
Append Movie Title
    ↓
Save favorites.json
    ↓
Movie remains in Favorites
```

Removal follows the reverse process.

> For a multi-user production system, a database would be more appropriate than a local JSON file.

---

## 🧪 Testing

The application was tested manually during development.

| Test | Result |
|---|---|
| Python syntax check | ✅ Passed |
| Category selection | ✅ Passed |
| Five recommendations | ✅ Passed |
| Poster display | ✅ Passed |
| Rating display | ✅ Passed |
| Movie title navigation | ✅ Passed |
| Movie details page | ✅ Passed |
| Trailer playback | ✅ Passed when suitable video is available |
| India availability | ✅ Passed when provider data is returned |
| Add Favorites | ✅ Passed |
| Remove Favorites | ✅ Passed |
| Favorites persistence | ✅ Passed in the local environment |
| Streamlit deployment | ✅ Passed |

Python syntax was checked using:

```bash
python -m py_compile app/app.py app/pages/movie_details.py
```

No formal recommendation accuracy metric is reported because the current user-facing recommendation mode is a simple category filter and there is no labelled ground-truth set for accuracy evaluation.

---

## 🚀 Deployment

The project was deployed using:

```text
Local Project
     ↓
Git
     ↓
GitHub
     ↓
Streamlit Community Cloud
     ↓
Live Web Application
```

Repository:

```text
https://github.com/singhsabb7143-create/AI-Movie-Recommendation-System
```

The final version was pushed to the `main` branch and verified on Streamlit Community Cloud.

---

## ⚠️ Limitations

- The current category recommender selects the first five matching dataset records rather than ranking the whole category with a learned relevance score.
- Trailer availability depends on videos returned by TMDB.
- Watch-provider availability is region-specific and can change over time.
- The application does not currently implement user-profile personalization.
- Collaborative filtering is not implemented.
- Favorites use a local JSON file rather than a production database.
- The category list is manually defined in the UI.
- A direct full-movie deep link is not guaranteed for every provider/movie.

---

## 🔮 Future Scope

Possible future improvements include:

- Hybrid recommendations using genre + content similarity
- Personalized recommendations
- User feedback signals
- Collaborative filtering
- Dynamic genre loading
- Better movie search
- Filters by year, language, rating, and runtime
- Watchlist support
- Notification features
- Responsive mobile-first interface
- Database-backed user accounts
- Automated integration tests and structured logging
- More reliable watch-provider link handling

---

## 👨‍💻 Team

| Team Member |
|---|
| Maninder Singh |
| Jashanjit Singh |
| Prabhnoor Singh |
| Akshit Bansal |

---

## 📚 References

- [TMDB API Documentation](https://developer.themoviedb.org/)
- [TMDB Movie Videos API](https://developer.themoviedb.org/reference/movie-videos)
- [TMDB Movie Watch Providers API](https://developer.themoviedb.org/reference/movie-watch-providers)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud)
- [scikit-learn Documentation](https://scikit-learn.org/stable/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Git Documentation](https://git-scm.com/doc)

---

## 🎓 Academic Note

This project demonstrates practical integration of:

- Data preparation
- Genre-based recommendation logic
- Movie metadata handling
- External API integration
- Streamlit UI development
- Multipage navigation
- Persistent storage
- Network reliability handling
- Git-based version control
- Cloud deployment

The architecture is intentionally simple enough for academic demonstration while retaining an extensible foundation for future recommendation improvements.
