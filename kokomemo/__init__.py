from .api import router as api
from .db import db_connect
from .logger import logger
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db_connect()
    yield


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def log_middleware(request: Request, call_next):
    logger.debug("%s: %s", request.method, request.headers)
    response = await call_next(request)
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://kokoseij.github.io",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(
    api,
    prefix="/api"
)


@app.get("/")
async def meow():
    return PlainTextResponse("ああ！夏を今もう一回！！")
