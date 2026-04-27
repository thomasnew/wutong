import asyncio
import contextlib

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.deps import photo_service, user_service
from app.api.routes import router
from app.core.config import settings

app = FastAPI(title=settings.app_name)
app.include_router(router)
app.mount("/photos", StaticFiles(directory=settings.photos_root), name="photos")

if settings.static_root is not None and settings.static_root.is_dir():
    app.mount(
        "/",
        StaticFiles(directory=str(settings.static_root), html=True),
        name="frontend",
    )

_scan_task: asyncio.Task | None = None


async def _periodic_scan() -> None:
    while True:
        try:
            photo_service.scan()
        except Exception:
            pass
        await asyncio.sleep(settings.scan_interval_seconds)


@app.on_event("startup")
async def startup() -> None:
    global _scan_task
    settings.photos_root.mkdir(parents=True, exist_ok=True)
    user_service.ensure_admin(settings.admin_default_username, settings.admin_default_password)
    photo_service.scan()
    _scan_task = asyncio.create_task(_periodic_scan())


@app.on_event("shutdown")
async def shutdown() -> None:
    if _scan_task:
        _scan_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await _scan_task
