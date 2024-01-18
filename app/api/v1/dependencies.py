from app import config, db

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from pymongo.collection import Collection as MongoCollection

import jwt
from jwt.exceptions import PyJWTError
from typing import Annotated
from functools import cache
from asyncio import get_running_loop

security = HTTPBearer()


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
