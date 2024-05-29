from kokomemo.dependencies.auth import LoginInfo, check_user
from kokomemo.api.v1.models import BaseResponse, Meta
from kokomemo.auth import get_new_id
from kokomemo.db import collection_depends
from kokomemo.models import Wall
from motor.motor_asyncio import AsyncIOMotorCollection as Collection
from pymongo import ReturnDocument
from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field
from pydantic.json_schema import SkipJsonSchema
from datetime import datetime, UTC
from typing import Annotated


router = APIRouter()


class WallNotFound(HTTPException):
    def __init__(self):
        super().__init__(status_code=404, detail="Wall not found.")


class WallsResponse(BaseResponse):
    data: list[Wall]


class WallResponse(BaseResponse):
    data: Wall


class PartialWall(Wall):
    id: SkipJsonSchema[str] = Field(default="", exclude=True)
    created_at: SkipJsonSchema[datetime] = Field(default=datetime.now(), exclude=True)
    modified_at: SkipJsonSchema[datetime] = Field(default=datetime.now(), exclude=True)


class EditWall(PartialWall):
    id: str
    name: str | None = None
    colour: int | None = None


@router.get("/")
def get_walls(
    login: Annotated[LoginInfo, Depends(check_user)]
) -> WallsResponse:
    walls = login.user.walls

    return WallsResponse(
        data=walls,
        meta=Meta(message="List of walls successfully fetched.")
    )


@router.post("/")
async def post_walls(
    login: Annotated[LoginInfo, Depends(check_user)],
    users: Annotated[Collection, Depends(collection_depends("users"))],
    data: PartialWall
) -> WallResponse:
    user = login.user
    walls_id = [wall.id for wall in user.walls]

    new_id = get_new_id(walls_id)

    new_wall = Wall(**data.model_dump(), id=new_id)

    await users.update_one(
        {"id": login.user.id},
        {"$push": {"walls": new_wall.model_dump()}}
    )

    return WallResponse(
        data=new_wall,
        meta=Meta(message="New wall has been successfully created.")
    )


@router.put("/")
async def edit_walls(
    login: Annotated[LoginInfo, Depends(check_user)],
    users: Annotated[Collection, Depends(collection_depends("users"))],
    data: EditWall
) -> WallResponse:

    if data.id not in [wall.id for wall in login.user.walls]:
        raise WallNotFound()

    payload = {"walls.$[wall].modified_at": datetime.now(UTC)}
    if data.name:
        payload.update({"walls.$[wall].name": data.name})
    if data.colour:
        payload.update({"walls.$[wall].colour": data.colour})

    new_user = await users.find_one_and_update(
        {"id": login.user.id},
        {"$set": payload},
        array_filters=[{"wall.id": data.id}],
        return_document=ReturnDocument.AFTER
    )

    wall = [wall for wall in new_user['walls'] if wall['id'] == data.id][0]

    return WallResponse(
        data=Wall(**wall),
        meta=Meta(message="Wall has been successfully edited.")
    )


@router.delete("/{id}")
async def delete_walls(
    id,
    login: Annotated[LoginInfo, Depends(check_user)],
    users: Annotated[Collection, Depends(collection_depends("users"))],
) -> BaseResponse:
    if id not in [wall.id for wall in login.user.walls]:
        raise WallNotFound()

    await users.update_one(
        {"id": login.user.id},
        {"$pull": {"walls": {"id": id}}}
    )

    return BaseResponse(
        meta=Meta(message="The wall has been removed.")
    )
