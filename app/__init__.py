from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .mongo import MongoManager

settings = config.Settings()
db = MongoManager(settings.mongo_url, settings.db_name)

app = FastAPI()

from .api.v1 import user, memo

v1 = APIRouter()
v1.include_router(
    user.router,
    prefix="/user",
    tags=["User"]
)
v1.include_router(
    memo.router,
    tags=["Memo"]
)

app.include_router(
    v1,
    prefix="/v1",
    tags=["v1"]
)


origins = [
    "http://localhost:5000"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/")
async def hello():
    return "あぁ！夏を今もう一回！！"
