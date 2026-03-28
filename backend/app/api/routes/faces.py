from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_face_service
from app.db.session import get_db
from app.db.models import ImageFace, Image, Person
from app.db.repo import Repository
from app.services.face_service import FaceService
from app.schemas.face import PersonCreate, PersonOut, PersonListOut, PersonFaceOut, AddReferenceRequest

router = APIRouter()


@router.get("/persons", response_model=PersonListOut)
def list_persons(
    filter: str = "all",
    svc: FaceService = Depends(get_face_service),
):
    if filter == "named":
        items = svc.list_named_persons()
    elif filter == "unknown":
        items = svc.list_unknown_persons()
    else:
        items = svc.list_persons()
    return PersonListOut(
        items=[PersonOut(**p) for p in items],
        total=len(items),
    )


@router.post("/persons", response_model=PersonOut)
def create_person(req: PersonCreate, svc: FaceService = Depends(get_face_service)):
    person = svc.create_person(req.name)
    return PersonOut(
        id=person.id,
        name=person.name,
        is_auto=person.is_auto,
        face_count=0,
        reference_count=0,
        created_at=person.created_at,
    )


@router.delete("/persons/{person_id}")
def delete_person(person_id: UUID, svc: FaceService = Depends(get_face_service)):
    if not svc.delete_person(person_id):
        raise HTTPException(404, "Person not found")
    return {"deleted": True}


@router.post("/persons/{person_id}/reference")
def add_reference(person_id: UUID, req: AddReferenceRequest, svc: FaceService = Depends(get_face_service)):
    ref = svc.add_reference(person_id, req.image_path)
    if not ref:
        raise HTTPException(400, "Could not extract face from image")
    return {"reference_id": ref.id}


@router.get("/persons/{person_id}/faces")
def get_person_faces(person_id: UUID, svc: FaceService = Depends(get_face_service)):
    faces = svc.get_person_faces(person_id)
    return {"items": [PersonFaceOut(**f) for f in faces], "total": len(faces)}


@router.post("/persons/{person_id}/rename")
def rename_person(person_id: UUID, body: dict, svc: FaceService = Depends(get_face_service)):
    name = body.get("name", "").strip()
    if not name:
        raise HTTPException(400, "Name is required")
    person = svc.rename_person(person_id, name)
    if not person:
        raise HTTPException(404, "Person not found")
    return {"id": str(person.id), "name": person.name}


@router.post("/cluster-unknown")
def cluster_unknown_faces(svc: FaceService = Depends(get_face_service)):
    count = svc.cluster_unassigned_faces()
    return {"clustered": count}


@router.get("/{face_id}/crop")
def get_face_crop(face_id: UUID, size: int = 128, db: Session = Depends(get_db)):
    from io import BytesIO
    from pathlib import Path
    from PIL import Image as PILImage
    from fastapi.responses import StreamingResponse

    face = Repository(db, ImageFace).get(face_id)
    if not face:
        raise HTTPException(404, "Face not found")

    image = Repository(db, Image).get(face.image_id)
    if not image:
        raise HTTPException(404, "Image not found")

    p = Path(image.file_path)
    if not p.exists():
        raise HTTPException(404, "File not found on disk")

    pil_img = PILImage.open(p)
    if pil_img.mode not in ("RGB", "L"):
        pil_img = pil_img.convert("RGB")

    if face.bbox_x is not None and face.bbox_w is not None:
        pad = int(face.bbox_w * 0.3)
        x1 = max(0, int(face.bbox_x) - pad)
        y1 = max(0, int(face.bbox_y) - pad)
        x2 = min(pil_img.width, int(face.bbox_x + face.bbox_w) + pad)
        y2 = min(pil_img.height, int(face.bbox_y + face.bbox_h) + pad)
        pil_img = pil_img.crop((x1, y1, x2, y2))

    pil_img.thumbnail((size, size), PILImage.Resampling.LANCZOS)
    buf = BytesIO()
    pil_img.save(buf, format="JPEG", quality=85)
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/jpeg")


@router.post("/{face_id}/name")
def name_face(face_id: UUID, body: dict, db: Session = Depends(get_db)):
    name = body.get("name", "").strip()
    if not name:
        raise HTTPException(400, "Name is required")

    face = Repository(db, ImageFace).get(face_id)
    if not face:
        raise HTTPException(404, "Face not found")

    old_person = Repository(db, Person).get(face.person_id) if face.person_id else None

    person_repo = Repository(db, Person)
    target_person = person_repo.get_by(name=name)

    if not target_person:
        if old_person and old_person.is_auto:
            old_person.name = name
            old_person.is_auto = False
            db.flush()
            target_person = old_person
        else:
            target_person = person_repo.create(name=name)
            db.flush()

    if old_person and old_person.is_auto and old_person.id != target_person.id:
        FaceService(db)._merge_persons(source=old_person, target=target_person)
    elif face.person_id != target_person.id:
        face.person_id = target_person.id
        db.flush()

    db.commit()

    return {
        "face_id": str(face_id),
        "person_id": str(target_person.id),
        "person_name": target_person.name,
    }
