from fastapi import APIRouter
from backend.crud import get_all_matches
from backend.schemas import MatchResponse

router = APIRouter(
    prefix="/matches",
    tags=["Matches"]
)

@router.get("/", response_model=list[MatchResponse])
def read_matches():
    return get_all_matches()