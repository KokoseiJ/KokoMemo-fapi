from .config import config
from .logger import logger
from .models import Session, User
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from bson.codec_options import CodecOptions
import jwt
from datetime import datetime, timedelta, UTC
from typing import Callable
from secrets import token_urlsafe
from math import floor

client = None
db = None

options = CodecOptions(tz_aware=True)


async def db_connect(url: str = None) -> None:
    global client, db

    if client is not None:
        logger.warning("DB has already been connected!")
        return

    if url is None:
        url = config.mongodb_url

    logger.debug("Attempting to connect to %s", url)

    client = AsyncIOMotorClient(url)
    db = client[config.db_name]

    await db.command("ping")

    logger.debug("MongoDB connected!")


def get_collection(name: str) -> Callable[[], AsyncIOMotorCollection]:
    def collection_dependency() -> AsyncIOMotorCollection:
        return db[name].with_options(options)


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
