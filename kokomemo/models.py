from pydantic import BaseModel
from datetime import datetime, timedelta


class Session(BaseModel):
    id: str
    name: str
    last_ip: str
    created_at: datetime
    last_refresh: datetime
    refresh_ttl: timedelta


class Integration(BaseModel):
    service: str
    data: dict


class Wall(BaseModel):
    id: str
    name: str
    colour: int
    created_at: datetime
    modified_at: datetime


class User(BaseModel):
    id: str
    name: str
    email: str
    used_bytes: int
    created_at: datetime
    sessions: list[Session]
    integrations: list[Integration]
    walls: list[Wall]
