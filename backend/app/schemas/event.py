from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EventCreate(BaseModel):
    name: str
    description: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    location_name: str | None = None


class EventOut(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    location_name: str | None = None
    auto_generated: bool
    image_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class EventListOut(BaseModel):
    items: list[EventOut]
    total: int
