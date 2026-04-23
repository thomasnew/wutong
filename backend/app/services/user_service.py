import uuid

from app.schemas.models import User
from app.services.security import hash_password, now_utc
from app.storage.json_store import JsonStore


class UserService:
    def __init__(self, store: JsonStore) -> None:
        self.store = store
        self.file_name = "users.json"

    def list_users(self) -> list[User]:
        return [User(**row) for row in self.store.read(self.file_name)]

    def get_by_id(self, user_id: str) -> User | None:
        for user in self.list_users():
            if user.id == user_id:
                return user
        return None

    def get_by_username(self, username: str) -> User | None:
        for user in self.list_users():
            if user.username == username:
                return user
        return None

    def ensure_admin(self, username: str, password: str) -> None:
        if self.get_by_username(username):
            return
        self.create_user(username=username, password=password, role="admin")

    def create_user(self, username: str, password: str, role: str = "user") -> User:
        if self.get_by_username(username):
            raise ValueError("username already exists")
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            password_hash=hash_password(password),
            role=role,  # type: ignore[arg-type]
            status="active",
            created_at=now_utc(),
        )
        rows = self.store.read(self.file_name)
        rows.append(user.model_dump(mode="json"))
        self.store.write(self.file_name, rows)
        return user

    def admin_update_user_credentials(
        self,
        user_id: str,
        new_username: str | None = None,
        new_password: str | None = None,
    ) -> User:
        rows = self.store.read(self.file_name)
        target = next((r for r in rows if r.get("id") == user_id), None)
        if not target:
            raise ValueError("user not found")

        if new_username is not None:
            new_username = new_username.strip()
            if not new_username:
                raise ValueError("username cannot be empty")
            for row in rows:
                if row.get("id") != user_id and row.get("username") == new_username:
                    raise ValueError("username already exists")
            target["username"] = new_username

        if new_password is not None:
            if len(new_password) < 4:
                raise ValueError("password too short")
            target["password_hash"] = hash_password(new_password)

        self.store.write(self.file_name, rows)
        return User(**target)

    def admin_delete_user(self, user_id: str, actor_id: str) -> None:
        rows = self.store.read(self.file_name)
        target = next((r for r in rows if r.get("id") == user_id), None)
        if not target:
            raise ValueError("user not found")
        if user_id == actor_id:
            raise ValueError("cannot delete current admin")

        # Keep at least one admin user in system.
        if target.get("role") == "admin":
            admin_count = len([r for r in rows if r.get("role") == "admin"])
            if admin_count <= 1:
                raise ValueError("cannot delete the last admin")

        rows = [r for r in rows if r.get("id") != user_id]
        self.store.write(self.file_name, rows)
