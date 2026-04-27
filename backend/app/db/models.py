from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16), default="user")
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True))


class TokenModel(Base):
    __tablename__ = "tokens"

    token: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    expire_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True))


class PhotoModel(Base):
    __tablename__ = "photos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    relative_path: Mapped[str] = mapped_column(String(1024), unique=True, index=True)
    folder_path: Mapped[str] = mapped_column(String(1024), default="")
    filename: Mapped[str] = mapped_column(String(255))
    media_type: Mapped[str] = mapped_column(String(16), default="image")
    title: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    captured_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    gps_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    gps_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_text: Mapped[str] = mapped_column(String(255), default="")
    metadata_source: Mapped[str] = mapped_column(String(16), default="unknown")
    metadata_updated_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True))


class CommentModel(Base):
    __tablename__ = "comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    photo_id: Mapped[str] = mapped_column(String(36), ForeignKey("photos.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), index=True)


class LikeModel(Base):
    __tablename__ = "likes"
    __table_args__ = (UniqueConstraint("photo_id", "user_id", name="uq_likes_photo_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    photo_id: Mapped[str] = mapped_column(String(36), ForeignKey("photos.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), index=True)


class AppSettingModel(Base):
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    marquee_speed_seconds: Mapped[int] = mapped_column(Integer, default=12)
