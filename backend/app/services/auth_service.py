from app.core.config import settings
from app.schemas.models import TokenRecord, User
from app.services.security import new_token, now_utc, token_expire, verify_password
from app.services.user_service import UserService
from app.storage.json_store import JsonStore


class AuthService:
    def __init__(self, store: JsonStore, user_service: UserService) -> None:
        self.store = store
        self.user_service = user_service
        self.file_name = "tokens.json"

    def login(self, username: str, password: str) -> tuple[str, User]:
        user = self.user_service.get_by_username(username)
        if not user or not verify_password(password, user.password_hash):
            raise ValueError("invalid credentials")
        if user.status != "active":
            raise ValueError("user disabled")
        token = TokenRecord(
            token=new_token(),
            user_id=user.id,
            expire_at=token_expire(settings.token_ttl_days),
            last_seen_at=now_utc(),
        )
        rows = self.store.read(self.file_name)
        rows.append(token.model_dump(mode="json"))
        self.store.write(self.file_name, rows)
        return token.token, user

    def logout(self, token: str) -> None:
        rows = self.store.read(self.file_name)
        rows = [row for row in rows if row.get("token") != token]
        self.store.write(self.file_name, rows)

    def get_user_by_token(self, token: str) -> User | None:
        now = now_utc()
        tokens = [TokenRecord(**row) for row in self.store.read(self.file_name)]
        matched = next((r for r in tokens if r.token == token), None)
        if not matched or matched.expire_at < now:
            return None

        user = self.user_service.get_by_id(matched.user_id)
        if not user:
            return None

        rows = self.store.read(self.file_name)
        for row in rows:
            if row.get("token") == token:
                row["last_seen_at"] = now.isoformat()
                row["expire_at"] = token_expire(settings.token_ttl_days).isoformat()
        self.store.write(self.file_name, rows)
        return user
