from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import Image, ImageFace, ImageObject, ImageTag, Person, PersonReference
from app.db.repo import Repository
from app.db.session import SessionLocal
from app.vector.client import get_qdrant
from app.vector.store import (
    ensure_collections, upsert_image_vector, upsert_face_vector, search_similar_faces,
)
from app.pipeline.ingestion import compute_phash, extract_basic_metadata
from app.pipeline.understanding.embedding import CLIPEmbedder
from app.pipeline.understanding.face import FacePipeline
from app.pipeline.understanding.caption import CaptionPipeline
from app.pipeline.understanding.objects import ObjectDetectionPipeline
from app.pipeline.understanding.ocr import OCRPipeline
from app.pipeline.enrichment.temporal import TemporalExtractor
from app.pipeline.enrichment.location import LocationExtractor
from app.pipeline.enrichment.classification import ImageClassifier

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    def __init__(self):
        self._embedder: CLIPEmbedder | None = None
        self._face = FacePipeline()
        self._caption = CaptionPipeline()
        self._objects = ObjectDetectionPipeline()
        self._ocr = OCRPipeline()
        self._temporal = TemporalExtractor()
        self._location = LocationExtractor()
        self._classifier = ImageClassifier()
        self._parallelism = get_settings().pipeline_parallelism

    @property
    def embedder(self) -> CLIPEmbedder:
        if self._embedder is None:
            self._embedder = CLIPEmbedder.get()
        return self._embedder

    def process_image(self, session: Session, image_path: str) -> UUID | None:
        path = Path(image_path).resolve()
        if not path.exists():
            logger.error(f"File not found: {path}")
            return None

        image_repo = Repository(session, Image)
        existing = image_repo.get_by(file_path=str(path))
        if existing and existing.processing_status == "completed":
            return existing.id

        try:
            metadata = extract_basic_metadata(path)
            file_hash = compute_phash(path)
            metadata["file_hash"] = file_hash

            if existing:
                image = existing
                for k, v in metadata.items():
                    setattr(image, k, v)
                image.processing_status = "processing"
            else:
                image = image_repo.create(**metadata, processing_status="processing")

            session.flush()
            image_id = image.id

            results = self._run_parallel_steps(image_id, str(path))
            self._apply_results(session, image_id, results)

            image.processing_status = "completed"
            image.processed_at = datetime.utcnow()
            session.commit()

            return image_id

        except Exception as e:
            logger.exception(f"Pipeline failed for {path}: {e}")
            if existing:
                existing.processing_status = "failed"
                try:
                    session.commit()
                except Exception:
                    session.rollback()
            return None

    def _run_parallel_steps(self, image_id: UUID, image_path: str) -> dict:
        collected: dict = {}
        steps = {
            "clip": lambda: self._step_clip(image_path),
            "ocr": lambda: self._step_ocr(image_path),
            "caption": lambda: self._step_caption(image_path),
            "faces": lambda: self._step_faces(image_path),
            "objects": lambda: self._step_objects(image_path),
            "temporal": lambda: self._step_temporal(image_path),
            "location": lambda: self._step_location(image_path),
        }

        with ThreadPoolExecutor(max_workers=self._parallelism) as pool:
            futures = {pool.submit(fn): name for name, fn in steps.items()}
            for future in as_completed(futures):
                name = futures[future]
                try:
                    collected[name] = future.result()
                except Exception as e:
                    logger.warning(f"[{image_id}] {name} failed: {e}")
                    collected[name] = None

        return collected

    def _step_clip(self, image_path: str) -> list[float]:
        return self.embedder.encode_image(image_path)

    def _step_ocr(self, image_path: str) -> str | None:
        return self._ocr.extract(image_path)

    def _step_caption(self, image_path: str) -> dict | None:
        return self._caption.generate(image_path)

    def _step_faces(self, image_path: str) -> list[dict]:
        faces = self._face.detect_faces(image_path)
        for face_data in faces:
            if face_data.get("face_img") is not None:
                face_data["analysis"] = self._face.analyze_face(face_data["face_img"])
        return faces

    def _step_objects(self, image_path: str) -> list[dict]:
        return self._objects.detect(image_path)

    def _step_temporal(self, image_path: str) -> datetime | None:
        return self._temporal.extract_datetime(image_path)

    def _step_location(self, image_path: str) -> dict | None:
        gps = self._location.extract_gps(image_path)
        if not gps:
            return None
        location_name = self._location.reverse_geocode(gps["latitude"], gps["longitude"])
        return {"latitude": gps["latitude"], "longitude": gps["longitude"], "location_name": location_name}

    def _apply_results(self, session: Session, image_id: UUID, results: dict):
        qdrant = get_qdrant()
        ensure_collections(qdrant)
        image_repo = Repository(session, Image)

        clip_vec = results.get("clip")
        if clip_vec is not None:
            try:
                upsert_image_vector(qdrant, image_id, clip_vec)
            except Exception as e:
                logger.warning(f"[{image_id}] Vector upsert failed: {e}")

        ocr_text = results.get("ocr")
        if ocr_text is not None:
            image_repo.update(image_id, ocr_text=ocr_text)

        caption_data = results.get("caption")
        if caption_data:
            image_repo.update(
                image_id,
                caption=caption_data.get("caption"),
                caption_detailed=caption_data.get("caption_detailed"),
                scene_type=caption_data.get("scene_type"),
                image_type=caption_data.get("image_type"),
            )

        faces = results.get("faces")
        if faces:
            self._save_faces(session, image_id, faces)

        objects_data = results.get("objects")
        if objects_data:
            self._save_objects(session, image_id, objects_data)

        taken_at = results.get("temporal")
        if taken_at:
            image_repo.update(image_id, taken_at=taken_at)

        location = results.get("location")
        if location:
            image_repo.update(
                image_id,
                latitude=location["latitude"],
                longitude=location["longitude"],
                location_name=location.get("location_name"),
            )

    def _save_faces(self, session: Session, image_id: UUID, faces: list[dict]):
        qdrant = get_qdrant()
        known_embeddings = self._load_known_embeddings(session)
        face_repo = Repository(session, ImageFace)
        person_repo = Repository(session, Person)
        settings = get_settings()

        for face_data in faces:
            person_name, confidence = self._face.identify_face(
                face_data["embedding"], known_embeddings
            )

            person_id = None
            if person_name:
                person = person_repo.get_by(name=person_name)
                if person:
                    person_id = person.id

            if not person_id:
                person_id = self._find_or_create_cluster(
                    session, qdrant, face_data["embedding"], settings.face_distance_threshold
                )

            analysis = face_data.get("analysis", {})
            bbox = face_data.get("bbox", {})
            face_record = face_repo.create(
                image_id=image_id,
                person_id=person_id,
                bbox_x=bbox.get("x"),
                bbox_y=bbox.get("y"),
                bbox_w=bbox.get("w"),
                bbox_h=bbox.get("h"),
                confidence=face_data.get("confidence"),
                emotion=analysis.get("emotion"),
                age_estimate=analysis.get("age"),
                gender_estimate=analysis.get("gender"),
            )

            upsert_face_vector(qdrant, face_record.id, face_data["embedding"], person_id)

    def _find_or_create_cluster(
        self, session: Session, qdrant, embedding: list[float], threshold: float
    ) -> UUID:
        similar = search_similar_faces(qdrant, embedding, limit=5)
        for hit in similar:
            pid = hit.payload.get("person_id") if hit.payload else None
            if not pid:
                continue
            score = hit.score
            distance = 1.0 - score
            if distance < threshold:
                person = Repository(session, Person).get(UUID(pid))
                if person:
                    return person.id

        auto_count = session.query(Person).filter(Person.is_auto == True).count()
        new_name = f"Unknown #{auto_count + 1}"
        while Repository(session, Person).get_by(name=new_name):
            auto_count += 1
            new_name = f"Unknown #{auto_count + 1}"

        person = Repository(session, Person).create(name=new_name, is_auto=True)
        session.flush()
        return person.id

    def _save_objects(self, session: Session, image_id: UUID, detections: list[dict]):
        obj_repo = Repository(session, ImageObject)
        for det in detections:
            bbox = det.get("bbox", {})
            obj_repo.create(
                image_id=image_id,
                label=det["label"],
                confidence=det["confidence"],
                bbox_x=bbox.get("x"),
                bbox_y=bbox.get("y"),
                bbox_w=bbox.get("w"),
                bbox_h=bbox.get("h"),
            )

    def reprocess_faces(self, session: Session, image_id: UUID, image_path: str):
        qdrant = get_qdrant()
        ensure_collections(qdrant)
        faces = self._step_faces(image_path)
        if faces:
            self._save_faces(session, image_id, faces)

    def _load_known_embeddings(self, session: Session) -> dict[str, list[list[float]]]:
        refs = session.query(PersonReference).join(Person).all()
        result: dict[str, list[list[float]]] = {}
        for ref in refs:
            name = ref.person.name
            if ref.embedding:
                result.setdefault(name, []).append(ref.embedding)
        return result


_orchestrator: PipelineOrchestrator | None = None


def get_orchestrator() -> PipelineOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = PipelineOrchestrator()
    return _orchestrator
