from kokomemo.models import User, Token
from kokomemo.db import collection_depends
from kokomemo.auth import verify_token, get_user
from kokomemo.logger import logger
from motor.motor_asyncio import AsyncIOMotorCollection as Collection
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import HTTPException, Depends
from pydantic import BaseModel
from typing import Annotated

security = HTTPBearer(
    scheme_name="Access Token",
    description="Access Token from login endpoint"
)


class InvalidToken(HTTPException):
    def __init__(self):
        super().__init__(status_code=401, detail="The token is invalid.")


class LoginInfo(BaseModel):
    user: User
    token: Token


async def check_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> Token:
    token = credentials.credentials
    logger.debug(type(token))
    body = verify_token(token)

    if not body:
        logger.warning("Invalid token %s", token)
        raise InvalidToken()
    elif body.typ != 'AT':
        logger.warning("Invalid token type %s: %s (%s)", body.typ, token, body)
        raise InvalidToken()

    return body


async def check_user(
    token: Annotated[Token, Depends(check_token)],
    users: Annotated[Collection, Depends(collection_depends("users"))]
) -> LoginInfo:
    user = await get_user(token.sub)

    if not user:
        logger.warning("User %s not found: %s", token.sub, token)
        raise InvalidToken()

    return LoginInfo(user=user, token=token)
