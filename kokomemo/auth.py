from .db import get_collection
from .config import config
from .models import User, Session
import jwt
from secrets import token_urlsafe
from datetime import datetime, timedelta, UTC
from math import floor


def get_new_tokens(session_id: str, refresh_id: str, now=None,
                   ttl: int = config.refresh_ttl) -> tuple[str, str]:
    if now is None:
        now = datetime.now(UTC)

    exp = now + timedelta(seconds=config.access_ttl)
    refresh_exp = now + timedelta(seconds=ttl)

    access_body = {
        "sub": session_id,
        "iat": floor(now.timestamp()),
        "exp": floor(exp.timestamp())
    }

    refresh_body = {
        "sub": session_id,
        "rid": refresh_id,
        "iat": floor(now.timestamp()),
        "exp": floor(refresh_exp.timestamp())
    }

    return (
        jwt.encode(access_body, config.secret),
        jwt.encode(refresh_body, config.secret)
    )


def new_session(user: User, ttl: int = config.refresh_ttl) \
                -> tuple[str, tuple[str, str]]:
    now = datetime.now(UTC)
    session_ids = [session['id'] for session in user['sessions']]
    new_id = get_new_id(session_ids)
    new_refresh_id = get_new_id()
    session = Session(
        id=new_id,
        new_refresh_id=new_refresh_id,
        created_at=now,
        expires_at=now + timedelta(seconds=ttl)
    )

    get_collection("users").update_one(
        {"id": user.id},
        {"$push": {"sessions": session.model_dump()}}
    )

    return (new_id, get_new_tokens(new_id, new_refresh_id, now, ttl))


async def get_session_ids(user_id: str) -> list[str]:
    user = await get_collection("users").find_one({"id": user_id})
    return [session['id'] for session in user['sessions']]


async def get_user_ids() -> list[str]:
    cursor = get_collection("users").find({}, {"id": 1})
    return [x['id'] async for x in cursor]


def get_new_id(ids: list[str] = [], token_len: int = 9) -> str:
    new_id = None
    while not new_id or new_id in ids:
        new_id = token_urlsafe(9)

    return new_id
