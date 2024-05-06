from .db import get_collection
from .config import config
from .models import User, Session, Token
from .logger import logger
import jwt
from jwt.exceptions import InvalidTokenError
from secrets import token_urlsafe
from datetime import datetime, timedelta, UTC


async def verify_token(token: str) -> tuple[Token, User] | bool:
    """
    Checks jwt validity, session and exp
    """

    try:
        data = jwt.decode(
            token, config.secret, algorithms=["HS256"],
            options={
                "require": ["typ", "sub", "sid", "iat", "exp"]
            }
        )
    except InvalidTokenError:
        return False

    data = Token(**data)

    if data.typ == "AT":
        pass
    elif data.typ == "RT":
        if not data.rid:
            return False
    else:
        return False

    users = get_collection("users")()

    user = await users.find_one(
        {"id": data['sub'], "sessions.id": data['sid']}
    )

    if not user:
        return False

    user = User(**user)

    session = [
        session for session in user.sessions
        if session.id == data.sid
    ][0]

    if data.typ == "RT" and session.current_refresh_id != data.rid:
        logger.warning("Duplicate Refresh Token detected: %s", data)
        await users.update_one(
            {"id": user.id}, {"$pull": {"sessions": {"id": data.sid}}}
        )
        return False

    return (data, user)


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
    session_ids = [session['id'] for session in user['sessions']]
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
