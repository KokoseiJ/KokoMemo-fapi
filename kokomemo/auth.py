from .db import get_collection
from .config import config
from .models import User, Session, Token
from pymongo import ReturnDocument
import jwt
from jwt.exceptions import InvalidTokenError
from collections.abc import Sequence
from secrets import token_urlsafe
from datetime import datetime, timedelta, UTC


def verify_token(token: str) -> Token | None:
    """
    Checks jwt validity and exp
    """

    try:
        data = jwt.decode(
            token, config.secret, algorithms=["HS256"],
            options={
                "require": ["typ", "sub", "sid", "iat", "exp"]
            }
        )
    except InvalidTokenError:
        return None

    data = Token(**data)

    if data.typ == "AT":
        return data
    elif data.typ == "RT":
        if not data.rid:
            return None
    else:
        return None

    return data


def get_new_tokens(user_id: str, session_id: str, refresh_id: str, now=None,
                   ttl: int = config.refresh_ttl) -> tuple[str, str]:
    if now is None:
        now = datetime.now(UTC)

    access_body = Token(
        typ="AT",
        sub=user_id,
        sid=session_id,
        iat=now,
        exp=now + timedelta(seconds=config.access_ttl)
    )

    refresh_body = Token(
        typ="RT",
        sub=user_id,
        sid=session_id,
        iat=now,
        exp=now + timedelta(seconds=ttl)
    )

    return (
        jwt.encode(access_body.model_dump(), config.secret),
        jwt.encode(refresh_body.model_dump(), config.secret)
    )


async def new_session(user: User, ttl: int = config.refresh_ttl) \
                -> tuple[str, tuple[str, str]]:
    now = datetime.now(UTC)
    session_ids = [session.id for session in user.sessions]
    new_id = get_new_id(session_ids)
    new_refresh_id = get_new_id()
    session = Session(
        id=new_id,
        current_refresh_id=new_refresh_id,
        created_at=now,
        expires_at=now + timedelta(seconds=ttl)
    )

    await get_collection("users").update_one(
        {"id": user.id},
        {"$push": {"sessions": session.model_dump()}}
    )

    return (new_id, get_new_tokens(user.id, new_id, new_refresh_id, now, ttl))


async def get_user(query: str | dict) -> User | None:
    """
    Queries user while wiping out expired sessions
    """

    if isinstance(query, str):
        query = {"id": query}
    elif not isinstance(query, dict):
        raise ValueError("query should be str or dict")

    user = await get_collection("users").find_one_and_update(
        query,
        {"$pull": {"sessions.expires_at": {"$lte": datetime.now(UTC)}}},
        return_document=ReturnDocument.AFTER
    )

    if not user:
        return None

    return User(**user)


async def get_session_ids(user_id: str) -> list[str]:
    user = await get_user(user_id)
    if user is None:
        raise RuntimeError("user %s not found", user_id)
    return [session.id for session in user.sessions]


async def get_user_ids() -> list[str]:
    cursor = get_collection("users").find({}, {"id": 1})
    return [x['id'] async for x in cursor]


def get_new_id(ids: Sequence[str] = [], token_len: int = 9) -> str:
    new_id = None
    while not new_id or new_id in ids:
        new_id = token_urlsafe(9)

    return new_id
