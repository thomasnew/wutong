import uuid
from contextlib import contextmanager

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import CommentModel
from app.schemas.models import Comment
from app.services.security import now_utc


class CommentService:
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
    def _to_comment(row: CommentModel) -> Comment:
        return Comment(
            id=row.id,
            photo_id=row.photo_id,
            user_id=row.user_id,
            content=row.content,
            created_at=row.created_at,
        )

    def list_by_photo(self, photo_id: str) -> list[Comment]:
        with self._session() as db:
            rows = db.execute(
                select(CommentModel).where(CommentModel.photo_id == photo_id).order_by(CommentModel.created_at.desc())
            ).scalars().all()
            return [self._to_comment(row) for row in rows]

    def list_all(self) -> list[Comment]:
        with self._session() as db:
            rows = db.execute(select(CommentModel)).scalars().all()
            return [self._to_comment(row) for row in rows]

    def add(self, photo_id: str, user_id: str, content: str) -> Comment:
        if not content.strip():
            raise ValueError("empty comment")
        with self._session() as db:
            row = CommentModel(
                id=str(uuid.uuid4()),
                photo_id=photo_id,
                user_id=user_id,
                content=content.strip(),
                created_at=now_utc(),
            )
            db.add(row)
            db.flush()
            return self._to_comment(row)

    def delete(self, comment_id: str, actor_id: str, actor_role: str) -> None:
        with self._session() as db:
            target = db.get(CommentModel, comment_id)
            if not target:
                raise ValueError("comment not found")
            if actor_role != "admin" and target.user_id != actor_id:
                raise PermissionError("forbidden")
            db.delete(target)
