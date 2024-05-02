from .v1 import router as v1

from fastapi import APIRouter

router = APIRouter()

router.include_router(
    v1,
    prefix="/v1",
    tags=["v1"]
)
