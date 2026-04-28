from contextlib import contextmanager

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.models import TokenModel
from app.schemas.models import User
from app.services.security import new_token, now_utc, token_expire, verify_password
from app.services.user_service import UserService


class AuthService:
    def __init__(self, session_factory: sessionmaker, user_service: UserService) -> None:
        self.session_factory = session_factory
        self.user_service = user_service

    @contextmanager
    def _session(self) -> Session:
        db = self.session_factory()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def login(self, username: str, password: str) -> tuple[str, User]:
        user = self.user_service.get_by_username(username)
        if not user or not verify_password(password, user.password_hash):
            raise ValueError("invalid credentials")
        if user.status != "active":
            raise ValueError("user disabled")
        with self._session() as db:
            token = TokenModel(
                token=new_token(),
                user_id=user.id,
                expire_at=token_expire(settings.token_ttl_days).replace(tzinfo=None),
                last_seen_at=now_utc().replace(tzinfo=None),
            )
            db.add(token)
            return token.token, user

    def logout(self, token: str) -> None:
        with self._session() as db:
            row = db.get(TokenModel, token)
            if row:
                db.delete(row)

    def get_user_by_token(self, token: str) -> User | None:
        # MySQL DATETIME is loaded as naive datetime by default with PyMySQL.
        # Normalize to naive UTC to avoid naive/aware comparison errors.
        now = now_utc().replace(tzinfo=None)
        with self._session() as db:
            matched = db.execute(select(TokenModel).where(TokenModel.token == token)).scalars().first()
            if not matched:
                return None
            if matched.expire_at < now:
                db.delete(matched)
                return None

            matched.last_seen_at = now
            matched.expire_at = token_expire(settings.token_ttl_days).replace(tzinfo=None)
            user = self.user_service.get_by_id(matched.user_id)
            return user
