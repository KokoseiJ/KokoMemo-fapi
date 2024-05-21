from pydantic import BaseModel


class Meta(BaseModel):
    message: str


class BaseResponse(BaseModel):
    meta: Meta
    data: BaseModel | dict | None = None
