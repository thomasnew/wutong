#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Ensure "app" package is importable when running as a script.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select

from app.db.base import Base
from app.db.models import AppSettingModel, CommentModel, LikeModel, PhotoModel, TokenModel, UserModel
from app.db.session import SessionLocal, engine
from app.schemas.models import Comment, Like, Photo, TokenRecord, User


def _read_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"JSON file must contain a list: {path}")
    return data


def _migrate_users(data_dir: Path) -> int:
    rows = [User(**row) for row in _read_json(data_dir / "users.json")]
    count = 0
    with SessionLocal() as db:
        for row in rows:
            model = db.get(UserModel, row.id)
            if not model:
                model = UserModel(id=row.id)
                db.add(model)
            model.username = row.username
            model.password_hash = row.password_hash
            model.role = row.role
            model.status = row.status
            model.created_at = row.created_at
            count += 1
        db.commit()
    return count


def _migrate_tokens(data_dir: Path) -> int:
    rows = [TokenRecord(**row) for row in _read_json(data_dir / "tokens.json")]
    count = 0
    with SessionLocal() as db:
        for row in rows:
            model = db.get(TokenModel, row.token)
            if not model:
                model = TokenModel(token=row.token)
                db.add(model)
            model.user_id = row.user_id
            model.expire_at = row.expire_at
            model.last_seen_at = row.last_seen_at
            count += 1
        db.commit()
    return count


def _migrate_photos(data_dir: Path) -> int:
    rows = [Photo(**row) for row in _read_json(data_dir / "photos.json")]
    count = 0
    with SessionLocal() as db:
        for row in rows:
            model = db.get(PhotoModel, row.id)
            if not model:
                model = PhotoModel(id=row.id)
                db.add(model)
            model.relative_path = row.relative_path
            model.folder_path = row.folder_path
            model.filename = row.filename
            model.media_type = row.media_type
            model.title = row.title
            model.description = row.description
            model.tags = row.tags
            model.captured_at = row.captured_at
            model.gps_lat = row.gps_lat
            model.gps_lng = row.gps_lng
            model.location_text = row.location_text
            model.metadata_source = row.metadata_source
            model.metadata_updated_by = row.metadata_updated_by
            model.updated_at = row.updated_at
            model.created_at = row.created_at
            count += 1
        db.commit()
    return count


def _migrate_comments(data_dir: Path) -> int:
    rows = [Comment(**row) for row in _read_json(data_dir / "comments.json")]
    count = 0
    with SessionLocal() as db:
        for row in rows:
            model = db.get(CommentModel, row.id)
            if not model:
                model = CommentModel(id=row.id)
                db.add(model)
            model.photo_id = row.photo_id
            model.user_id = row.user_id
            model.content = row.content
            model.created_at = row.created_at
            count += 1
        db.commit()
    return count


def _migrate_likes(data_dir: Path) -> int:
    rows = [Like(**row) for row in _read_json(data_dir / "likes.json")]
    count = 0
    with SessionLocal() as db:
        for row in rows:
            exists = db.execute(
                select(LikeModel).where(LikeModel.photo_id == row.photo_id, LikeModel.user_id == row.user_id)
            ).scalars().first()
            if exists:
                exists.created_at = row.created_at
            else:
                db.add(LikeModel(photo_id=row.photo_id, user_id=row.user_id, created_at=row.created_at))
            count += 1
        db.commit()
    return count


def _migrate_settings(data_dir: Path) -> int:
    rows = _read_json(data_dir / "app_settings.json")
    if not rows:
        return 0
    speed = rows[0].get("marquee_speed_seconds", 12)
    try:
        speed = int(speed)
    except Exception:
        speed = 12
    speed = max(4, min(60, speed))
    with SessionLocal() as db:
        model = db.execute(select(AppSettingModel).limit(1)).scalars().first()
        if not model:
            model = AppSettingModel(marquee_speed_seconds=speed)
            db.add(model)
        else:
            model.marquee_speed_seconds = speed
        db.commit()
    return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate legacy JSON data into MySQL.")
    parser.add_argument(
        "--json-dir",
        default=str(BACKEND_DIR / "data"),
        help="Legacy JSON data directory (default: backend/data).",
    )
    args = parser.parse_args()

    data_dir = Path(args.json_dir).resolve()
    if not data_dir.exists():
        raise SystemExit(f"JSON directory not found: {data_dir}")

    Base.metadata.create_all(bind=engine)

    print(f"Migrating from: {data_dir}")
    users = _migrate_users(data_dir)
    photos = _migrate_photos(data_dir)
    comments = _migrate_comments(data_dir)
    likes = _migrate_likes(data_dir)
    tokens = _migrate_tokens(data_dir)
    settings = _migrate_settings(data_dir)

    print("Migration completed:")
    print(f"- users: {users}")
    print(f"- photos: {photos}")
    print(f"- comments: {comments}")
    print(f"- likes: {likes}")
    print(f"- tokens: {tokens}")
    print(f"- app_settings: {settings}")


if __name__ == "__main__":
    main()
