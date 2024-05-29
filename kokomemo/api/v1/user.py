from .login import router as login
from kokomemo.db import collection_depends
from kokomemo.dependencies.auth import check_user, LoginInfo
from kokomemo.models import User, Session, Wall, Integration
from .models import BaseResponse, Meta
from kokomemo.logger import logger
from motor.motor_asyncio import AsyncIOMotorCollection as Collection
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from pydantic.json_schema import SkipJsonSchema
from typing import Annotated

router = APIRouter()

router.include_router(
    login,
    prefix="/login",
    tags=["login"]
)


class PartialIntegration(Integration):
    data: SkipJsonSchema[dict] = Field(default=[], exclude=True)


class UserInfo(User):
    sessions: SkipJsonSchema[list[Session]] = Field(default=[], exclude=True)
    walls: SkipJsonSchema[list[Wall]] = Field(default=[], exclude=True)
    integrations: list[PartialIntegration]


class UserInfoResponse(BaseResponse):
    data: UserInfo


class UserInfoRequest(BaseModel):
    name: str


@router.get("/info")
def get_userinfo(
    user: Annotated[LoginInfo, Depends(check_user)]
) -> UserInfoResponse:
    user_info = UserInfo(**user.user.model_dump())

    return UserInfoResponse(
        meta=Meta(message="User successfully queried"),
        data=user_info
    )


@router.put("/info")
async def put_userinfo(
    user: Annotated[LoginInfo, Depends(check_user)],
    users: Annotated[Collection, Depends(collection_depends("users"))],
    user_info: UserInfoRequest
) -> UserInfoResponse:
    await users.update_one(
        {"id": user.user.id}, {"$set": {"name": user_info.name}}
    )
    user.user.name = user_info.name

    return UserInfoResponse(
        meta=Meta(message="Info successfully updated."),
        data=UserInfo(**user.user.model_dump())
    )
