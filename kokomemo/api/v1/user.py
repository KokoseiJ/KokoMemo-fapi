from kokomemo.dependencies.auth import check_user, LoginInfo
from kokomemo.models import User, Session, Wall, Integration
from .models import BaseResponse, Meta
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from pydantic.json_schema import SkipJsonScheme
from typing import Annotated

router = APIRouter()


class PartialIntegration(Integration):
    data: SkipJsonScheme[dict] = Field(default=[], exclude=True)


class UserInfo(User):
    sessions: SkipJsonScheme[list[Session]] = Field(default=[], exclude=True)
    walls: SkipJsonScheme[list[Wall]] = Field(default=[], exclude=True)
    integrations: list[PartialIntegration]


class UserInfoResponse(BaseResponse):
    data: UserInfo


class UserInfoRequest(BaseResponse):
    name: str


@router.get("/info")
def get_userinfo(
    user: Annotated[LoginInfo, Depends(check_user)]
) -> UserInfoResponse:
    user_info = UserInfo(**user.model_dump())

    return UserInfoResponse(
        meta=Meta(message="User successfully queried"),
        data=user_info
    )


@router.post("/info")
def get_userinfo(
    user: Annotated[LoginInfo, Depends(check_user)],
    users: Annotated[Collection, Depends(collection_depends("users"))],
    user_info: UserInfoRequest
):
    await users.update_one(
        {"id": user.user.id}, {"$set": {"name": user_info.name}}
    )
    user.name = user_info.name

    return UserInfoResponse(
        meta=Meta(message="Info successfully updated."),
        data=UserInfo(**user.model_dump())
    )
