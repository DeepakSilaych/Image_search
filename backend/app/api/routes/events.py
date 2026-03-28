from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Event, Image
from app.db.repo import Repository
from app.schemas.event import EventCreate, EventOut, EventListOut
from app.pipeline.enrichment.events import EventDetector

router = APIRouter()


@router.get("", response_model=EventListOut)
def list_events(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    repo = Repository(db, Event)
    events = repo.list(skip=skip, limit=limit, order_by="-start_date")
    total = repo.count()

    items = []
    for e in events:
        img_count = Repository(db, Image).count(event_id=e.id)
        items.append(EventOut(
            id=e.id,
            name=e.name,
            description=e.description,
            start_date=e.start_date,
            end_date=e.end_date,
            location_name=e.location_name,
            auto_generated=e.auto_generated,
            image_count=img_count,
            created_at=e.created_at,
        ))

    return EventListOut(items=items, total=total)


@router.post("", response_model=EventOut)
def create_event(req: EventCreate, db: Session = Depends(get_db)):
    repo = Repository(db, Event)
    event = repo.create(
        name=req.name,
        description=req.description,
        start_date=req.start_date,
        end_date=req.end_date,
        location_name=req.location_name,
        auto_generated=False,
    )
    repo.commit()
    return EventOut(
        id=event.id,
        name=event.name,
        description=event.description,
        start_date=event.start_date,
        end_date=event.end_date,
        location_name=event.location_name,
        auto_generated=event.auto_generated,
        image_count=0,
        created_at=event.created_at,
    )


@router.post("/detect")
def detect_events(db: Session = Depends(get_db)):
    detector = EventDetector()
    event_ids = detector.detect_events(db)
    return {"detected_events": len(event_ids), "event_ids": event_ids}


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: UUID, db: Session = Depends(get_db)):
    repo = Repository(db, Event)
    event = repo.get(event_id)
    if not event:
        raise HTTPException(404, "Event not found")
    img_count = Repository(db, Image).count(event_id=event.id)
    return EventOut(
        id=event.id,
        name=event.name,
        description=event.description,
        start_date=event.start_date,
        end_date=event.end_date,
        location_name=event.location_name,
        auto_generated=event.auto_generated,
        image_count=img_count,
        created_at=event.created_at,
    )


@router.delete("/{event_id}")
def delete_event(event_id: UUID, db: Session = Depends(get_db)):
    repo = Repository(db, Event)
    for img in Repository(db, Image).list(limit=10000, event_id=event_id):
        img.event_id = None
    if not repo.delete(event_id):
        raise HTTPException(404, "Event not found")
    repo.commit()
    return {"deleted": True}
