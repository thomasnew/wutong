from app.storage.json_store import JsonStore


class SettingsService:
    def __init__(self, store: JsonStore) -> None:
        self.store = store
        self.file_name = "app_settings.json"
        self.default_speed = 12

    def get_settings(self) -> dict:
        rows = self.store.read(self.file_name)
        if not rows:
            data = {"marquee_speed_seconds": self.default_speed}
            self.store.write(self.file_name, [data])
            return data
        row = rows[0]
        speed = row.get("marquee_speed_seconds", self.default_speed)
        try:
            speed = int(speed)
        except Exception:
            speed = self.default_speed
        if speed < 4:
            speed = 4
        if speed > 60:
            speed = 60
        return {"marquee_speed_seconds": speed}

    def update_marquee_speed(self, seconds: int) -> dict:
        if seconds < 4:
            seconds = 4
        if seconds > 60:
            seconds = 60
        data = {"marquee_speed_seconds": seconds}
        self.store.write(self.file_name, [data])
        return data
