from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


Role = Literal["admin", "user"]


class User(BaseModel):
    id: str
    username: str
    password_hash: str
    role: Role = "user"
    status: Literal["active", "disabled"] = "active"
    created_at: datetime


class TokenRecord(BaseModel):
    token: str
    user_id: str
    expire_at: datetime
    last_seen_at: datetime


class Photo(BaseModel):
    id: str
    relative_path: str
    folder_path: str
    filename: str
    title: str = ""
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    captured_at: datetime | None = None
    gps_lat: float | None = None
    gps_lng: float | None = None
    location_text: str = ""
    metadata_source: Literal["exif", "manual", "mtime", "unknown"] = "unknown"
    metadata_updated_by: str | None = None
    updated_at: datetime
    created_at: datetime


class Comment(BaseModel):
    id: str
    photo_id: str
    user_id: str
    content: str
    created_at: datetime


class Like(BaseModel):
    photo_id: str
    user_id: str
    created_at: datetime
