import json
import threading
from pathlib import Path
from typing import Any


class JsonStore:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def read(self, name: str) -> list[dict[str, Any]]:
        path = self.base_dir / name
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def write(self, name: str, data: list[dict[str, Any]]) -> None:
        path = self.base_dir / name
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        with self._lock:
            with tmp_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            tmp_path.replace(path)
