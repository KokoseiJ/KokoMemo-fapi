from pydantic import BaseModel, Field
from datetime import datetime, UTC


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
    created_at: datetime = Field(default_factory=lambda: datetime(UTC))
    modified_at: datetime = Field(default_factory=lambda: datetime(UTC))


class User(BaseModel):
    id: str
    name: str
    email: str
    used_bytes: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime(UTC))
    sessions: list[Session] = []
    integrations: list[Integration]
    walls: list[Wall] = []
