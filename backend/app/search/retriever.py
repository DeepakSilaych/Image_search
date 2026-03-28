from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import select, extract, func, or_
from sqlalchemy.orm import Session

from app.db.models import Image, ImageFace, ImageObject, Person
from app.vector.client import get_qdrant
from app.vector.store import search_similar_images
from app.pipeline.understanding.embedding import CLIPEmbedder
from app.search.query_parser import ParsedQuery

MIN_VECTOR_SCORE = 0.18
TEXT_MATCH_BOOST = 0.5


@dataclass
class RetrievalCandidate:
    image_id: UUID
    vector_score: float = 0.0
    text_score: float = 0.0
    filter_score: float = 0.0
    match_reasons: list[str] = field(default_factory=list)


class HybridRetriever:
    def retrieve(self, session: Session, parsed: ParsedQuery, limit: int = 200) -> list[RetrievalCandidate]:
        vector_candidates = self._vector_search(parsed, limit)
        text_candidates = self._text_search(session, parsed)

        merged: dict[UUID, RetrievalCandidate] = {}

        for img_id, score in vector_candidates.items():
            if score < MIN_VECTOR_SCORE:
                continue
            merged[img_id] = RetrievalCandidate(image_id=img_id, vector_score=score)

        for img_id, (score, reasons) in text_candidates.items():
            if img_id in merged:
                merged[img_id].text_score = score
                merged[img_id].match_reasons.extend(reasons)
            else:
                c = RetrievalCandidate(image_id=img_id, text_score=score)
                c.match_reasons.extend(reasons)
                merged[img_id] = c

        candidates = list(merged.values())
        self._apply_structured_filters(session, parsed, candidates)

        return candidates[:limit]

    def _vector_search(self, parsed: ParsedQuery, limit: int) -> dict[UUID, float]:
        embedder = CLIPEmbedder.get()
        query_vector = embedder.encode_text(parsed.semantic_text)
        qdrant = get_qdrant()
        results = search_similar_images(qdrant, query_vector, limit=limit)
        return {UUID(hit.id): hit.score for hit in results}

    def _text_search(self, session: Session, parsed: ParsedQuery) -> dict[UUID, tuple[float, list[str]]]:
        query = parsed.original.strip()
        if not query:
            return {}

        person_names_lower = {p.lower() for p in parsed.persons}
        terms = [
            t.strip() for t in query.lower().split()
            if len(t.strip()) >= 2 and t.strip() not in person_names_lower
        ]
        if not terms:
            return {}

        results: dict[UUID, tuple[float, list[str]]] = {}

        for term in terms:
            pattern = f"%{term}%"
            matches = session.execute(
                select(Image.id, Image.caption, Image.ocr_text).where(
                    Image.processing_status == "completed"
                ).where(
                    or_(
                        func.lower(Image.caption).like(pattern),
                        func.lower(Image.ocr_text).like(pattern),
                        func.lower(Image.caption_detailed).like(pattern),
                    )
                ).limit(200)
            ).all()

            for img_id, caption, ocr_text in matches:
                score = 0.0
                reasons = []
                cap_lower = (caption or "").lower()
                ocr_lower = (ocr_text or "").lower()

                if term in cap_lower:
                    score += TEXT_MATCH_BOOST
                    reasons.append(f"caption contains '{term}'")
                if term in ocr_lower:
                    score += TEXT_MATCH_BOOST * 0.8
                    reasons.append(f"OCR contains '{term}'")

                if img_id in results:
                    old_score, old_reasons = results[img_id]
                    results[img_id] = (old_score + score, old_reasons + reasons)
                else:
                    results[img_id] = (score, reasons)

        obj_pattern = f"%{query.lower()}%"
        obj_matches = session.execute(
            select(ImageObject.image_id, ImageObject.label).where(
                func.lower(ImageObject.label).like(obj_pattern)
            ).limit(200)
        ).all()
        for img_id, label in obj_matches:
            score = TEXT_MATCH_BOOST * 0.6
            reasons = [f"object: {label}"]
            if img_id in results:
                old_score, old_reasons = results[img_id]
                results[img_id] = (old_score + score, old_reasons + reasons)
            else:
                results[img_id] = (score, reasons)

        return results

    def _apply_structured_filters(
        self, session: Session, parsed: ParsedQuery, candidates: list[RetrievalCandidate]
    ):
        if not candidates:
            return

        image_ids = [c.image_id for c in candidates]
        images = {
            img.id: img
            for img in session.execute(
                select(Image).where(Image.id.in_(image_ids))
            ).scalars().all()
        }

        person_image_ids: set[UUID] = set()
        if parsed.persons:
            person_names = [p.lower() for p in parsed.persons]
            face_q = (
                select(ImageFace.image_id)
                .join(Person)
                .where(func.lower(Person.name).in_(person_names))
                .where(ImageFace.image_id.in_(image_ids))
            )
            person_image_ids = {row[0] for row in session.execute(face_q).all()}

        to_remove = []
        for c in candidates:
            img = images.get(c.image_id)
            if not img:
                to_remove.append(c)
                continue

            if parsed.persons:
                if c.image_id in person_image_ids:
                    c.filter_score += 1.0
                    c.match_reasons.append("person match")
                else:
                    to_remove.append(c)
                    continue

            if parsed.year and img.taken_at and img.taken_at.year == parsed.year:
                c.filter_score += 0.2
                c.match_reasons.append(f"year={parsed.year}")

            if parsed.scenes and img.scene_type in parsed.scenes:
                c.filter_score += 0.2
                c.match_reasons.append(f"scene={img.scene_type}")

        for c in to_remove:
            candidates.remove(c)
