# 🎬 AI Movie Recommendation System

A content-based movie recommendation web application built with Python and Streamlit.

## 🚀 Features

- Select a movie from the dropdown
- Get 5 similar movie recommendations
- Movie posters from TMDB
- TMDB ratings
- Genre badges
- Movie overview
- Add movies to Favorites
- Remove movies from Favorites
- Favorites remain saved after restarting the application
- Dark themed user interface

## 🧠 Recommendation Method

The system uses content-based filtering.

Movie information such as:

- Overview
- Genres
- Keywords
- Top cast members

is combined into a single `tags` field.

The tags are converted into numerical vectors using `CountVectorizer`.

Cosine similarity is then used to find movies that are most similar to the selected movie.

## 🛠️ Technologies Used

- Python
- Pandas
- Scikit-learn
- Streamlit
- Requests
- TMDB API

## 📁 Project Structure

```text
Movie-Recommendation-System/
├── .streamlit/
│   └── secrets.toml
├── app/
│   ├── app.py
│   └── app_backup.py
├── data/
│   ├── movies.csv
│   └── credits.csv
├── favorites.json
├── movies.pkl
├── similarity.pkl
├── requirements.txt
└── README.md