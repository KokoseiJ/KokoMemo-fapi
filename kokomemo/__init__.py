from .api import router as api

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

app = FastAPI()

app.include_router(
    api,
    prefix="/api"
)


@app.get("/")
async def meow():
    return PlainTextResponse("ああ！夏を今もう一回！！")
