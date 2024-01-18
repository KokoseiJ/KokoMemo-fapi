from app import config

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from pymongo import MongoClient
from pymongo.database import Database as MongoDatabase
from pymongo.collection import Collection as MongoCollection

import jwt

from functools import cache
from typing import Annotated
from asyncio import get_running_loop
from jwt.exceptions import PyJWTError


router = APIRouter()


class MongoManager:
    def __init__(self, url: str, name: str):
        self.url = url
        self.name = name
        self.mongo = None
        self.db = None
        self.users = None
        self.memos = None

    async def connect(self) -> MongoClient:
        self.mongo = await get_running_loop().run_in_executor(
            None, lambda: MongoClient(self.url)
        )

        return self.mongo

    async def get_db(self) -> MongoDatabase:
        if self.mongo is None:
            await self.connect()

        self.db = await get_running_loop().run_in_executor(
            None, lambda: self.mongo[self.name]
        )

        return self.db

    async def get_collection(self, name) -> MongoCollection:
        if self.db is None:
            await self.get_db()

        return await get_running_loop().run_in_executor(
            None, lambda: self.db[name]
        )

    async def get_users(self) -> MongoCollection:
        if self.users is None:
            self.users = await self.get_collection("users")

        return self.users

    async def get_memos(self) -> MongoCollection:
        if self.memos is None:
            self.memos = await self.get_collection("memos")
        return self.memos


@cache
def get_settings() -> config.Settings:
    return config.Settings()


db = MongoManager(get_settings().mongo_url, get_settings().db_name)


def token_validation(token: str, secret: str, algo: list[str]) -> str:
    try:
        body = jwt.decode(token, secret, algorithms=algo)
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Failed to decode JWT.")

    return body["sub"]


security = HTTPBearer()


async def get_user(
    authorization: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    settings: Annotated[config.Settings, Depends(get_settings)],
    users: Annotated[MongoCollection, Depends(db.get_users)],
) -> dict:
    token = authorization.credentials
    user_id = token_validation(token, settings.secret_key, [settings.jwt_algo])

    loop = get_running_loop()

    user = await loop.run_in_executor(
        None, lambda: users.find_one({"id": user_id})
    )

    if user is None:
        raise HTTPException(status_code=401, detail="No user found!")

    return user


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
