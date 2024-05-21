from .api import router as api
from .db import db_connect
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db_connect()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(
    api,
    prefix="/api"
)


@app.get("/")
async def meow():
    return PlainTextResponse("ああ！夏を今もう一回！！")
