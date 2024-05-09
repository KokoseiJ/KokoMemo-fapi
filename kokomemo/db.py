from .config import config
from .logger import logger
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from bson.codec_options import CodecOptions
from typing import Callable

client = None
db = None

options: CodecOptions = CodecOptions(tz_aware=True)


async def db_connect(url: str | None = None) -> None:
    global client, db

    if client is not None:
        logger.warning("DB has already been connected!")
        return

    if url is None:
        url = config.mongodb_url

    logger.debug("Attempting to connect to %s", url)

    client = AsyncIOMotorClient(url)
    db = client[config.dbname]

    await db.command("ping")

    logger.debug("MongoDB connected!")


def get_collection(name: str) -> AsyncIOMotorCollection:
    if db is None:
        raise RuntimeError("DB is not initialized!")
    return db[name].with_options(options)


def collection_depends(name: str) -> Callable[[], AsyncIOMotorCollection]:
    def inner_depends() -> AsyncIOMotorCollection:
        return get_collection(name)

    return inner_depends
