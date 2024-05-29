from kokomemo.dependencies.auth import LoginInfo, check_user
from kokomemo.api.v1.models import BaseResponse, Meta
from kokomemo.auth import get_new_id
from kokomemo.db import collection_depends
from kokomemo.models import Wall, Memo
from motor.motor_asyncio import AsyncIOMotorCollection as Collection
from pymongo import ReturnDocument, DESCENDING
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from pydantic.json_schema import SkipJsonSchema
from datetime import datetime, UTC
from typing import Annotated
from math import floor


router = APIRouter()


class WallNotFound(HTTPException):
    def __init__(self):
        super().__init__(status_code=404, detail="Wall not found.")


class WallsResponse(BaseResponse):
    data: list[Wall]


class WallResponse(BaseResponse):
    data: Wall


class MemosResponse(BaseResponse):
    data: list[Memo]


class MemoResponse(BaseResponse):
    data: Memo


class PostWall(Wall):
    id: SkipJsonSchema[str] = Field(default="", exclude=True)
    created_at: SkipJsonSchema[datetime] = Field(default=datetime.now(), exclude=True)
    modified_at: SkipJsonSchema[datetime] = Field(default=datetime.now(), exclude=True)


class EditWall(PostWall):
    id: str
    name: str | None = None
    colour: int | None = None


class PostMemo(Memo):
    id: SkipJsonSchema[str] = Field(default="", exclude=True)
    user_id: SkipJsonSchema[str] = Field(default="", exclude=True)
    wall_id: SkipJsonSchema[str] = Field(default="", exclude=True)
    index: SkipJsonSchema[float] = Field(default=0, exclude=True)
    created_at: SkipJsonSchema[datetime] = Field(default=datetime.now(), exclude=True)
    modified_at: SkipJsonSchema[datetime] = Field(default=datetime.now(), exclude=True)


def is_valid_wallid(
    wall_id,
    login: Annotated[LoginInfo, Depends(check_user)]
):
    if wall_id not in [wall.id for wall in login.user.walls]:
        raise WallNotFound()

    return wall_id


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
    data: PostWall
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


@router.delete("/{wall_id}")
async def delete_walls(
    wall_id: Annotated[str, Depends(is_valid_wallid)],
    login: Annotated[LoginInfo, Depends(check_user)],
    users: Annotated[Collection, Depends(collection_depends("users"))],
) -> BaseResponse:
    await users.update_one(
        {"id": login.user.id},
        {"$pull": {"walls": {"id": id}}}
    )

    return BaseResponse(
        meta=Meta(message="The wall has been removed.")
    )


@router.get("/walls/{wall_id}/memos")
async def get_memos(
    wall_id: Annotated[str, Depends(is_valid_wallid)],
    login: Annotated[LoginInfo, Depends(check_user)],
    memos: Annotated[Collection, Depends(collection_depends("memos"))],
    after: int | None = None,
    limit: int = 20
) -> MemosResponse:
    condition = {"wall_id": wall_id, "user_id": login.user.id}
    if after is not None:
        condition.update({"index": {"$lt": after}})
    memos = [memo async for memo in memos.find(condition)
                                         .sort("index", DESCENDING)
                                         .limit(limit)]

    return MemosResponse(
        data=memos,
        meta=Meta(message="Memos successfully fetched")
    )


@router.post("/walls/{wall_id}/memos")
async def post_memos(
    wall_id: Annotated[str, Depends(is_valid_wallid)],
    login: Annotated[LoginInfo, Depends(check_user)],
    memos: Annotated[Collection, Depends(collection_depends("memos"))],
    data: PostMemo
) -> MemoResponse:
    memo_ids = [memo['id'] async for memo in memos.find({})]
    new_id = get_new_id(memo_ids, 12)

    recent_entry = [Memo(**x) async for x in memos.find({
        "wall_id": wall_id,
        "user_id": login.user.id
    }).sort('index', DESCENDING).limit(1)]
    if recent_entry:
        index = floor(recent_entry[0].index) + 1.0
    else:
        index = 1.0

    new_memo = Memo(
        **data.model_dump(),
        id=new_id, user_id=login.user.id, wall_id=wall_id,
        index=index
    )

    await memos.insert_one(new_memo.model_dump())

    return MemoResponse(
        data=new_memo,
        meta=Meta(message="Memo successfully created.")
    )
