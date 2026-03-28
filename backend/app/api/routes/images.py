from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse

from app.api.deps import get_image_service
from app.services.image_service import ImageService
from app.schemas.image import (
    ImageOut, BulkIndexRequest, BulkIndexResponse,
    ScanRequest, ScanResponse, UploadResponse,
)

router = APIRouter()


@router.get("")
def list_images(
    skip: int = 0,
    limit: int = 50,
    status: str | None = None,
    scene: str | None = None,
    favorite: bool | None = None,
    svc: ImageService = Depends(get_image_service),
):
    filters = {}
    if status:
        filters["processing_status"] = status
    if scene:
        filters["scene_type"] = scene
    if favorite is not None:
        filters["is_favorite"] = favorite
    items, total = svc.list_images(skip=skip, limit=limit, **filters)
    return {
        "items": [ImageOut.from_orm_image(i) for i in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/browse")
def browse_filesystem(path: str = "/"):
    from pathlib import Path as P
    target = P(path).expanduser().resolve()
    if not target.is_dir():
        raise HTTPException(400, "Not a directory")
    dirs = []
    try:
        for entry in sorted(target.iterdir()):
            if entry.name.startswith("."):
                continue
            if entry.is_dir():
                dirs.append({"name": entry.name, "path": str(entry)})
    except PermissionError:
        pass
    return {"current": str(target), "parent": str(target.parent), "dirs": dirs}


@router.get("/folders")
def list_folders(root: str | None = None, svc: ImageService = Depends(get_image_service)):
    return svc.get_folder_tree(root)


@router.get("/folders/images")
def list_folder_images(
    path: str,
    skip: int = 0,
    limit: int = 100,
    svc: ImageService = Depends(get_image_service),
):
    items, total = svc.list_images_in_folder(path, skip=skip, limit=limit)
    return {
        "items": [ImageOut.from_orm_image(i) for i in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{image_id}")
def get_image(image_id: UUID, svc: ImageService = Depends(get_image_service)):
    img = svc.get(image_id)
    if not img:
        raise HTTPException(404, "Image not found")
    return ImageOut.from_orm_image(img)


@router.get("/{image_id}/file")
def get_image_file(image_id: UUID, svc: ImageService = Depends(get_image_service)):
    img = svc.get(image_id)
    if not img:
        raise HTTPException(404, "Image not found")
    p = Path(img.file_path)
    if not p.exists():
        raise HTTPException(404, "File not found on disk")
    return FileResponse(str(p), media_type=img.mime_type or "image/jpeg")


@router.get("/{image_id}/thumbnail")
def get_thumbnail(image_id: UUID, size: int = 300, svc: ImageService = Depends(get_image_service)):
    from io import BytesIO
    from PIL import Image
    from fastapi.responses import StreamingResponse

    img = svc.get(image_id)
    if not img:
        raise HTTPException(404, "Image not found")
    p = Path(img.file_path)
    if not p.exists():
        raise HTTPException(404, "File not found on disk")

    pil_img = Image.open(p)
    pil_img.thumbnail((size, size), Image.Resampling.LANCZOS)
    if pil_img.mode not in ("RGB", "L"):
        pil_img = pil_img.convert("RGB")
    buf = BytesIO()
    pil_img.save(buf, format="JPEG", quality=80)
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/jpeg")


@router.post("/scan", response_model=ScanResponse)
def scan_directory(req: ScanRequest, bg: BackgroundTasks, svc: ImageService = Depends(get_image_service)):
    result = svc.scan_directory(req.directory, req.recursive)
    from app.services.worker import start_worker
    bg.add_task(start_worker)
    return ScanResponse(**result)


@router.post("/upload", response_model=list[UploadResponse])
async def upload_images(files: list[UploadFile] = File(...), svc: ImageService = Depends(get_image_service)):
    results = []
    for f in files:
        content = await f.read()
        image_id = svc.save_upload(f.filename or "upload.jpg", content)
        img = svc.get(image_id)
        results.append(UploadResponse(image_id=image_id, file_path=img.file_path if img else ""))
    from app.services.worker import start_worker
    start_worker()
    return results


@router.post("/index")
def index_single(image_path: str, svc: ImageService = Depends(get_image_service)):
    result = svc.index_image(image_path)
    if not result:
        raise HTTPException(400, "Failed to index image")
    return {"image_id": result}


@router.post("/bulk-index", response_model=BulkIndexResponse)
def bulk_index(req: BulkIndexRequest, svc: ImageService = Depends(get_image_service)):
    result = svc.bulk_index(req.directory, req.recursive, req.extensions)
    return BulkIndexResponse(**result)


@router.delete("/{image_id}")
def delete_image(image_id: UUID, svc: ImageService = Depends(get_image_service)):
    if not svc.delete(image_id):
        raise HTTPException(404, "Image not found")
    return {"deleted": True}


@router.post("/{image_id}/favorite")
def toggle_favorite(image_id: UUID, svc: ImageService = Depends(get_image_service)):
    result = svc.toggle_favorite(image_id)
    if result is None:
        raise HTTPException(404, "Image not found")
    return {"is_favorite": result}


@router.post("/reprocess-faces")
def reprocess_faces(bg: BackgroundTasks, svc: ImageService = Depends(get_image_service)):
    count = svc.clear_and_requeue_faces()
    from app.services.worker import start_worker
    bg.add_task(start_worker)
    return {"requeued": count}
