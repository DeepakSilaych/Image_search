from uuid import UUID

from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    limit: int = 50
    filters: dict | None = None


class SearchHit(BaseModel):
    image_id: UUID
    file_path: str
    score: float
    caption: str | None = None
    scene_type: str | None = None
    faces: list[str] = []
    match_reasons: list[str] = []


class SearchResponse(BaseModel):
    query: str
    hits: list[SearchHit]
    total: int
    parsed_query: dict | None = None
