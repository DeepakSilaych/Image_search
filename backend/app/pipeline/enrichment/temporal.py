from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PIL import Image
from PIL.ExifTags import TAGS


class TemporalExtractor:
    def extract_datetime(self, image_path: str | Path) -> datetime | None:
        try:
            img = Image.open(image_path)
            exif = img.getexif()
            if not exif:
                return self._from_file_stat(image_path)

            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, "")
                if tag in ("DateTimeOriginal", "DateTimeDigitized", "DateTime"):
                    return datetime.strptime(str(value), "%Y:%m:%d %H:%M:%S")
        except Exception:
            pass
        return self._from_file_stat(image_path)

    def _from_file_stat(self, image_path: str | Path) -> datetime | None:
        try:
            p = Path(image_path)
            stat = p.stat()
            return datetime.fromtimestamp(stat.st_mtime)
        except Exception:
            return None

    def get_time_context(self, dt: datetime) -> dict:
        hour = dt.hour
        if 5 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 17:
            time_of_day = "afternoon"
        elif 17 <= hour < 21:
            time_of_day = "evening"
        else:
            time_of_day = "night"

        return {
            "year": dt.year,
            "month": dt.month,
            "day_of_week": dt.strftime("%A"),
            "time_of_day": time_of_day,
            "season": self._get_season(dt.month),
        }

    def _get_season(self, month: int) -> str:
        if month in (3, 4, 5):
            return "spring"
        if month in (6, 7, 8):
            return "summer"
        if month in (9, 10, 11):
            return "autumn"
        return "winter"
