from fastapi import APIRouter, Depends

from app.api.deps import get_search_service
from app.services.search_service import SearchService
from app.schemas.search import SearchRequest, SearchResponse

router = APIRouter()


@router.post("", response_model=SearchResponse)
def search_images(req: SearchRequest, svc: SearchService = Depends(get_search_service)):
    return svc.search(req.query, limit=req.limit)


@router.get("", response_model=SearchResponse)
def search_images_get(q: str, limit: int = 50, svc: SearchService = Depends(get_search_service)):
    return svc.search(q, limit=limit)
