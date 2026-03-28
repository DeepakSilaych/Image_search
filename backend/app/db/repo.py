from __future__ import annotations

from typing import TypeVar, Generic, Type, Any
from uuid import UUID

from sqlalchemy import select, func, delete as sa_delete
from sqlalchemy.orm import Session

from app.db.session import Base

T = TypeVar("T", bound=Base)


class Repository(Generic[T]):
    def __init__(self, session: Session, model: Type[T]):
        self._session = session
        self._model = model

    def get(self, id: UUID) -> T | None:
        return self._session.get(self._model, id)

    def get_by(self, **filters: Any) -> T | None:
        q = select(self._model)
        for k, v in filters.items():
            q = q.where(getattr(self._model, k) == v)
        return self._session.execute(q).scalar_one_or_none()

    def list(self, skip: int = 0, limit: int = 100, order_by: str | None = None, **filters: Any) -> list[T]:
        q = select(self._model)
        for k, v in filters.items():
            col = getattr(self._model, k)
            if isinstance(v, list):
                q = q.where(col.in_(v))
            else:
                q = q.where(col == v)
        if order_by:
            desc = order_by.startswith("-")
            col = getattr(self._model, order_by.lstrip("-"))
            q = q.order_by(col.desc() if desc else col.asc())
        return list(self._session.execute(q.offset(skip).limit(limit)).scalars().all())

    def count(self, **filters: Any) -> int:
        q = select(func.count()).select_from(self._model)
        for k, v in filters.items():
            q = q.where(getattr(self._model, k) == v)
        return self._session.execute(q).scalar_one()

    def create(self, **data: Any) -> T:
        obj = self._model(**data)
        self._session.add(obj)
        self._session.flush()
        self._session.refresh(obj)
        return obj

    def create_many(self, items: list[dict]) -> list[T]:
        objects = [self._model(**d) for d in items]
        self._session.add_all(objects)
        self._session.flush()
        for obj in objects:
            self._session.refresh(obj)
        return objects

    def update(self, id: UUID, **data: Any) -> T | None:
        obj = self.get(id)
        if not obj:
            return None
        for k, v in data.items():
            setattr(obj, k, v)
        self._session.flush()
        self._session.refresh(obj)
        return obj

    def delete(self, id: UUID) -> bool:
        obj = self.get(id)
        if not obj:
            return False
        self._session.delete(obj)
        self._session.flush()
        return True

    def delete_many(self, **filters: Any) -> int:
        q = sa_delete(self._model)
        for k, v in filters.items():
            q = q.where(getattr(self._model, k) == v)
        result = self._session.execute(q)
        self._session.flush()
        return result.rowcount

    def commit(self):
        self._session.commit()

    def rollback(self):
        self._session.rollback()
