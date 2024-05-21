from .user import router as user
from fastapi import APIRouter

router = APIRouter()

router.include_router(
    user,
    prefix="/user",
    tags=["user"]
)
