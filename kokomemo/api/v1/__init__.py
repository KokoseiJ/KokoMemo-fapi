from .user import router as user
from .memo import router as memo
from fastapi import APIRouter

router = APIRouter()

router.include_router(
    user,
    prefix="/user",
    tags=["user"]
)

router.include_router(
    memo,
    prefix="/walls",
    tags=["memo"]
)
