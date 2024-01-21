from app import db, config
from .dependencies import get_settings

from fastapi import APIRouter, Body, HTTPException, Depends
from pydantic import BaseModel

from pymongo.collection import Collection as MongoCollection

from google.oauth2 import id_token
from google.auth.transport import requests

import jwt
import secrets
import datetime
from typing import Annotated
from asyncio import get_running_loop

router = APIRouter()


async def get_new_id(collection: MongoCollection) -> str:
    loop = get_running_loop()
    users = await db.get_users()
    while True:
        id_ = secrets.token_urlsafe(9)
        data = await loop.run_in_executor(
            None, lambda: users.find_one({"id": id_})
        )
        if data is not None:
            continue

    return id_


def get_token(user_id: str) -> str:
    now = datetime.datetime.now(tz=datetime.UTC)
    exp = now + datetime.timedelta(hour=24)

    body = {
        "sub": user_id,
        "iat": now,
        "exp": exp
    }

    settings = get_settings()

    return jwt.encode(body, settings.secret_key, algorithm=[settings.jwt_algo])


class LoginResponse(BaseModel):
    token: str


@router.post("/google")
async def google_login(
    token: Annotated[str, Body(embed=True)],
    settings: Annotated[config.Settings, Depends(get_settings)],
    users: Annotated[MongoCollection, Depends(db.get_users)]
) -> LoginResponse:
    loop = get_running_loop()

    try:
        idinfo = await loop.run_in_executor(
            None, 
            lambda: id_token.verify_oauth2_token(
                token,
                requests.Request(),
                settings.google_client_id
            )
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Token is invalid.")

    login_data = {
        "service": "google",
        "id": idinfo['sub']
    }

    user = await loop.run_in_executor(
        None, lambda: users.find_one({"logins": login_data})
    )

    if user is None:
        user = {
            "id": get_new_id(),
            "email": idinfo['email'],
            "name": idinfo['name'][:30],
            "used_bytes": 0,
            "logins": [login_data],
            "walls": []
        }

        await loop.run_in_executor(
            None, lambda: users.insert_one(user)
        )

    return LoginResponse(
        token=get_token(user['id'])
    )
