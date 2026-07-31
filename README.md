# Pakistani News Relevance Dashboard

An AI-powered news relevance analysis system that compares news articles from **Dawn (English)** and **Daily Ummat (Urdu)** to identify articles covering the same real-world events using multimodal similarity.

This project was developed as a **Data Science Semester Project**.

---

## Project Overview

The system performs the following tasks:

- Scrapes news articles from Dawn and Daily Ummat
- Downloads and stores article images locally
- Stores articles in an SQLite database
- Preprocesses article text
- Computes semantic similarity using Sentence Transformers
- Computes image similarity using dhash + HSV histogram correlation
- Combines text and image similarity into a weighted relevance score
- Matches related articles from both newspapers
- Exposes data through a FastAPI REST API
- Provides a frontend dashboard (under development)

---

## Features

### Data Collection

- Dawn News Scraper
- Daily Ummat Scraper
- Automatic image downloading
- SQLite storage

### NLP Processing

- Text preprocessing
- Stopword removal
- Sentence embeddings
- Cosine similarity

### Image Processing

- Difference Hash (dhash) structural similarity
- HSV histogram color similarity
- Combined 50/50 structural + color scoring

### Multimodal Matching

Weighted scoring:

```
Relevance Score =
0.65 × Text Similarity
+
0.35 × Image Similarity
```

Match Levels:

| Score | Level |
|--------|-------|
| ≥ 0.50 | High |
| ≥ 0.38 | Medium |
| < 0.38 | Low |

---

## Tech Stack

### Backend

- Python
- FastAPI
- SQLite

### Machine Learning

- Sentence Transformers
- all-MiniLM-L6-v2
- dhash (Difference Hash)
- OpenCV HSV Histogram

### Frontend

- HTML/CSS/JavaScript

---

## Project Structure

```
pakistani-news-relevance-dashboard/

backend/
│
├── crud.py
├── database.py
├── main.py
└── routers/

data/
│
├── raw/
│   ├── images/
│   └── processed/
│       └── database/
│           └── news.db

ml_engine/
│
├── preprocessing.py
├── text_similarity.py
├── image_similarity.py
├── scoring.py
└── matcher.py

scraper/
│
├── dawn_scraper.py
└── ummat_scraper.py

tests/
```

---

## API Endpoints

| Method | Endpoint | Description |
|----------|----------|-------------|
| GET | `/` | API Status |
| GET | `/articles` | Retrieve all articles |
| GET | `/matches` | Retrieve matched article pairs |
| GET | `/statistics` | Dashboard statistics |
| GET | `/live` | Live API status |

---

## Current Project Status

### Backend

- ✅ Database
- ✅ CRUD Operations
- ✅ FastAPI REST API
- ✅ Static Image Serving
- ✅ CORS Configuration

### Data Pipeline

- ✅ Dawn Scraper
- ✅ Daily Ummat Scraper
- ✅ Image Downloader

### Machine Learning

- ✅ Text Preprocessing
- ✅ Sentence Embeddings
- ✅ Image Embeddings
- ✅ Multimodal Similarity
- ✅ Article Matcher

### Frontend

- ✅ Dashboard
- ✅ Interactive UI

---

## Running the Project

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Start the Backend

```bash
uvicorn backend.main:app --reload
```

Open:

```
http://127.0.0.1:8000/docs
```

to access the interactive API documentation.

---

## Team

| Role | Responsibility |
|------|----------------|
| Data Engineer | Data collection, database, backend integration |
| ML/NLP Engineer | NLP pipeline, multimodal similarity, matching engine |
| Frontend Engineer | React dashboard and visualization |

---

## License

This project was developed for academic purposes as part of a university semester project.
