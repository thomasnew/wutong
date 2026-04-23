from app.schemas.models import Like
from app.services.security import now_utc
from app.storage.json_store import JsonStore


class LikeService:
    def __init__(self, store: JsonStore) -> None:
        self.store = store
        self.file_name = "likes.json"

    def count_by_photo(self, photo_id: str) -> int:
        rows = self.store.read(self.file_name)
        return len([r for r in rows if r["photo_id"] == photo_id])

    def list_by_photo(self, photo_id: str) -> list[Like]:
        rows = [Like(**r) for r in self.store.read(self.file_name)]
        return [r for r in rows if r.photo_id == photo_id]

    def list_all(self) -> list[Like]:
        return [Like(**r) for r in self.store.read(self.file_name)]

    def has_liked(self, photo_id: str, user_id: str) -> bool:
        rows = self.store.read(self.file_name)
        return any(r for r in rows if r["photo_id"] == photo_id and r["user_id"] == user_id)

    def like(self, photo_id: str, user_id: str) -> None:
        rows = self.store.read(self.file_name)
        if any(r for r in rows if r["photo_id"] == photo_id and r["user_id"] == user_id):
            return
        like = Like(photo_id=photo_id, user_id=user_id, created_at=now_utc())
        rows.append(like.model_dump(mode="json"))
        self.store.write(self.file_name, rows)

    def unlike(self, photo_id: str, user_id: str) -> None:
        rows = self.store.read(self.file_name)
        rows = [r for r in rows if not (r["photo_id"] == photo_id and r["user_id"] == user_id)]
        self.store.write(self.file_name, rows)
