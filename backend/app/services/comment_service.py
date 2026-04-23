import uuid

from app.schemas.models import Comment
from app.services.security import now_utc
from app.storage.json_store import JsonStore


class CommentService:
    def __init__(self, store: JsonStore) -> None:
        self.store = store
        self.file_name = "comments.json"

    def list_by_photo(self, photo_id: str) -> list[Comment]:
        rows = [Comment(**row) for row in self.store.read(self.file_name)]
        return [c for c in rows if c.photo_id == photo_id]

    def list_all(self) -> list[Comment]:
        return [Comment(**row) for row in self.store.read(self.file_name)]

    def add(self, photo_id: str, user_id: str, content: str) -> Comment:
        if not content.strip():
            raise ValueError("empty comment")
        comment = Comment(
            id=str(uuid.uuid4()),
            photo_id=photo_id,
            user_id=user_id,
            content=content.strip(),
            created_at=now_utc(),
        )
        rows = self.store.read(self.file_name)
        rows.append(comment.model_dump(mode="json"))
        self.store.write(self.file_name, rows)
        return comment

    def delete(self, comment_id: str, actor_id: str, actor_role: str) -> None:
        rows = self.store.read(self.file_name)
        target = next((r for r in rows if r["id"] == comment_id), None)
        if not target:
            raise ValueError("comment not found")
        if actor_role != "admin" and target["user_id"] != actor_id:
            raise PermissionError("forbidden")
        rows = [r for r in rows if r["id"] != comment_id]
        self.store.write(self.file_name, rows)
