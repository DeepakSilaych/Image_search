from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from uuid import UUID

import numpy as np
from PIL import Image

from app.config import get_settings

logger = logging.getLogger(__name__)


def _resize_for_detection(img_path: str, max_dim: int = 1024) -> str | None:
    img = Image.open(img_path)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    if max(img.size) <= max_dim:
        return None
    img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    img.save(tmp.name, "JPEG", quality=85)
    return tmp.name


def _cosine_distance(a, b) -> float:
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0.0 or nb == 0.0:
        return 1.0
    return float(1.0 - np.dot(a, b) / (na * nb))


def _is_valid_face_bbox(area: dict, img_w: int, img_h: int) -> bool:
    x, y = area.get("x", 0), area.get("y", 0)
    w, h = area.get("w", 0), area.get("h", 0)
    if w <= 0 or h <= 0:
        return False
    face_area = w * h
    img_area = img_w * img_h
    if img_area > 0 and face_area / img_area > 0.8:
        return False
    aspect = w / h if h > 0 else 0
    if aspect > 3.0 or aspect < 0.2:
        return False
    if w < 20 or h < 20:
        return False
    return True


class FacePipeline:
    def detect_faces(self, image_path: str) -> list[dict]:
        from deepface import DeepFace
        settings = get_settings()

        pil_img = Image.open(image_path)
        if pil_img.mode not in ("RGB", "L"):
            pil_img = pil_img.convert("RGB")
        img_w, img_h = pil_img.size

        tmp_path = _resize_for_detection(image_path)
        detect_path = tmp_path or image_path

        try:
            faces = DeepFace.extract_faces(
                img_path=detect_path,
                detector_backend=settings.face_detector,
                enforce_detection=False,
            )
        except Exception:
            if tmp_path:
                os.unlink(tmp_path)
            return []

        if tmp_path:
            scale_x = img_w / pil_img.size[0] if pil_img.size[0] > 0 else 1
            scale_y = img_h / pil_img.size[1] if pil_img.size[1] > 0 else 1
            resized = Image.open(tmp_path)
            scale_x = img_w / resized.size[0]
            scale_y = img_h / resized.size[1]
            resized.close()
        else:
            scale_x, scale_y = 1.0, 1.0

        results = []
        for face_obj in faces or []:
            confidence = face_obj.get("confidence", 0.0)
            if confidence < settings.face_min_confidence:
                continue

            area = face_obj.get("facial_area", {})
            scaled_area = {
                "x": int(area.get("x", 0) * scale_x),
                "y": int(area.get("y", 0) * scale_y),
                "w": int(area.get("w", 0) * scale_x),
                "h": int(area.get("h", 0) * scale_y),
            }

            if not _is_valid_face_bbox(scaled_area, img_w, img_h):
                continue

            try:
                emb_result = DeepFace.represent(
                    img_path=face_obj["face"],
                    model_name=settings.face_model,
                    enforce_detection=False,
                    detector_backend="skip",
                )
                embedding = emb_result[0]["embedding"]
            except Exception:
                continue

            results.append({
                "embedding": embedding,
                "bbox": scaled_area,
                "confidence": confidence,
                "face_img": face_obj.get("face"),
            })

        if tmp_path:
            os.unlink(tmp_path)
        return results

    def identify_face(self, embedding: list[float], known_embeddings: dict[str, list[list[float]]]) -> tuple[str | None, float]:
        settings = get_settings()
        best_name = None
        best_dist = settings.face_distance_threshold

        for name, embeddings in known_embeddings.items():
            for known_emb in embeddings:
                dist = _cosine_distance(known_emb, embedding)
                if dist < best_dist:
                    best_dist = dist
                    best_name = name

        return best_name, 1.0 - best_dist if best_name else 0.0

    def get_face_embedding(self, image_path: str) -> list[float] | None:
        from deepface import DeepFace
        settings = get_settings()
        try:
            result = DeepFace.represent(
                img_path=image_path,
                model_name=settings.face_model,
                detector_backend=settings.face_detector,
                enforce_detection=False,
            )
            return result[0]["embedding"] if result else None
        except Exception:
            return None

    def analyze_face(self, face_img) -> dict:
        from deepface import DeepFace
        try:
            analysis = DeepFace.analyze(
                img_path=face_img,
                actions=["emotion", "age", "gender"],
                enforce_detection=False,
                detector_backend="skip",
            )
            if analysis:
                a = analysis[0]
                return {
                    "emotion": a.get("dominant_emotion"),
                    "age": a.get("age"),
                    "gender": a.get("dominant_gender"),
                }
        except Exception:
            pass
        return {}
