from __future__ import annotations

from pathlib import Path

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS


class LocationExtractor:
    def extract_gps(self, image_path: str | Path) -> dict | None:
        try:
            img = Image.open(image_path)
            exif = img.getexif()
            if not exif:
                return None

            gps_ifd = exif.get_ifd(0x8825)
            if not gps_ifd:
                return None

            gps_data = {}
            for tag_id, value in gps_ifd.items():
                tag = GPSTAGS.get(tag_id, tag_id)
                gps_data[tag] = value

            lat = self._convert_dms_to_decimal(
                gps_data.get("GPSLatitude"), gps_data.get("GPSLatitudeRef")
            )
            lon = self._convert_dms_to_decimal(
                gps_data.get("GPSLongitude"), gps_data.get("GPSLongitudeRef")
            )

            if lat is not None and lon is not None:
                return {"latitude": lat, "longitude": lon}
        except Exception:
            pass
        return None

    def _convert_dms_to_decimal(self, dms, ref) -> float | None:
        if not dms or not ref:
            return None
        try:
            degrees = float(dms[0])
            minutes = float(dms[1])
            seconds = float(dms[2])
            decimal = degrees + minutes / 60 + seconds / 3600
            if ref in ("S", "W"):
                decimal = -decimal
            return decimal
        except (IndexError, TypeError, ValueError):
            return None

    def reverse_geocode(self, lat: float, lon: float) -> str | None:
        try:
            from geopy.geocoders import Nominatim
            geolocator = Nominatim(user_agent="image_search")
            location = geolocator.reverse(f"{lat}, {lon}", exactly_one=True, language="en")
            if location:
                addr = location.raw.get("address", {})
                city = addr.get("city") or addr.get("town") or addr.get("village")
                country = addr.get("country")
                parts = [p for p in [city, country] if p]
                return ", ".join(parts) if parts else str(location.address)[:100]
        except Exception:
            pass
        return None
