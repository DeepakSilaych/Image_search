from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import Image
from app.search.retriever import RetrievalCandidate


WEIGHT_SEMANTIC = 0.45
WEIGHT_TEXT = 0.20
WEIGHT_FILTER = 0.30
WEIGHT_RECENCY = 0.05

MIN_FINAL_SCORE = 0.10


class Ranker:
    def rank(self, session: Session, candidates: list[RetrievalCandidate], limit: int = 50) -> list[RetrievalCandidate]:
        if not candidates:
            return []

        image_ids = [c.image_id for c in candidates]
        images = {
            img.id: img
            for img in session.query(Image).filter(Image.id.in_(image_ids)).all()
        }

        scored = []
        for c in candidates:
            img = images.get(c.image_id)
            if not img:
                continue

            semantic = c.vector_score
            text = min(c.text_score, 1.0)
            filter_s = min(c.filter_score, 1.0)
            recency = self._recency_score(img.taken_at)

            final = (
                WEIGHT_SEMANTIC * semantic
                + WEIGHT_TEXT * text
                + WEIGHT_FILTER * filter_s
                + WEIGHT_RECENCY * recency
            )

            if final < MIN_FINAL_SCORE and c.text_score == 0:
                continue

            c.vector_score = final
            scored.append(c)

        scored.sort(key=lambda c: c.vector_score, reverse=True)
        return scored[:limit]

    def _recency_score(self, taken_at: datetime | None) -> float:
        if not taken_at:
            return 0.0
        days = (datetime.utcnow() - taken_at).days
        if days < 7:
            return 1.0
        if days < 30:
            return 0.8
        if days < 365:
            return 0.5
        return 0.2
