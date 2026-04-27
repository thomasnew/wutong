from contextlib import contextmanager

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import AppSettingModel

class SettingsService:
    def __init__(self, session_factory: sessionmaker) -> None:
        self.session_factory = session_factory
        self.default_speed = 12

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

    def get_settings(self) -> dict:
        with self._session() as db:
            row = db.execute(select(AppSettingModel).limit(1)).scalars().first()
            if not row:
                row = AppSettingModel(marquee_speed_seconds=self.default_speed)
                db.add(row)
                db.flush()
            speed = max(4, min(60, int(row.marquee_speed_seconds)))
            if speed != row.marquee_speed_seconds:
                row.marquee_speed_seconds = speed
            return {"marquee_speed_seconds": speed}

    def update_marquee_speed(self, seconds: int) -> dict:
        if seconds < 4:
            seconds = 4
        if seconds > 60:
            seconds = 60
        with self._session() as db:
            row = db.execute(select(AppSettingModel).limit(1)).scalars().first()
            if not row:
                row = AppSettingModel(marquee_speed_seconds=seconds)
                db.add(row)
            else:
                row.marquee_speed_seconds = seconds
            return {"marquee_speed_seconds": seconds}
