import uuid
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS

from app.schemas.models import Photo
from app.services.security import now_utc
from app.storage.json_store import JsonStore


def _to_utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class PhotoService:
    def __init__(self, store: JsonStore, photos_root: Path) -> None:
        self.store = store
        self.photos_root = photos_root
        self.file_name = "photos.json"
        self.allowed = {".jpg", ".jpeg", ".png"}

    def list_photos(self, folder: str | None = None) -> list[Photo]:
        rows = [Photo(**row) for row in self.store.read(self.file_name)]
        if folder:
            rows = [p for p in rows if p.folder_path.startswith(folder)]
        return sorted(rows, key=lambda p: (p.captured_at or p.updated_at), reverse=True)

    def get_photo(self, photo_id: str) -> Photo | None:
        for p in self.list_photos():
            if p.id == photo_id:
                return p
        return None

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
        rows = self.store.read(self.file_name)
        for row in rows:
            if row["id"] == photo_id:
                if title is not None:
                    row["title"] = title
                if description is not None:
                    row["description"] = description
                if tags is not None:
                    row["tags"] = tags
                if location_text is not None:
                    row["location_text"] = location_text
                if captured_at is not None:
                    row["captured_at"] = captured_at.isoformat()
                row["metadata_source"] = "manual"
                row["metadata_updated_by"] = user_id
                row["updated_at"] = now_utc().isoformat()
                self.store.write(self.file_name, rows)
                return Photo(**row)
        raise ValueError("photo not found")

    def folder_tree(self) -> dict:
        root = {"name": "/", "path": "", "children": []}
        if not self.photos_root.exists():
            return root

        nodes: dict[str, dict] = {"": root}
        # Build folder tree from filesystem directories so empty child folders
        # are still visible in the sidebar.
        for dir_path in sorted([p for p in self.photos_root.rglob("*") if p.is_dir()]):
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
        existing = {p.relative_path: p for p in self.list_photos()}
        now = now_utc()
        seen: set[str] = set()
        created = 0
        updated = 0

        for file_path in self.photos_root.rglob("*"):
            if file_path.suffix.lower() not in self.allowed or not file_path.is_file():
                continue
            rel = file_path.relative_to(self.photos_root).as_posix()
            seen.add(rel)
            meta = self._extract_metadata(file_path)
            if rel not in existing:
                parent = Path(rel).parent.as_posix()
                folder_path = "" if parent == "." else parent
                photo = Photo(
                    id=str(uuid.uuid4()),
                    relative_path=rel,
                    folder_path=folder_path,
                    filename=file_path.name,
                    captured_at=meta["captured_at"],
                    gps_lat=meta["gps_lat"],
                    gps_lng=meta["gps_lng"],
                    location_text="",
                    metadata_source=meta["metadata_source"],
                    updated_at=now,
                    created_at=now,
                )
                existing[rel] = photo
                created += 1
            else:
                p = existing[rel]
                p.filename = file_path.name
                parent = Path(rel).parent.as_posix()
                p.folder_path = "" if parent == "." else parent
                p.updated_at = now
                if p.metadata_source != "manual":
                    p.captured_at = meta["captured_at"]
                    p.gps_lat = meta["gps_lat"]
                    p.gps_lng = meta["gps_lng"]
                    p.metadata_source = meta["metadata_source"]
                updated += 1

        deleted = 0
        for rel in list(existing):
            if rel not in seen:
                del existing[rel]
                deleted += 1

        self.store.write(
            self.file_name,
            [p.model_dump(mode="json") for p in existing.values()],
        )
        return {"created": created, "updated": updated, "deleted": deleted}

    def _extract_metadata(self, path: Path) -> dict:
        captured_at: datetime | None = None
        gps_lat: float | None = None
        gps_lng: float | None = None
        metadata_source = "unknown"
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
