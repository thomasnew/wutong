import os
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import CommentModel, LikeModel, PhotoModel
from app.schemas.models import Photo
from app.services.security import now_utc


def _to_utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class PhotoService:
    def __init__(self, session_factory: sessionmaker, photos_root: Path) -> None:
        self.session_factory = session_factory
        self.photos_root = photos_root
        self.image_exts = {".jpg", ".jpeg", ".png", ".webp"}
        self.video_exts = {
            ".mp4",
            ".mov",
            ".webm",
            ".m4v",
            ".avi",
            ".mkv",
            ".flv",
            ".wmv",
            ".3gp",
            ".ogv",
            ".ts",
            ".m2ts",
            ".mts",
            ".mpg",
            ".mpeg",
        }
        self.allowed = self.image_exts | self.video_exts

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
    def _to_photo(row: PhotoModel) -> Photo:
        return Photo(
            id=row.id,
            relative_path=row.relative_path,
            folder_path=row.folder_path,
            filename=row.filename,
            media_type=row.media_type,  # type: ignore[arg-type]
            title=row.title,
            description=row.description,
            tags=list(row.tags or []),
            captured_at=row.captured_at,
            gps_lat=row.gps_lat,
            gps_lng=row.gps_lng,
            location_text=row.location_text,
            metadata_source=row.metadata_source,  # type: ignore[arg-type]
            metadata_updated_by=row.metadata_updated_by,
            updated_at=row.updated_at,
            created_at=row.created_at,
        )

    def list_photos(self, folder: str | None = None) -> list[Photo]:
        with self._session() as db:
            query = select(PhotoModel)
            if folder:
                query = query.where(PhotoModel.folder_path.startswith(folder))
            rows = db.execute(query).scalars().all()
            photos = [self._to_photo(row) for row in rows]
            return sorted(photos, key=lambda p: (p.captured_at or p.updated_at), reverse=True)

    def get_photo(self, photo_id: str) -> Photo | None:
        with self._session() as db:
            row = db.get(PhotoModel, photo_id)
            return self._to_photo(row) if row else None

    def update_metadata(
        self,
        photo_id: str,
        title: str | None,
        description: str | None,
        tags: list[str] | None,
        location_text: str | None,
        captured_at: datetime | None,
        user_id: str,
    ) -> Photo:
        with self._session() as db:
            row = db.get(PhotoModel, photo_id)
            if not row:
                raise ValueError("photo not found")
            if title is not None:
                row.title = title
            if description is not None:
                row.description = description
            if tags is not None:
                row.tags = tags
            if location_text is not None:
                row.location_text = location_text
            if captured_at is not None:
                row.captured_at = captured_at
            row.metadata_source = "manual"
            row.metadata_updated_by = user_id
            row.updated_at = now_utc()
            db.flush()
            return self._to_photo(row)

    def folder_tree(self) -> dict:
        root = {"name": "/", "path": "", "children": []}
        if not self.photos_root.exists():
            return root

        nodes: dict[str, dict] = {"": root}
        dirs, _ = self._walk_photos_root()
        # Build folder tree from filesystem directories so empty child folders
        # are still visible in the sidebar.
        for dir_path in sorted(dirs):
            rel = dir_path.relative_to(self.photos_root).as_posix()
            if rel == ".":
                continue
            parts = [p for p in rel.split("/") if p]
            current_path = ""
            for part in parts:
                parent_path = current_path
                current_path = f"{current_path}/{part}" if current_path else part
                if current_path not in nodes:
                    node = {"name": part, "path": current_path, "children": []}
                    nodes[current_path] = node
                    nodes[parent_path]["children"].append(node)
        return root

    def scan(self) -> dict[str, int]:
        with self._session() as db:
            existing_rows = db.execute(select(PhotoModel)).scalars().all()
            existing = {row.relative_path: row for row in existing_rows}
            id_remap: dict[str, str] = {}
            for rel, row in existing.items():
                stable_id = self._stable_photo_id(rel)
                if row.id != stable_id:
                    id_remap[row.id] = stable_id
                    row.id = stable_id

            if id_remap:
                for old_id, new_id in id_remap.items():
                    for like in db.execute(select(LikeModel).where(LikeModel.photo_id == old_id)).scalars().all():
                        like.photo_id = new_id
                    for comment in db.execute(
                        select(CommentModel).where(CommentModel.photo_id == old_id)
                    ).scalars().all():
                        comment.photo_id = new_id

            now = now_utc()
            seen: set[str] = set()
            created = 0
            updated = 0

            _, files = self._walk_photos_root()
            for file_path in sorted(files):
                if file_path.suffix.lower() not in self.allowed or not file_path.is_file():
                    continue
                rel = file_path.relative_to(self.photos_root).as_posix()
                seen.add(rel)
                media_type = self._detect_media_type(file_path)
                meta = self._extract_metadata(file_path, media_type=media_type)
                if rel not in existing:
                    parent = Path(rel).parent.as_posix()
                    folder_path = "" if parent == "." else parent
                    row = PhotoModel(
                        id=self._stable_photo_id(rel),
                        relative_path=rel,
                        folder_path=folder_path,
                        filename=file_path.name,
                        media_type=media_type,
                        captured_at=meta["captured_at"],
                        gps_lat=meta["gps_lat"],
                        gps_lng=meta["gps_lng"],
                        location_text="",
                        metadata_source=meta["metadata_source"],
                        updated_at=now,
                        created_at=now,
                    )
                    db.add(row)
                    existing[rel] = row
                    created += 1
                else:
                    row = existing[rel]
                    row.filename = file_path.name
                    row.media_type = media_type
                    parent = Path(rel).parent.as_posix()
                    row.folder_path = "" if parent == "." else parent
                    row.updated_at = now
                    if row.metadata_source != "manual":
                        row.captured_at = meta["captured_at"]
                        row.gps_lat = meta["gps_lat"]
                        row.gps_lng = meta["gps_lng"]
                        row.metadata_source = meta["metadata_source"]
                    updated += 1

            deleted = 0
            for rel in list(existing):
                if rel not in seen:
                    db.delete(existing[rel])
                    deleted += 1

            return {"created": created, "updated": updated, "deleted": deleted}

    def _extract_metadata(self, path: Path, media_type: str) -> dict:
        captured_at: datetime | None = None
        gps_lat: float | None = None
        gps_lng: float | None = None
        metadata_source = "unknown"
        if media_type == "image":
            try:
                with Image.open(path) as img:
                    exif = img.getexif()
                    exif_map = {TAGS.get(k, k): v for k, v in exif.items()}
                    if "DateTimeOriginal" in exif_map:
                        raw = exif_map["DateTimeOriginal"]
                        captured_at = _to_utc(datetime.strptime(raw, "%Y:%m:%d %H:%M:%S"))
                        metadata_source = "exif"
                    gps = exif_map.get("GPSInfo")
                    if gps:
                        gps_map = {GPSTAGS.get(k, k): v for k, v in gps.items()}
                        gps_lat = self._gps_to_decimal(
                            gps_map.get("GPSLatitude"), gps_map.get("GPSLatitudeRef")
                        )
                        gps_lng = self._gps_to_decimal(
                            gps_map.get("GPSLongitude"), gps_map.get("GPSLongitudeRef")
                        )
            except Exception:
                pass

        if not captured_at:
            captured_at = _to_utc(datetime.fromtimestamp(path.stat().st_mtime))
            metadata_source = "mtime"

        return {
            "captured_at": captured_at,
            "gps_lat": gps_lat,
            "gps_lng": gps_lng,
            "metadata_source": metadata_source,
        }

    def _detect_media_type(self, path: Path) -> str:
        ext = path.suffix.lower()
        if ext in self.video_exts:
            return "video"
        return "image"

    def _stable_photo_id(self, relative_path: str) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"media:{relative_path}"))

    def _walk_photos_root(self) -> tuple[list[Path], list[Path]]:
        dirs: list[Path] = []
        files: list[Path] = []
        if not self.photos_root.exists():
            return dirs, files

        visited_real_dirs: set[str] = set()
        for current_dir, dirnames, filenames in os.walk(self.photos_root, followlinks=True):
            real_current = os.path.realpath(current_dir)
            if real_current in visited_real_dirs:
                dirnames[:] = []
                continue
            visited_real_dirs.add(real_current)

            current_path = Path(current_dir)
            if current_path != self.photos_root:
                dirs.append(current_path)

            # Prevent symlink cycles by pruning children whose real path was visited.
            kept_dirnames: list[str] = []
            for dirname in dirnames:
                real_child = os.path.realpath(current_path / dirname)
                if real_child in visited_real_dirs:
                    continue
                kept_dirnames.append(dirname)
            dirnames[:] = kept_dirnames

            for filename in filenames:
                files.append(current_path / filename)

        return dirs, files

    @staticmethod
    def _gps_to_decimal(values, ref):
        if not values:
            return None
        try:
            d, m, s = values
            decimal = float(d) + float(m) / 60 + float(s) / 3600
            if ref in ("S", "W"):
                decimal = -decimal
            return decimal
        except Exception:
            return None
