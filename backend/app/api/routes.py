from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import (
    admin_required,
    auth_service,
    comment_service,
    get_current_user,
    like_service,
    photo_service,
    settings_service,
    user_service,
)
from app.schemas.models import User

router = APIRouter(prefix="/api")


def _username_map() -> dict[str, str]:
    return {u.id: u.username for u in user_service.list_users()}


def _photo_brief(p) -> dict[str, Any]:
    return {
        "photo_id": p.id,
        "title": p.title or p.filename,
        "filename": p.filename,
        "relative_path": p.relative_path,
    }


class LoginReq(BaseModel):
    username: str
    password: str


class CreateUserReq(BaseModel):
    username: str
    password: str
    role: str = "user"


class AddCommentReq(BaseModel):
    content: str = Field(min_length=1, max_length=1000)


class UpdateMetadataReq(BaseModel):
    title: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    location_text: str | None = None
    captured_at: datetime | None = None


class UpdateMarqueeSpeedReq(BaseModel):
    marquee_speed_seconds: int = Field(ge=4, le=60)


class AdminUpdateUserReq(BaseModel):
    username: str | None = None
    password: str | None = Field(default=None, min_length=4)


@router.post("/auth/login")
def login(payload: LoginReq) -> dict[str, Any]:
    try:
        token, user = auth_service.login(payload.username, payload.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    return {"token": token, "user": user.model_dump(mode="json", exclude={"password_hash"})}


@router.post("/auth/logout")
def logout(
    user: User = Depends(get_current_user),
    authorization: str = Header(default=""),
) -> dict[str, str]:
    token = authorization.removeprefix("Bearer ").strip()
    auth_service.logout(token)
    return {"message": f"bye {user.username}"}


@router.get("/auth/me")
def me(user: User = Depends(get_current_user)) -> dict[str, Any]:
    return user.model_dump(mode="json", exclude={"password_hash"})


@router.get("/settings")
def get_settings(user: User = Depends(get_current_user)) -> dict[str, Any]:
    return settings_service.get_settings()


@router.get("/folders/tree")
def folder_tree(user: User = Depends(get_current_user)) -> dict:
    return photo_service.folder_tree()


@router.get("/photos")
def list_photos(folder: str | None = None, user: User = Depends(get_current_user)) -> list[dict]:
    photos = photo_service.list_photos(folder=folder)
    return [
        {
            **p.model_dump(mode="json"),
            "like_count": like_service.count_by_photo(p.id),
            "liked_by_me": like_service.has_liked(p.id, user.id),
            "comment_count": len(comment_service.list_by_photo(p.id)),
        }
        for p in photos
    ]


@router.get("/stats/top")
def top_stats(user: User = Depends(get_current_user)) -> dict[str, list[dict]]:
    photos = photo_service.list_photos()
    photo_map = {p.id: p for p in photos}
    likes = like_service.list_all()
    comments = comment_service.list_all()

    like_count: dict[str, int] = {}
    for row in likes:
        like_count[row.photo_id] = like_count.get(row.photo_id, 0) + 1

    comment_count: dict[str, int] = {}
    for row in comments:
        comment_count[row.photo_id] = comment_count.get(row.photo_id, 0) + 1

    top_liked = sorted(
        [(pid, cnt) for pid, cnt in like_count.items() if pid in photo_map],
        key=lambda x: x[1],
        reverse=True,
    )[:10]
    top_commented = sorted(
        [(pid, cnt) for pid, cnt in comment_count.items() if pid in photo_map],
        key=lambda x: x[1],
        reverse=True,
    )[:10]

    latest_map: dict[str, datetime] = {}
    for p in photos:
        latest_map[p.id] = p.updated_at
    for row in likes:
        if row.photo_id in photo_map:
            latest_map[row.photo_id] = max(latest_map.get(row.photo_id, row.created_at), row.created_at)
    for row in comments:
        if row.photo_id in photo_map:
            latest_map[row.photo_id] = max(latest_map.get(row.photo_id, row.created_at), row.created_at)
    latest_updated = sorted(latest_map.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "top_liked": [
            {
                **_photo_brief(photo_map[pid]),
                "like_count": cnt,
            }
            for pid, cnt in top_liked
        ],
        "top_commented": [
            {
                **_photo_brief(photo_map[pid]),
                "comment_count": cnt,
            }
            for pid, cnt in top_commented
        ],
        "latest_updated": [
            {
                **_photo_brief(photo_map[pid]),
                "updated_at": ts.isoformat(),
            }
            for pid, ts in latest_updated
        ],
    }


@router.get("/photos/{photo_id}")
def get_photo(photo_id: str, user: User = Depends(get_current_user)) -> dict:
    p = photo_service.get_photo(photo_id)
    if not p:
        raise HTTPException(status_code=404, detail="photo not found")
    username_map = _username_map()
    comment_rows = comment_service.list_by_photo(p.id)
    likes = like_service.list_by_photo(p.id)
    return {
        **p.model_dump(mode="json"),
        "like_count": like_service.count_by_photo(p.id),
        "liked_by_me": like_service.has_liked(p.id, user.id),
        "liked_users": [
            {"user_id": r.user_id, "username": username_map.get(r.user_id, "unknown")}
            for r in likes
        ],
        "comments": [
            {
                **c.model_dump(mode="json"),
                "username": username_map.get(c.user_id, "unknown"),
            }
            for c in comment_rows
        ],
    }


@router.post("/photos/{photo_id}/like")
def like_photo(photo_id: str, user: User = Depends(get_current_user)) -> dict[str, str]:
    like_service.like(photo_id, user.id)
    return {"message": "liked"}


@router.delete("/photos/{photo_id}/like")
def unlike_photo(photo_id: str, user: User = Depends(get_current_user)) -> dict[str, str]:
    like_service.unlike(photo_id, user.id)
    return {"message": "unliked"}


@router.get("/photos/{photo_id}/comments")
def get_comments(photo_id: str, user: User = Depends(get_current_user)) -> list[dict]:
    username_map = _username_map()
    return [
        {
            **c.model_dump(mode="json"),
            "username": username_map.get(c.user_id, "unknown"),
        }
        for c in comment_service.list_by_photo(photo_id)
    ]


@router.post("/photos/{photo_id}/comments")
def add_comment(photo_id: str, payload: AddCommentReq, user: User = Depends(get_current_user)) -> dict:
    try:
        c = comment_service.add(photo_id, user.id, payload.content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {
        **c.model_dump(mode="json"),
        "username": user.username,
    }


@router.delete("/comments/{comment_id}")
def delete_comment(comment_id: str, user: User = Depends(get_current_user)) -> dict[str, str]:
    try:
        comment_service.delete(comment_id, actor_id=user.id, actor_role=user.role)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    return {"message": "deleted"}


@router.post("/admin/scan")
def admin_scan(user: User = Depends(admin_required)) -> dict[str, int]:
    return photo_service.scan()


@router.patch("/admin/photos/{photo_id}/metadata")
def update_metadata(photo_id: str, payload: UpdateMetadataReq, user: User = Depends(admin_required)) -> dict:
    try:
        p = photo_service.update_metadata(
            photo_id=photo_id,
            title=payload.title,
            description=payload.description,
            tags=payload.tags,
            location_text=payload.location_text,
            captured_at=payload.captured_at,
            user_id=user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return p.model_dump(mode="json")


@router.get("/admin/users")
def admin_users(user: User = Depends(admin_required)) -> list[dict]:
    return [u.model_dump(mode="json", exclude={"password_hash"}) for u in user_service.list_users()]


@router.post("/admin/users")
def create_user(payload: CreateUserReq, user: User = Depends(admin_required)) -> dict:
    try:
        new_user = user_service.create_user(
            username=payload.username, password=payload.password, role=payload.role
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return new_user.model_dump(mode="json", exclude={"password_hash"})


@router.patch("/admin/users/{user_id}")
def admin_update_user(user_id: str, payload: AdminUpdateUserReq, user: User = Depends(admin_required)) -> dict:
    if payload.username is None and payload.password is None:
        raise HTTPException(status_code=400, detail="no fields to update")
    try:
        updated = user_service.admin_update_user_credentials(
            user_id=user_id,
            new_username=payload.username,
            new_password=payload.password,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return updated.model_dump(mode="json", exclude={"password_hash"})


@router.delete("/admin/users/{user_id}")
def admin_delete_user(user_id: str, user: User = Depends(admin_required)) -> dict[str, str]:
    try:
        user_service.admin_delete_user(user_id=user_id, actor_id=user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"message": "deleted"}


@router.patch("/admin/settings/marquee-speed")
def update_marquee_speed(payload: UpdateMarqueeSpeedReq, user: User = Depends(admin_required)) -> dict:
    return settings_service.update_marquee_speed(payload.marquee_speed_seconds)
