from fastapi import APIRouter, Depends
from typing import Annotated
from pydantic import BaseModel

from .dependencies import get_user

router = APIRouter()


class Wall(BaseModel):
    id: str
    name: str
    colour: int


class NewWall(BaseModel):
    name: str
    colour: int


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
    wall: str
    content: str


@router.get("/walls")
def get_walls(user: Annotated[dict, Depends(get_user)]) -> list[Wall]:
    pass


@router.post("/walls")
def create_wall(user: Annotated[dict, Depends(get_user)], wall: NewWall) -> Wall:
    pass


@router.put("/walls")
def edit_wall(user: Annotated[dict, Depends(get_user)], wall: Wall):
    pass


@router.delete("/walls/{wall_id}")
def delete_wall(user: Annotated[dict, Depends(get_user)], wall_id: str):
    pass


@router.get("/walls/{wall_id}/memos")
def get_memos(
    user: Annotated[dict, Depends(get_user)],
    wall_id: str,
    before: int | None,
    limit: int = 20
) -> list[Memo]:
    pass


@router.get("/walls/{wall_id}/memos/{memo_id}")
def get_memo(
    user: Annotated[dict, Depends(get_user)],
    wall_id: str,
    user_id: str
) -> Memo:
    pass


@router.post("/walls/{wall_id}/memos")
def create_memo(
    user: Annotated[dict, Depends(get_user)],
    memo: NewMemo
) -> Memo:
    pass


@router.put("/walls/{wall_id}/memos")
def edit_memo(
    user: Annotated[dict, Depends(get_user)],
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
