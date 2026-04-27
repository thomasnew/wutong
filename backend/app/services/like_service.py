from contextlib import contextmanager

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import LikeModel
from app.schemas.models import Like
from app.services.security import now_utc


class LikeService:
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
    def _to_like(row: LikeModel) -> Like:
        return Like(photo_id=row.photo_id, user_id=row.user_id, created_at=row.created_at)

    def count_by_photo(self, photo_id: str) -> int:
        with self._session() as db:
            count = db.execute(
                select(func.count(LikeModel.id)).where(LikeModel.photo_id == photo_id)
            ).scalar_one()
            return int(count)

    def list_by_photo(self, photo_id: str) -> list[Like]:
        with self._session() as db:
            rows = db.execute(
                select(LikeModel).where(LikeModel.photo_id == photo_id).order_by(LikeModel.created_at.desc())
            ).scalars().all()
            return [self._to_like(row) for row in rows]

    def list_all(self) -> list[Like]:
        with self._session() as db:
            rows = db.execute(select(LikeModel)).scalars().all()
            return [self._to_like(row) for row in rows]

    def has_liked(self, photo_id: str, user_id: str) -> bool:
        with self._session() as db:
            row = db.execute(
                select(LikeModel.id).where(LikeModel.photo_id == photo_id, LikeModel.user_id == user_id)
            ).first()
            return row is not None

    def like(self, photo_id: str, user_id: str) -> None:
        with self._session() as db:
            exists = db.execute(
                select(LikeModel.id).where(LikeModel.photo_id == photo_id, LikeModel.user_id == user_id)
            ).first()
            if exists:
                return
            db.add(LikeModel(photo_id=photo_id, user_id=user_id, created_at=now_utc()))

    def unlike(self, photo_id: str, user_id: str) -> None:
        with self._session() as db:
            row = db.execute(
                select(LikeModel).where(LikeModel.photo_id == photo_id, LikeModel.user_id == user_id)
            ).scalars().first()
            if row:
                db.delete(row)
