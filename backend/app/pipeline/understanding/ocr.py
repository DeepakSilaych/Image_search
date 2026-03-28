from __future__ import annotations

import os
import tempfile
from pathlib import Path

from PIL import Image


class OCRPipeline:
    def extract(self, image_path: str | Path) -> str:
        try:
            import pytesseract
            img = Image.open(image_path)
            if max(img.size) > 2048:
                img.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
            text = pytesseract.image_to_string(img)
            return " ".join(text.split())
        except ImportError:
            return self._fallback_ocrmac(str(image_path))
        except Exception:
            return ""

    def _fallback_ocrmac(self, image_path: str) -> str:
        try:
            from ocrmac.ocrmac import OCR as OCRMac
            img = Image.open(image_path)
            if max(img.size) > 1024:
                img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                    img.save(tmp.name, "JPEG", quality=85)
                    annotations = OCRMac(tmp.name).recognize()
                os.unlink(tmp.name)
            else:
                annotations = OCRMac(image_path).recognize()
            parts = [str(item[0]) for item in (annotations or []) if item and item[0]]
            return " ".join(" ".join(parts).split())
        except Exception:
            return ""
