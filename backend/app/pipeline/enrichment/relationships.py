from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Image, ImageFace, PersonRelationship


class RelationshipBuilder:
    def update_co_occurrences(self, session: Session):
        images_with_faces = session.execute(
            select(ImageFace.image_id, ImageFace.person_id)
            .where(ImageFace.person_id.isnot(None))
        ).all()

        image_people: dict[UUID, set[UUID]] = defaultdict(set)
        for image_id, person_id in images_with_faces:
            image_people[image_id].add(person_id)

        pair_counts: dict[tuple[UUID, UUID], int] = defaultdict(int)
        for people in image_people.values():
            people_list = sorted(people)
            for i in range(len(people_list)):
                for j in range(i + 1, len(people_list)):
                    pair_counts[(people_list[i], people_list[j])] += 1

        for (a_id, b_id), count in pair_counts.items():
            existing = session.execute(
                select(PersonRelationship).where(
                    PersonRelationship.person_a_id == a_id,
                    PersonRelationship.person_b_id == b_id,
                )
            ).scalar_one_or_none()

            if existing:
                existing.co_occurrence_count = count
            else:
                session.add(PersonRelationship(
                    person_a_id=a_id,
                    person_b_id=b_id,
                    co_occurrence_count=count,
                ))

        session.commit()
