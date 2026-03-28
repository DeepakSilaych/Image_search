from sqlalchemy.orm import Session
from fastapi import Depends

from app.db.session import get_db
from app.services.image_service import ImageService
from app.services.search_service import SearchService
from app.services.face_service import FaceService


def get_image_service(db: Session = Depends(get_db)) -> ImageService:
    return ImageService(db)


def get_search_service(db: Session = Depends(get_db)) -> SearchService:
    return SearchService(db)


def get_face_service(db: Session = Depends(get_db)) -> FaceService:
    return FaceService(db)
