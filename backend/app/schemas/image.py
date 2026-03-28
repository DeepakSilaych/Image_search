from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ImageBase(BaseModel):
    file_path: str


class ImageCreate(ImageBase):
    pass


class FaceOut(BaseModel):
    id: UUID
    person_name: str | None = None
    confidence: float | None = None
    emotion: str | None = None
    bbox: dict | None = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_face(cls, face) -> "FaceOut":
        bbox = None
        if face.bbox_x is not None:
            bbox = {"x": face.bbox_x, "y": face.bbox_y, "w": face.bbox_w, "h": face.bbox_h}
        return cls(
            id=face.id,
            person_name=face.person.name if face.person else None,
            confidence=face.confidence,
            emotion=face.emotion,
            bbox=bbox,
        )


class ObjectOut(BaseModel):
    id: UUID
    label: str
    confidence: float

    model_config = {"from_attributes": True}


class TagOut(BaseModel):
    id: UUID
    tag: str
    source: str
    confidence: float | None = None

    model_config = {"from_attributes": True}


class ImageOut(BaseModel):
    id: UUID
    file_path: str
    file_hash: str | None = None
    width: int | None = None
    height: int | None = None
    mime_type: str | None = None

    taken_at: datetime | None = None
    location_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    caption: str | None = None
    scene_type: str | None = None
    image_type: str | None = None
    ocr_text: str | None = None

    event_id: UUID | None = None
    is_favorite: bool = False
    quality_score: float | None = None
    processing_status: str = "pending"

    created_at: datetime
    processed_at: datetime | None = None

    faces: list[FaceOut] = []
    objects: list[ObjectOut] = []
    tags: list[TagOut] = []

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_image(cls, image) -> "ImageOut":
        return cls(
            id=image.id,
            file_path=image.file_path,
            file_hash=image.file_hash,
            width=image.width,
            height=image.height,
            mime_type=image.mime_type,
            taken_at=image.taken_at,
            location_name=image.location_name,
            latitude=image.latitude,
            longitude=image.longitude,
            caption=image.caption,
            scene_type=image.scene_type,
            image_type=image.image_type,
            ocr_text=image.ocr_text,
            event_id=image.event_id,
            is_favorite=image.is_favorite,
            quality_score=image.quality_score,
            processing_status=image.processing_status,
            created_at=image.created_at,
            processed_at=image.processed_at,
            faces=[FaceOut.from_face(f) for f in image.faces],
            objects=[ObjectOut.model_validate(o) for o in image.objects],
            tags=[TagOut.model_validate(t) for t in image.tags],
        )


class ImageListOut(BaseModel):
    items: list[ImageOut]
    total: int
    skip: int
    limit: int


class BulkIndexRequest(BaseModel):
    directory: str
    recursive: bool = True
    extensions: list[str] = [".jpg", ".jpeg", ".png", ".heic", ".webp"]


class BulkIndexResponse(BaseModel):
    queued: int
    skipped: int
    errors: list[str] = []


class ScanRequest(BaseModel):
    directory: str
    recursive: bool = True


class ScanResponse(BaseModel):
    registered: int
    skipped: int
    errors: int


class UploadResponse(BaseModel):
    image_id: UUID
    file_path: str
