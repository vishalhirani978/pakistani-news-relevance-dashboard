from fastapi import APIRouter
from backend.crud import get_stats

router = APIRouter(
    prefix="/statistics",
    tags=["Statistics"]
)

@router.get("/")
def statistics():
    return get_stats()