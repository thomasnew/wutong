import uuid
from contextlib import contextmanager

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import UserModel
from app.schemas.models import User
from app.services.security import hash_password, now_utc


class UserService:
    def __init__(self, session_factory: sessionmaker) -> None:
        self.session_factory = session_factory

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

    @staticmethod
    def _to_user(row: UserModel) -> User:
        return User(
            id=row.id,
            username=row.username,
            password_hash=row.password_hash,
            role=row.role,  # type: ignore[arg-type]
            status=row.status,  # type: ignore[arg-type]
            created_at=row.created_at,
        )

    def list_users(self) -> list[User]:
        with self._session() as db:
            rows = db.execute(select(UserModel).order_by(UserModel.created_at.asc())).scalars().all()
            return [self._to_user(row) for row in rows]

    def get_by_id(self, user_id: str) -> User | None:
        with self._session() as db:
            row = db.get(UserModel, user_id)
            return self._to_user(row) if row else None

    def get_by_username(self, username: str) -> User | None:
        with self._session() as db:
            row = db.execute(select(UserModel).where(UserModel.username == username)).scalars().first()
            return self._to_user(row) if row else None

    def ensure_admin(self, username: str, password: str) -> None:
        if self.get_by_username(username):
            return
        self.create_user(username=username, password=password, role="admin")

    def create_user(self, username: str, password: str, role: str = "user") -> User:
        with self._session() as db:
            exists = db.execute(select(UserModel).where(UserModel.username == username)).scalars().first()
            if exists:
                raise ValueError("username already exists")
            row = UserModel(
                id=str(uuid.uuid4()),
                username=username,
                password_hash=hash_password(password),
                role=role,
                status="active",
                created_at=now_utc(),
            )
            db.add(row)
            db.flush()
            return self._to_user(row)

    def admin_update_user_credentials(
        self,
        user_id: str,
        new_username: str | None = None,
        new_password: str | None = None,
    ) -> User:
        with self._session() as db:
            target = db.get(UserModel, user_id)
            if not target:
                raise ValueError("user not found")

            if new_username is not None:
                new_username = new_username.strip()
                if not new_username:
                    raise ValueError("username cannot be empty")
                exists = db.execute(
                    select(UserModel).where(UserModel.username == new_username, UserModel.id != user_id)
                ).scalars().first()
                if exists:
                    raise ValueError("username already exists")
                target.username = new_username

            if new_password is not None:
                if len(new_password) < 4:
                    raise ValueError("password too short")
                target.password_hash = hash_password(new_password)

            db.flush()
            return self._to_user(target)

    def admin_delete_user(self, user_id: str, actor_id: str) -> None:
        with self._session() as db:
            target = db.get(UserModel, user_id)
            if not target:
                raise ValueError("user not found")
            if user_id == actor_id:
                raise ValueError("cannot delete current admin")

            if target.role == "admin":
                admins = db.execute(select(UserModel).where(UserModel.role == "admin")).scalars().all()
                if len(admins) <= 1:
                    raise ValueError("cannot delete the last admin")

            db.delete(target)
