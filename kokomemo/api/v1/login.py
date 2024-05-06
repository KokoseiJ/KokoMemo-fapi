from kokomemo.config import Settings, get_config
from kokomemo.db import get_collection, get_new_id, get_user_ids, new_session
from kokomemo.models import User
from kokomemo.logger import logger
from pydantic import BaseModel
from fastapi import APIRouter, Body, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection as Collection
from google.oauth2 import id_token
from google.auth.transport import requests
from typing import Annotated
import asyncio

router = APIRouter()


class InvalidToken(HTTPException):
    def __init__(self):
        super().__init__(status_code=401, detail="The token is invalid.")


class LoginResult(BaseModel):
    access_token: str
    refresh_token: str


async def get_google_idinfo(
    token: Annotated[
        str, Body(description="Token from Google")
    ],
    config: Annotated[Settings, Depends(get_config)]
) -> dict:
    try:
        return asyncio.get_running_loop.run_in_executor(
            None, lambda: id_token.verify_oauth_token(
                token, requests.Request(), config.google_id
            )
        )
    except ValueError:
        raise InvalidToken()


@router.post("/google")
async def google_login(
    idinfo: Annotated[dict, Depends(get_google_idinfo)],
    users: Annotated[Collection, Depends(get_collection("users"))]
) -> LoginResult:
    user = users.find_one({
        'integrations.service': 'google',
        'integrations.data.id': idinfo['sub']
    })

    if not user:
        logger.debug(
            "Google ID %s not found, searching for email %s",
            idinfo['sub'],
            idinfo['email']
        )
        user = users.find_one_and_update(
            {"email": idinfo['email']},
            {
                "$push": {
                    "integrations": {
                        'service': 'google',
                        'data': {'id': idinfo['sub']}
                    }
                }
            }
        )

    if not user:
        logger.debug(
            "email %s not found. Creating a new account",
            idinfo['email']
        )

        new_id = get_new_id(await get_user_ids())

        user = User(
            id=new_id,
            name=idinfo['name'],
            email=idinfo['email'],
            integrations=[{
                "service": "google",
                "data": {"id": idinfo['sub']}
            }]
        ).model_dump()

        users.insert_one(user)
        logger.debug("New user: %s", user)

    user = User(**user)

    session_id, (at, rt) = new_session(user)

    return LoginResult(access_token=at, refresh_token=rt)
