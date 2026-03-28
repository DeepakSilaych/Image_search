from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.models import Image, Event


TIME_GAP_HOURS = 4
MIN_CLUSTER_SIZE = 3


class EventDetector:
    def detect_events(self, session: Session) -> list[UUID]:
        images = session.execute(
            select(Image)
            .where(Image.taken_at.isnot(None), Image.event_id.is_(None))
            .order_by(Image.taken_at.asc())
        ).scalars().all()

        if not images:
            return []

        clusters: list[list[Image]] = []
        current_cluster: list[Image] = [images[0]]

        for img in images[1:]:
            prev_time = current_cluster[-1].taken_at
            if img.taken_at and prev_time and (img.taken_at - prev_time) < timedelta(hours=TIME_GAP_HOURS):
                if img.location_name and current_cluster[0].location_name:
                    if img.location_name == current_cluster[0].location_name:
                        current_cluster.append(img)
                        continue
                current_cluster.append(img)
            else:
                if len(current_cluster) >= MIN_CLUSTER_SIZE:
                    clusters.append(current_cluster)
                current_cluster = [img]

        if len(current_cluster) >= MIN_CLUSTER_SIZE:
            clusters.append(current_cluster)

        created_events = []
        for cluster in clusters:
            event = self._create_event_from_cluster(session, cluster)
            created_events.append(event.id)

        session.commit()
        return created_events

    def _create_event_from_cluster(self, session: Session, images: list[Image]) -> Event:
        start = images[0].taken_at
        end = images[-1].taken_at
        location = next((i.location_name for i in images if i.location_name), None)

        name = self._generate_event_name(start, location, images)

        event = Event(
            name=name,
            start_date=start,
            end_date=end,
            location_name=location,
            auto_generated=True,
        )
        session.add(event)
        session.flush()

        for img in images:
            img.event_id = event.id

        return event

    def _generate_event_name(self, start: datetime | None, location: str | None, images: list[Image]) -> str:
        parts = []
        if location:
            parts.append(location)
        if start:
            parts.append(start.strftime("%B %Y"))
        if not parts:
            parts.append(f"Event ({len(images)} photos)")
        return " - ".join(parts)
