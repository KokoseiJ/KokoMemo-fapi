from pymongo import MongoClient
from pymongo.database import Database as MongoDatabase
from pymongo.collection import Collection as MongoCollection

from asyncio import get_running_loop


class MongoManager:
    def __init__(self, url: str, name: str):
        self.url = url
        self.name = name
        self.mongo = None
        self.db = None
        self.users = None
        self.memos = None

    async def connect(self) -> MongoClient:
        self.mongo = await get_running_loop().run_in_executor(
            None, lambda: MongoClient(self.url)
        )

        return self.mongo

    async def get_db(self) -> MongoDatabase:
        if self.mongo is None:
            await self.connect()

        self.db = await get_running_loop().run_in_executor(
            None, lambda: self.mongo[self.name]
        )

        return self.db

    async def get_collection(self, name) -> MongoCollection:
        if self.db is None:
            await self.get_db()

        return await get_running_loop().run_in_executor(
            None, lambda: self.db[name]
        )

    async def get_users(self) -> MongoCollection:
        if self.users is None:
            self.users = await self.get_collection("users")

        return self.users

    async def get_memos(self) -> MongoCollection:
        if self.memos is None:
            self.memos = await self.get_collection("memos")
        return self.memos
