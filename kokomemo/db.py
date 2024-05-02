from .config import config
from .logger import logger
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from typing import Callable

client = None
db = None


async def db_connect(url=None):
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


def get_collection(name) -> Callable[[], AsyncIOMotorCollection]:
    def collection_dependency() -> AsyncIOMotorCollection:
        return db[name]
