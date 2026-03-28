from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import Image, Person
from app.db.repo import Repository
from app.search.query_parser import QueryParser, ParsedQuery
from app.search.retriever import HybridRetriever
from app.search.ranker import Ranker
from app.schemas.search import SearchHit, SearchResponse


class SearchService:
    def __init__(self, session: Session):
        self._session = session

    def search(self, query: str, limit: int = 50) -> SearchResponse:
        known_names = {
            p.name for p in Repository(self._session, Person).list(limit=1000)
        }
        parser = QueryParser(known_persons=known_names)
        parsed = parser.parse(query)

        retriever = HybridRetriever()
        candidates = retriever.retrieve(self._session, parsed, limit=limit * 4)

        ranker = Ranker()
        ranked = ranker.rank(self._session, candidates, limit=limit)

        image_ids = [c.image_id for c in ranked]
        images = {
            img.id: img
            for img in self._session.query(Image).filter(Image.id.in_(image_ids)).all()
        }

        hits = []
        for c in ranked:
            img = images.get(c.image_id)
            if not img:
                continue
            face_names = [f.person.name for f in img.faces if f.person]
            hits.append(SearchHit(
                image_id=img.id,
                file_path=img.file_path,
                score=round(c.vector_score, 4),
                caption=img.caption,
                scene_type=img.scene_type,
                faces=face_names,
                match_reasons=c.match_reasons,
            ))

        return SearchResponse(
            query=query,
            hits=hits,
            total=len(hits),
            parsed_query=parsed.to_dict(),
        )
