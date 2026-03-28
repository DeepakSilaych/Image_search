from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PersonCreate(BaseModel):
    name: str


class PersonOut(BaseModel):
    id: UUID
    name: str
    is_auto: bool = False
    face_count: int = 0
    reference_count: int = 0
    representative_face_id: UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PersonListOut(BaseModel):
    items: list[PersonOut]
    total: int


class PersonFaceOut(BaseModel):
    id: UUID
    image_id: UUID
    confidence: float | None = None
    emotion: str | None = None


class AddReferenceRequest(BaseModel):
    person_id: UUID
    image_path: str
