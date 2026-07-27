import os
import tempfile
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ml_engine.scoring import calculate_relevance
from ml_engine.text_similarity import calculate_text_similarity

router = APIRouter(prefix="/relevance", tags=["Relevance"])


class RelevanceRequest(BaseModel):
    heading: str
    sub_heading: str
    image_url: Optional[str] = None


class RelevanceResponse(BaseModel):
    text_similarity: float
    relevance_score: float
    match_level: str
    image_used: bool


def classify_match(score: float) -> str:
    if score >= 0.50:
        return "High"
    elif score >= 0.38:
        return "Medium"
    return "Low"


@router.post("/", response_model=RelevanceResponse)
def compute_relevance(req: RelevanceRequest):
    if not req.heading.strip() or not req.sub_heading.strip():
        raise HTTPException(
            status_code=400, detail="Heading and sub-heading cannot be empty"
        )

    text_sim = calculate_text_similarity(req.heading, req.sub_heading)
    relevance_score = text_sim
    image_used = False

    if req.image_url:
        try:
            resp = requests.get(req.image_url, timeout=10)
            if resp.status_code == 200:
                ext = os.path.splitext(req.image_url.split("?")[0])[1] or ".jpg"
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
                tmp.write(resp.content)
                tmp_path = tmp.name
                tmp.close()

                result = calculate_relevance(
                    req.heading, req.sub_heading, tmp_path, tmp_path
                )
                relevance_score = result["relevance_score"]
                text_sim = result["text_similarity"]
                image_used = True

                os.unlink(tmp_path)
        except Exception:
            pass

    match_level = classify_match(relevance_score)

    return RelevanceResponse(
        text_similarity=round(text_sim, 3),
        relevance_score=round(relevance_score, 3),
        match_level=match_level,
        image_used=image_used,
    )
