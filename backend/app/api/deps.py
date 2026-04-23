from fastapi import Depends, Header, HTTPException, status

from app.core.config import settings
from app.schemas.models import User
from app.services.auth_service import AuthService
from app.services.comment_service import CommentService
from app.services.like_service import LikeService
from app.services.photo_service import PhotoService
from app.services.settings_service import SettingsService
from app.services.user_service import UserService
from app.storage.json_store import JsonStore

store = JsonStore(settings.data_dir)
user_service = UserService(store)
auth_service = AuthService(store, user_service)
photo_service = PhotoService(store, settings.photos_root)
comment_service = CommentService(store)
like_service = LikeService(store)
settings_service = SettingsService(store)


def get_current_user(authorization: str = Header(default="")) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing token")
    token = authorization.removeprefix("Bearer ").strip()
    user = auth_service.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    return user


def admin_required(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin required")
    return user
