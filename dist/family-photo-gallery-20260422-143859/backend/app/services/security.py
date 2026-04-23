import hashlib
import secrets
from datetime import datetime, timedelta, timezone


def now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def new_token() -> str:
    return secrets.token_urlsafe(32)


def token_expire(days: int) -> datetime:
    return now_utc() + timedelta(days=days)
