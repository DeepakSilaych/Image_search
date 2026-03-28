from __future__ import annotations

from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Person, PersonReference, ImageFace
from app.db.repo import Repository
from app.pipeline.understanding.face import FacePipeline
from app.vector.client import get_qdrant
from app.vector.store import upsert_face_vector


class FaceService:
    def __init__(self, session: Session):
        self._session = session
        self._person_repo = Repository(session, Person)
        self._ref_repo = Repository(session, PersonReference)

    def create_person(self, name: str) -> Person:
        existing = self._person_repo.get_by(name=name)
        if existing:
            return existing
        person = self._person_repo.create(name=name)
        self._person_repo.commit()
        return person

    def list_persons(self, include_auto: bool = True) -> list[dict]:
        q = self._session.query(Person)
        if not include_auto:
            q = q.filter(Person.is_auto == False)
        persons = q.order_by(Person.name).all()
        return self._enrich_persons(persons)

    def list_unknown_persons(self) -> list[dict]:
        persons = self._session.query(Person).filter(
            Person.is_auto == True
        ).order_by(Person.created_at.desc()).all()
        return self._enrich_persons(persons)

    def list_named_persons(self) -> list[dict]:
        persons = self._session.query(Person).filter(
            Person.is_auto == False
        ).order_by(Person.name).all()
        return self._enrich_persons(persons)

    def _enrich_persons(self, persons: list) -> list[dict]:
        result = []
        for p in persons:
            face_count = self._session.query(func.count(ImageFace.id)).filter(
                ImageFace.person_id == p.id
            ).scalar()
            ref_count = self._session.query(func.count(PersonReference.id)).filter(
                PersonReference.person_id == p.id
            ).scalar()

            representative_face = self._session.query(ImageFace).filter(
                ImageFace.person_id == p.id
            ).first()

            result.append({
                "id": p.id,
                "name": p.name,
                "is_auto": p.is_auto,
                "face_count": face_count,
                "reference_count": ref_count,
                "representative_face_id": representative_face.id if representative_face else None,
                "created_at": p.created_at,
            })
        return result

    def get_person_faces(self, person_id: UUID) -> list[dict]:
        faces = self._session.query(ImageFace).filter(
            ImageFace.person_id == person_id
        ).all()
        return [
            {
                "id": f.id,
                "image_id": f.image_id,
                "confidence": f.confidence,
                "emotion": f.emotion,
            }
            for f in faces
        ]

    def rename_person(self, person_id: UUID, new_name: str) -> Person | None:
        person = self._person_repo.get(person_id)
        if not person:
            return None

        existing = self._person_repo.get_by(name=new_name)
        if existing and existing.id != person_id:
            self._merge_persons(source=person, target=existing)
            return existing

        person.name = new_name
        person.is_auto = False
        self._session.flush()
        self._session.commit()
        return person

    def _merge_persons(self, source: Person, target: Person):
        self._session.query(ImageFace).filter(
            ImageFace.person_id == source.id
        ).update({ImageFace.person_id: target.id})

        self._session.query(PersonReference).filter(
            PersonReference.person_id == source.id
        ).update({PersonReference.person_id: target.id})

        qdrant = get_qdrant()
        faces = self._session.query(ImageFace).filter(
            ImageFace.person_id == target.id
        ).all()
        for face in faces:
            from app.vector.store import get_face_vector
            vec = get_face_vector(qdrant, face.id)
            if vec:
                upsert_face_vector(qdrant, face.id, vec, target.id)

        self._session.delete(source)
        self._session.flush()
        self._session.commit()

    def add_reference(self, person_id: UUID, image_path: str) -> PersonReference | None:
        person = self._person_repo.get(person_id)
        if not person:
            return None

        face_pipeline = FacePipeline()
        embedding = face_pipeline.get_face_embedding(image_path)
        if not embedding:
            return None

        ref = self._ref_repo.create(
            person_id=person_id,
            image_path=image_path,
            embedding=embedding,
        )
        self._ref_repo.commit()

        upsert_face_vector(get_qdrant(), ref.id, embedding, person_id)
        return ref

    def cluster_unassigned_faces(self) -> int:
        from app.config import get_settings
        from app.vector.store import search_similar_faces, get_face_vector

        unassigned = self._session.query(ImageFace).filter(
            ImageFace.person_id == None
        ).all()

        if not unassigned:
            return 0

        settings = get_settings()
        qdrant = get_qdrant()
        clustered = 0

        for face in unassigned:
            embedding = get_face_vector(qdrant, face.id)
            if not embedding:
                continue

            similar = search_similar_faces(qdrant, embedding, limit=10)
            matched_person_id = None

            for hit in similar:
                if str(hit.id) == str(face.id):
                    continue
                pid = hit.payload.get("person_id") if hit.payload else None
                if not pid:
                    continue
                distance = 1.0 - hit.score
                if distance < settings.face_distance_threshold:
                    person = self._person_repo.get(UUID(pid))
                    if person:
                        matched_person_id = person.id
                        break

            if not matched_person_id:
                auto_count = self._session.query(Person).filter(Person.is_auto == True).count()
                new_name = f"Unknown #{auto_count + 1}"
                while self._person_repo.get_by(name=new_name):
                    auto_count += 1
                    new_name = f"Unknown #{auto_count + 1}"
                person = self._person_repo.create(name=new_name, is_auto=True)
                self._session.flush()
                matched_person_id = person.id

            face.person_id = matched_person_id
            upsert_face_vector(qdrant, face.id, embedding, matched_person_id)
            clustered += 1

        self._session.commit()
        return clustered

    def delete_person(self, person_id: UUID) -> bool:
        self._session.query(ImageFace).filter(
            ImageFace.person_id == person_id
        ).update({ImageFace.person_id: None})
        self._ref_repo.delete_many(person_id=person_id)
        success = self._person_repo.delete(person_id)
        if success:
            self._person_repo.commit()
        return success
