from kokomemo.config import Settings, get_config
from kokomemo.db import collection_depends
from kokomemo.auth import (
    get_new_id, get_user_ids, get_user,
    new_session, get_new_tokens, verify_token
)
from kokomemo.models import User, Integration
from kokomemo.logger import logger
from kokomemo.dependencies.auth import InvalidToken, LoginInfo, check_user
from kokomemo.v1.models import BaseResponse, Meta
from pydantic import BaseModel
from fastapi import APIRouter, Body, Depends
from motor.motor_asyncio import AsyncIOMotorCollection as Collection
from pymongo import ReturnDocument
from google.oauth2 import id_token
from google.auth.transport import requests
from typing import Annotated
from datetime import datetime, timedelta, UTC
import asyncio

router = APIRouter()


class LoginTokens(BaseModel):
    access_token: str
    refresh_token: str


class LoginResponse(BaseResponse):
    data: LoginTokens


async def get_google_idinfo(
    token: Annotated[
        str, Body(description="Token from Google")
    ],
    config: Annotated[Settings, Depends(get_config)]
) -> dict:
    try:
        return await asyncio.get_running_loop().run_in_executor(
            None, lambda: id_token.verify_oauth_token(
                token, requests.Request(), config.google_id
            )
        )
    except ValueError:
        logger.warning("validation failed: %s", token)
        raise InvalidToken()


@router.post("/google")
async def google_login(
    idinfo: Annotated[dict, Depends(get_google_idinfo)],
    users: Annotated[Collection, Depends(collection_depends("users"))]
) -> LoginResponse:
    user = await get_user({
        'integrations.service': 'google',
        'integrations.data.id': idinfo['sub']
    })

    if not user:
        logger.debug(
            "Google ID %s not found, searching for email %s",
            idinfo['sub'],
            idinfo['email']
        )
        user = await users.find_one_and_update(
            {"email": idinfo['email']},
            {
                "$push": {
                    "integrations": {
                        'service': 'google',
                        'data': {'id': idinfo['sub']}
                    }
                }
            },
            return_document=ReturnDocument.AFTER
        )

        user = User(**user)

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
            integrations=[Integration(
                service="google",
                data={"id": idinfo['sub']}
            )]
        ).model_dump()

        await users.insert_one(user)
        logger.debug("New user: %s", user)

        user = User(**user)

    session_id, (at, rt) = await new_session(user)

    return LoginResponse(
        meta=Meta(message="Login Successful."),
        data=LoginTokens(access_token=at, refresh_token=rt)
    )


@router.get("/logout")
async def logout(
    login: Annotated[LoginInfo, Depends(check_user)],
    users: Annotated[Collection, Depends(
        collection_depends("users")
    )]
):
    await users.update_one(
        {"id": login.user.id},
        {"$pull": {"sessions": {"id": login.token.sid}}}
    )

    return BaseResponse(meta=Meta(message="Session has been deleted."))


@router.get("/token/refresh")
async def refresh(
    token: Annotated[str, Body(description="Refresh Token")],
    users: Annotated[Collection, Depends(collection_depends("users"))],
    config: Annotated[Settings, Depends(get_config)]
):
    """
    This has to check:
    If user exists
    If session exists
    If session is expired
    If the refresh id matches

    Then
    Update db refresh id and exp date
    return new set of tokens
    """
    body = verify_token(token)

    if not body:
        logger.warning("Invalid token %s", token)
        raise InvalidToken()
    elif body.typ != "RT":
        logger.warning("Invalid token type %s: %s (%s)", body.typ, token, body)
        raise InvalidToken()

    now = datetime.now(UTC)

    user = await get_user(body.sub)

    if not user:
        raise InvalidToken()

    sessions = [
        session for session in user.sessions if session.id == body.sid
    ]

    if not sessions:
        logger.warning(
            "Session %s for user %s not found: %s",
            body.sid, body.sub, token
        )
        raise InvalidToken()

    session = sessions[0]

    if session.current_refresh_id != body.rid:
        logger.warning("Duplicated Refresh Token for %s: %s(%s)",
                       body.sub, token, body)
        raise InvalidToken()
    
    new_id = get_new_id((body.rid,))

    await users.update_one(
        {"id": body.sub},
        {"$set": {
            "sessions.$[session].current_refresh_id": new_id,
            "sessions.$[session].expires_at": now + timedelta(
                seconds=config.refresh_ttl
            )
        }},
        array_filters=[{"session.id": body.sid}]
    )

    at, rt = get_new_tokens(user.id, body.sid, new_id)

    return LoginResponse(
        meta=Meta(message="Refresh Successful."),
        data=LoginTokens(access_token=at, refresh_token=rt)
    )
