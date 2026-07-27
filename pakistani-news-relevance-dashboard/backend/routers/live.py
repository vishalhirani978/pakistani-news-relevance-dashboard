from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/live")
def live():

    return {"status": "running"}
