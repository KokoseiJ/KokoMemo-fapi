from app import config, db

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from pymongo.collection import Collection as MongoCollection
from pydantic import BaseModel

import jwt
import secrets
from jwt.exceptions import PyJWTError
from typing import Annotated
from functools import cache
from asyncio import get_running_loop

security = HTTPBearer()


class ErrorMessage(BaseModel):
    message: str


async def get_new_id(collection: MongoCollection) -> str:
    loop = get_running_loop()
    while True:
        id_ = secrets.token_urlsafe(9)
        data = await loop.run_in_executor(
            None, lambda: collection.find_one({"id": id_})
        )
        if data is None:
            break

    return id_


def token_validation(token: str, secret: str, algo: list[str]) -> str:
    try:
        body = jwt.decode(token, secret, algorithms=algo)
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Failed to decode JWT.")

    return body["sub"]


@cache
def get_settings() -> config.Settings:
    return config.Settings()


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
