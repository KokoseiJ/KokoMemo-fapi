from pydantic import BaseModel, Field
from datetime import datetime, UTC


class Memo(BaseModel):
    id: str
    user_id: str
    wall_id: str
    contents: str = ""
    index: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    modified_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Session(BaseModel):
    id: str
    current_refresh_id: str
    created_at: datetime
    expires_at: datetime


class Integration(BaseModel):
    service: str
    data: dict


class Wall(BaseModel):
    id: str
    name: str
    colour: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    modified_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class User(BaseModel):
    id: str
    name: str
    email: str
    used_bytes: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    sessions: list[Session] = []
    integrations: list[Integration]
    walls: list[Wall] = []


class Token(BaseModel):
    typ: str
    sub: str
    sid: str
    rid: str | None = None
    iat: datetime
    exp: datetime
