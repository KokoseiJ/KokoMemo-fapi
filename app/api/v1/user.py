from app import db
from .dependencies import get_user
from .login import router as login_router

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from pymongo.collection import Collection as MongoCollection

from typing import Annotated

router = APIRouter()
router.include_router(
    login_router,
    prefix="/login"
)


class User(BaseModel):
    email: str
    name: str
    used_bytes: int


class EditableUser(BaseModel):
    name: str | None = Field(
        default=None, title="New nickname for the user", max_length=30
    )


class ErrorMessage(BaseModel):
    message: str


@router.get("/info", responses={401: {"model": ErrorMessage}})
async def get_info(user: Annotated[dict, Depends(get_user)]) -> User:
    return User(
        email=user["email"],
        name=user["name"],
        used_bytes=user["used_bytes"]
    )


@router.put("/info", status_code=204, responses={401: {"model": ErrorMessage}})
async def edit_info(
    new_user: EditableUser,
    user: Annotated[dict, Depends(get_user)],
    users: Annotated[MongoCollection, Depends(db.get_users)]
) -> None:
    update = {}
    if new_user.name is not None:
        update.update({"name": new_user.name})

    if update is not None:
        users.update_one({"_id": user["_id"]}, {"$set": update})

    return
