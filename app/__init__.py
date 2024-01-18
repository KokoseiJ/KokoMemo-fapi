from fastapi import FastAPI, APIRouter

from . import config
from .mongo import MongoManager

settings = config.Settings()

db = MongoManager(settings.mongo_url, settings.db_name)
app = FastAPI()

from .api.v1 import user

v1 = APIRouter()
v1.include_router(
    user.router,
    prefix="/user",
    tags=["User"]
)

app.include_router(
    v1,
    prefix="/v1",
    tags=["v1"]
)


@app.get("/")
async def hello():
    return "あぁ！夏を今もう一回！！"
