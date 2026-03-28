import uuid
from datetime import datetime

from sqlalchemy import (
    String, Text, Float, Integer, Boolean, DateTime, ForeignKey, BigInteger, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def _uuid():
    return uuid.uuid4()


class Image(Base):
    __tablename__ = "images"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    file_path: Mapped[str] = mapped_column(Text, unique=True, index=True)
    file_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger)
    mime_type: Mapped[str | None] = mapped_column(String(50))
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)

    taken_at: Mapped[datetime | None] = mapped_column(DateTime)
    camera_make: Mapped[str | None] = mapped_column(String(100))
    camera_model: Mapped[str | None] = mapped_column(String(100))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    location_name: Mapped[str | None] = mapped_column(String(255))

    caption: Mapped[str | None] = mapped_column(Text)
    caption_detailed: Mapped[str | None] = mapped_column(Text)
    scene_type: Mapped[str | None] = mapped_column(String(100))
    image_type: Mapped[str | None] = mapped_column(String(50))
    ocr_text: Mapped[str | None] = mapped_column(Text)
    dominant_colors: Mapped[dict | None] = mapped_column(JSONB)

    event_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("events.id"))
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    quality_score: Mapped[float | None] = mapped_column(Float)

    processing_status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime)

    faces: Mapped[list["ImageFace"]] = relationship(back_populates="image", cascade="all, delete-orphan")
    objects: Mapped[list["ImageObject"]] = relationship(back_populates="image", cascade="all, delete-orphan")
    tags: Mapped[list["ImageTag"]] = relationship(back_populates="image", cascade="all, delete-orphan")
    event: Mapped["Event | None"] = relationship(back_populates="images")

    __table_args__ = (
        Index("ix_images_taken_at", "taken_at"),
        Index("ix_images_scene_type", "scene_type"),
        Index("ix_images_image_type", "image_type"),
        Index("ix_images_location", "latitude", "longitude"),
    )


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    is_auto: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    references: Mapped[list["PersonReference"]] = relationship(back_populates="person", cascade="all, delete-orphan")
    faces: Mapped[list["ImageFace"]] = relationship(back_populates="person")


class PersonReference(Base):
    __tablename__ = "person_references"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    person_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"))
    image_path: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list | None] = mapped_column(JSONB)

    person: Mapped["Person"] = relationship(back_populates="references")


class ImageFace(Base):
    __tablename__ = "image_faces"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    image_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("images.id", ondelete="CASCADE"), index=True)
    person_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("persons.id", ondelete="SET NULL"), index=True)

    bbox_x: Mapped[float | None] = mapped_column(Float)
    bbox_y: Mapped[float | None] = mapped_column(Float)
    bbox_w: Mapped[float | None] = mapped_column(Float)
    bbox_h: Mapped[float | None] = mapped_column(Float)
    confidence: Mapped[float | None] = mapped_column(Float)

    emotion: Mapped[str | None] = mapped_column(String(50))
    age_estimate: Mapped[int | None] = mapped_column(Integer)
    gender_estimate: Mapped[str | None] = mapped_column(String(20))

    image: Mapped["Image"] = relationship(back_populates="faces")
    person: Mapped["Person | None"] = relationship(back_populates="faces")


class ImageObject(Base):
    __tablename__ = "image_objects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    image_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("images.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(100), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    bbox_x: Mapped[float | None] = mapped_column(Float)
    bbox_y: Mapped[float | None] = mapped_column(Float)
    bbox_w: Mapped[float | None] = mapped_column(Float)
    bbox_h: Mapped[float | None] = mapped_column(Float)

    image: Mapped["Image"] = relationship(back_populates="objects")


class ImageTag(Base):
    __tablename__ = "image_tags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    image_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("images.id", ondelete="CASCADE"), index=True)
    tag: Mapped[str] = mapped_column(String(100), index=True)
    source: Mapped[str] = mapped_column(String(20), default="auto")
    confidence: Mapped[float | None] = mapped_column(Float)

    image: Mapped["Image"] = relationship(back_populates="tags")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    start_date: Mapped[datetime | None] = mapped_column(DateTime)
    end_date: Mapped[datetime | None] = mapped_column(DateTime)
    location_name: Mapped[str | None] = mapped_column(String(255))
    auto_generated: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    images: Mapped[list["Image"]] = relationship(back_populates="event")


class PersonRelationship(Base):
    __tablename__ = "person_relationships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    person_a_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), index=True)
    person_b_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), index=True)
    relationship_type: Mapped[str | None] = mapped_column(String(50))
    co_occurrence_count: Mapped[int] = mapped_column(Integer, default=0)

    person_a: Mapped["Person"] = relationship(foreign_keys=[person_a_id])
    person_b: Mapped["Person"] = relationship(foreign_keys=[person_b_id])

    __table_args__ = (
        Index("ix_person_rel_pair", "person_a_id", "person_b_id", unique=True),
    )
