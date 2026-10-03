# 🎬 AI Movie Recommendation System

A category-guided movie discovery web application built with **Python, Streamlit, Pandas, scikit-learn, Requests, and the TMDB API**.

The application uses a **locally trained CineAI recommendation model** to generate movie recommendations. TMDB is used only to enrich the recommended movies with live presentation and media information such as posters, ratings, trailers, and India-region watch-provider data.

---

## 👥 Team Members

- **Maninder Singh**
- **Jashanjit Singh**
- **Prabhnoor Singh**
- **Akshit Bansal**

---

## 🌐 Live Application

The project is deployed on **Streamlit Community Cloud**.

**Live App:** https://singhsabb7143-create-ai-movie-recommendation-syst-appapp-egfyb0.streamlit.app

**GitHub Repository:** https://github.com/singhsabb7143-create/AI-Movie-Recommendation-System

---

## 📌 Project Overview

Movie platforms contain large catalogues, which can make it difficult to decide what to watch.

This project provides a simple category-based discovery flow while using a local machine-learning recommendation engine for the core ranking.

```text
Select Movie Category
        ↓
CineAI Recommendation Model
        ↓
Semantic Similarity + Quality + Specificity Scoring
        ↓
5 Movie Recommendations
        ↓
TMDB Enrichment
        ↓
Poster + Rating + Movie Details
        ↓
Trailer + India Availability + Favorites
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

The selected category is passed to the local CineAI recommendation model, which ranks candidate movies and returns five recommendations while avoiding previously recommended movies when history is available.

### 🧠 CineAI Recommendation Model

The core recommendation engine is a **locally trained machine-learning model** stored in:

```text
models/cineai_model.joblib
```

The model uses:

- Movie overview/text content
- Genres and related text features
- **TF-IDF vectorization**
- **TruncatedSVD** dimensionality reduction
- **Cosine similarity / semantic retrieval**
- Quality and specificity signals for final ranking
- Diversity-aware selection for recommendations

The current model version is **CineAI V2**.

### 🖼️ Movie Posters

Posters are retrieved from the TMDB API and displayed on recommendation cards and the Movie Details page.

### ⭐ Movie Ratings

TMDB ratings are fetched and displayed with recommendations and on the Movie Details page.

### 📄 Movie Details Page

Clicking a movie opens the dedicated page:

```text
app/pages/movie_details.py
```

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

Trailer/video information is fetched from TMDB. The application prefers a suitable YouTube trailer and falls back to another suitable YouTube video when available.

### 📺 India Availability

The application reads TMDB watch-provider information for the **India (`IN`) region** and displays provider names returned by the API.

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

### 🔁 Recommendation History

Recommendation history is persisted using:

```text
recommendation_history.json
```

This helps prevent the same movies from being repeatedly shown after application refreshes or restarts, subject to the available candidate pool.

---

## 🧠 Recommendation Methodology

The visible recommendation flow is **genre-guided**, but the actual ranking is performed by the locally trained CineAI model rather than by a simple API recommendation endpoint.

### Model Pipeline

```text
Movie Text / Metadata
        ↓
TF-IDF Representation
        ↓
TruncatedSVD
        ↓
256-D Latent Representation
        ↓
Cosine Similarity / Semantic Retrieval
        ↓
Quality + Specificity Signals
        ↓
Final Ranking
        ↓
Diversity-aware Selection
        ↓
Top 5 Recommendations
```

### Current Model Configuration

| Parameter | Value |
|---|---:|
| Movies indexed | 4,803 |
| TF-IDF features | 35,000 |
| SVD latent dimensions | 256 |
| Model version | 2 |
| Semantic weight | 75% |
| Quality weight | 20% |
| Specificity weight | 5% |

The trained model and metadata are stored in:

```text
models/cineai_model.joblib
models/cineai_model.json
```

### Important Role of TMDB

TMDB is **not the core recommendation engine**.

TMDB is used after recommendation generation to fetch supplementary information such as:

- Posters
- Ratings
- Overview/details
- Trailers/videos
- India-region watch providers

This means the recommendation logic remains based on the project's own trained CineAI model, while TMDB provides live movie information and media enrichment.

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| **Python** | Core application, model, and data-processing language |
| **Streamlit** | Interactive web application and multipage UI |
| **Pandas** | Loading, filtering, and transforming movie data |
| **scikit-learn** | TF-IDF, TruncatedSVD, cosine similarity, and ML utilities |
| **Requests** | HTTP communication with TMDB |
| **Joblib** | Saving and loading the trained recommendation model |
| **TMDB API** | Posters, ratings, movie details, videos, and watch-provider data |
| **Git / GitHub** | Version control and source repository |
| **Streamlit Community Cloud** | Cloud deployment |

---

## 📂 Project Structure

```text
Movie-Recommendation-System/
│
├── app/
│   ├── app.py
│   ├── cineai_model.py
│   ├── train_cineai_model.py
│   └── pages/
│       └── movie_details.py
│
├── data/
│   ├── movies.csv
│   └── credits.csv
│
├── models/
│   ├── cineai_model.joblib
│   └── cineai_model.json
│
├── app/pages/
│   └── movie_details.py
│
├── evaluate_cineai_model.py
├── compare_v1_v2.py
├── favorites.json
├── recommendation_history.json
├── requirements.txt
├── README.md
└── .gitignore
```

### Important Files

| File | Purpose |
|---|---|
| `app/app.py` | Main Streamlit application |
| `app/cineai_model.py` | CineAI recommendation model implementation |
| `app/train_cineai_model.py` | Training script for the local recommendation model |
| `app/pages/movie_details.py` | Dedicated movie details page |
| `models/cineai_model.joblib` | Trained recommendation model |
| `models/cineai_model.json` | Model metadata/configuration |
| `data/movies.csv` | Movie metadata used by the project |
| `data/credits.csv` | Cast/credits data |
| `evaluate_cineai_model.py` | Model response/evaluation checks |
| `compare_v1_v2.py` | Comparison of recommendation scoring configurations |
| `favorites.json` | Persistent favorites |
| `recommendation_history.json` | Persistent recommendation history |
| `requirements.txt` | Python dependencies |

---

## ⚙️ How to Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/singhsabb7143-create/AI-Movie-Recommendation-System.git
cd AI-Movie-Recommendation-System
```

### 2. Create and activate a virtual environment

**macOS / Linux:**

```bash
python -m venv venv
source venv/bin/activate
```

**Windows:**

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

The application will open at the local Streamlit URL, normally:

```text
http://localhost:8501
```

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

TMDB is used to enrich the locally generated recommendations with live movie information.

### Poster

Movie poster data is retrieved from TMDB movie information.

### Rating

The TMDB `vote_average` value is used for the displayed movie rating.

### Overview

Movie summaries/details are retrieved from TMDB.

### Trailer

Movie video information is retrieved from the TMDB movie videos endpoint. The application selects a suitable YouTube video when available.

### Availability

Movie watch-provider information is retrieved for the India region:

```text
IN
```

Provider names are collected from the provider categories returned by TMDB.

---

## ⚡ Reliability and Performance Handling

The application uses a reusable Requests session with retry handling and timeouts.

Implemented measures include:

- HTTP session reuse
- Retry handling for transient HTTP failures
- Request timeouts
- Streamlit caching for repeated API calls
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
Save favorite data
    ↓
Write favorites.json
    ↓
Favorite remains available after restart
```

Removal follows the reverse process.

> For a multi-user production system, a database would be more appropriate than a local JSON file.

---

## 🔁 Recommendation History and Persistence

Recommendation history is maintained in both the current Streamlit session and a local JSON file:

```text
recommendation_history.json
```

The history is used to exclude previously recommended movie IDs where possible, reducing repetitive recommendation batches across refreshes and restarts.

If the candidate pool becomes too small, the application can reuse a recent subset so that recommendations remain available.

---

## 🧪 Testing and Evaluation

The application was tested during development for the main user flow, including recommendations, details, TMDB enrichment, and persistence.

The CineAI model was also checked in a fresh Python process after training.

### Model Evaluation Snapshot

```text
Movies indexed : 4,803
TF-IDF features: 35,000
Model load time: 0.2147 sec
Genres tested  : 11
Successful     : 11/11
Movies returned: 55
Average response: 0.0178 sec
Fastest response: 0.0046 sec
Slowest response: 0.0414 sec
```

There is currently **no labelled ground-truth recommendation dataset**, so formal accuracy, precision, recall, or F1 metrics are not reported for the recommendation task.

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

### Repository

https://github.com/singhsabb7143-create/AI-Movie-Recommendation-System

### Live Application

https://singhsabb7143-create-ai-movie-recommendation-syst-appapp-egfyb0.streamlit.app

---

## ⚠️ Limitations

- Recommendation quality depends on the available movie metadata and trained representation.
- TMDB trailer availability depends on the videos returned by the API.
- Watch-provider availability is region-specific and can change over time.
- The application does not currently implement user-profile personalization.
- Collaborative filtering is not implemented.
- Favorites and recommendation history use local JSON persistence rather than a production database.
- The category list is currently defined in the application UI.
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
- Machine-learning based movie recommendation
- TF-IDF text representation
- TruncatedSVD dimensionality reduction
- Cosine-similarity retrieval
- Movie metadata handling
- External API integration
- Streamlit UI development
- Multipage navigation
- Persistent storage
- Network reliability handling
- Git-based version control
- Cloud deployment

The architecture is intentionally simple enough for academic demonstration while retaining an extensible foundation for future recommendation improvements.
