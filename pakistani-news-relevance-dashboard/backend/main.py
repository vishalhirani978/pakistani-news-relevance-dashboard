from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend import database
from backend.routers.articles import router as articles_router
from backend.routers.statistics import router as statistics_router
from backend.routers.live import router as live_router
from backend.routers.matches import router as matches_router
from backend.routers.relevance import router as relevance_router

app = FastAPI(title="Pakistani News Relevance Dashboard", version="1.0")

# CORS: open for all origins in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Routers ---
app.include_router(articles_router)
app.include_router(statistics_router)
app.include_router(live_router)
app.include_router(matches_router)
app.include_router(relevance_router)

# --- Static image assets ---
app.mount("/images", StaticFiles(directory="data/raw/images"), name="images")


@app.get("/")
def root():
    return {"message": "Pakistani News Relevance Dashboard API"}
