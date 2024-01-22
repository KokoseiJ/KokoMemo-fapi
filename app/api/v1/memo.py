from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from pydantic import BaseModel

from pymongo.collection import Collection as MongoCollection

import secrets
from .dependencies import get_user, get_new_id
from asyncio import get_running_loop
from app import db

router = APIRouter()


class Wall(BaseModel):
    id: str
    name: str
    colour: int


class NewWall(BaseModel):
    name: str
    colour: int


class EditWall(BaseModel):
    id: str
    name: str | None
    colour: int | None


class Memo(BaseModel):
    id: str
    owner: str
    wall: str
    created_at: int
    edited_at: int
    content: str


class NewMemo(BaseModel):
    content: str


class EditMemo(BaseModel):
    id: str
    wall: str | None
    content: str | None


@router.get("/walls")
def get_walls(user: Annotated[dict, Depends(get_user)]) -> list[Wall]:
    return user['walls']


@router.post("/walls")
def create_wall(
    user: Annotated[dict, Depends(get_user)],
    users: Annotated[MongoCollection, Depends(db.get_users)],
    wall: NewWall
) -> Wall:

    wall_ids = [wall['id'] for wall in user['walls']]

    while True:
        id_ = secrets.token_urlsafe(9)
        if id_ not in wall_ids:
            break

    new_wall = {
        "id": id_,
        "name": wall.name,
        "colour": wall.colour
    }

    await get_running_loop().run_in_executor(
        None, lambda: users.update_one(
            {"_id": user['_id']},
            {"$addToSet", {"walls": new_wall}}
        )
    )

    return new_wall


@router.put("/walls")
def edit_wall(
    user: Annotated[dict, Depends(get_user)],
    users: Annotated[MongoCollection, Depends(db.get_users)],
    wall: EditWall
):
    if wall.id not in [wall['id'] for wall in user['walls']]:
        raise HTTPException(
            status_code=404,
            details="Wall not found."
        )

    if wall.name is None and wall.colour is None:
        raise HTTPException(
            status_code=400,
            details="Either name or colour should be provided."
        )

    updates = dict()
    if wall.name is not None:
        updates.update({"walls.$[wall].name": wall.name})
    if wall.colour is not None:
        updates.update({"walls.$[wall].colour": wall.colour})

    await get_running_loop().run_in_executor(
        None, lambda: users.update_one(
            {"_id": user['_id']},
            {"$set": updates},
            array_filters=[{"wall.id": wall.id}]
        )
    )


@router.delete("/walls/{wall_id}")
def delete_wall(
    user: Annotated[dict, Depends(get_user)],
    users: Annotated[MongoCollection, Depends(db.get_users)],
    memos: Annotated[MongoCollection, Depends(db.get_memos)],
    wall_id: str
):
    loop = get_running_loop()

    if wall_id not in [wall['id'] for wall in user['walls']]:
        raise HTTPException(
            status_code=404,
            details="Wall not found."
        )
    loop.run_in_executor(
        None, lambda: users.update_one(
            {"_id": user['_id']},
            {"$pull": {"walls": {"id": wall_id}}}
        )
    )

    await loop.run_in_executor(
        None, lambda: memos.delete_many({"wall": wall_id})
    )


@router.get("/walls/{wall_id}/memos")
def get_memos(
    user: Annotated[dict, Depends(db.get_users)],
    users: Annotated[MongoCollection, Depends(db.get_users)],
    memos: Annotated[MongoCollection, Depends(db.get_memos)],
    wall_id: str,
    before: int | None,
    limit: int = 20
) -> list[Memo]:
    loop = get_running_loop()

    if wall_id not in [wall['id'] for wall in user['walls']]:
        raise HTTPException(
            status_code=404,
            details="Wall not found."
        )

    query = {
        "owner": user['id'],
        "wall": wall_id
    }

    if before is not None:
        query.update({"created_at": {"$lte": before}})

    cursor = await loop.run_in_executor(None, lambda: memos.find(query))
    cursor.sort("created_at").limit(20)

    return await loop.run_in_executor(None, lambda: list(cursor))


@router.get("/walls/{wall_id}/memos/{memo_id}")
def get_memo(
    user: Annotated[dict, Depends(get_user)],
    wall_id: str,
    memo_id: str
) -> Memo:
    if wall_id not in [wall['id'] for wall in user['walls']]:
        raise HTTPException(
            status_code=404,
            details="Wall not found."
        )

    data = await get_running_loop().run_in_executor(
        None, lambda: memos.find_one({
                "id": memo_id,
                "owner": user['id'],
                "wall": wall_id
            })
    )

    if data is None:
        raise HTTPException(
            status_code=404,
            details="Memo not found."
        )

    return data


@router.post("/walls/{wall_id}/memos")
def create_memo(
    user: Annotated[dict, Depends(get_user)],
    memos: Annotated[MongoCollection, Depends(db.get_memos)],
    wall_id: str,
    memo: NewMemo
) -> Memo:
    


@router.put("/walls/{wall_id}/memos")
def edit_memo(
    user: Annotated[dict, Depends(get_user)],
    wall_id: str,
    memo: EditMemo
):
    pass


@router.delete("/walls/{wall_id}/memos/{memo_id}")
def delete_memo(
    user: Annotated[dict, Depends(get_user)],
    wall_id: str,
    user_id: str
):
    pass
