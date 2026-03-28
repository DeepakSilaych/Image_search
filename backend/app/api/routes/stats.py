from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.db.models import Image, Person, Event, ImageFace, ImageObject
from app.vector.client import get_qdrant
from app.vector.store import get_collection_info, COLLECTION_IMAGES, COLLECTION_FACES

router = APIRouter()


@router.get("")
def get_stats(db: Session = Depends(get_db)):
    total_images = db.query(func.count(Image.id)).scalar()
    processed = db.query(func.count(Image.id)).filter(Image.processing_status == "completed").scalar()
    pending = db.query(func.count(Image.id)).filter(Image.processing_status == "pending").scalar()
    failed = db.query(func.count(Image.id)).filter(Image.processing_status == "failed").scalar()
    total_persons = db.query(func.count(Person.id)).scalar()
    total_events = db.query(func.count(Event.id)).scalar()
    total_faces = db.query(func.count(ImageFace.id)).scalar()
    total_objects = db.query(func.count(ImageObject.id)).scalar()

    scene_dist = dict(
        db.query(Image.scene_type, func.count(Image.id))
        .filter(Image.scene_type.isnot(None))
        .group_by(Image.scene_type)
        .all()
    )

    type_dist = dict(
        db.query(Image.image_type, func.count(Image.id))
        .filter(Image.image_type.isnot(None))
        .group_by(Image.image_type)
        .all()
    )

    qdrant = get_qdrant()
    img_collection = get_collection_info(qdrant, COLLECTION_IMAGES)
    face_collection = get_collection_info(qdrant, COLLECTION_FACES)

    from app.services.worker import is_worker_running
    processing = db.query(func.count(Image.id)).filter(Image.processing_status == "processing").scalar()

    return {
        "images": {
            "total": total_images,
            "processed": processed,
            "pending": pending,
            "processing": processing,
            "failed": failed,
        },
        "persons": total_persons,
        "events": total_events,
        "faces_detected": total_faces,
        "objects_detected": total_objects,
        "scene_distribution": scene_dist,
        "type_distribution": type_dist,
        "vectors": {
            "images": img_collection.points_count if img_collection else 0,
            "faces": face_collection.points_count if face_collection else 0,
        },
        "worker_running": is_worker_running(),
    }
