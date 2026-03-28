from __future__ import annotations

import logging
import mimetypes
import shutil
import uuid
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import Image, ImageFace, ImageObject, ImageTag
from app.db.repo import Repository
from app.pipeline.ingestion import discover_images, walk_images, extract_basic_metadata

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "uploads"


class ImageService:
    def __init__(self, session: Session):
        self._session = session
        self._repo = Repository(session, Image)

    def get(self, image_id: UUID) -> Image | None:
        return self._repo.get(image_id)

    def list_images(self, skip: int = 0, limit: int = 50, **filters) -> tuple[list[Image], int]:
        items = self._repo.list(skip=skip, limit=limit, order_by="-created_at", **filters)
        total = self._repo.count(**filters)
        return items, total

    def scan_directory(self, directory: str, recursive: bool = True) -> dict:
        registered = 0
        skipped = 0
        errors = 0

        for path in walk_images(directory, recursive=recursive):
            try:
                resolved = str(path.resolve())
                existing = self._repo.get_by(file_path=resolved)
                if existing:
                    skipped += 1
                    continue

                metadata = extract_basic_metadata(path)
                self._repo.create(**metadata, processing_status="pending")
                registered += 1

                if registered % 500 == 0:
                    self._repo.commit()
                    logger.info(f"Scan progress: {registered} registered, {skipped} skipped")

            except Exception as e:
                errors += 1
                logger.debug(f"Scan skip {path}: {e}")

        self._repo.commit()
        return {"registered": registered, "skipped": skipped, "errors": errors}

    def save_upload(self, filename: str, content: bytes) -> UUID:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        ext = Path(filename).suffix.lower() or ".jpg"
        dest_name = f"{uuid.uuid4().hex}{ext}"
        dest = UPLOAD_DIR / dest_name
        dest.write_bytes(content)

        metadata = extract_basic_metadata(dest)
        image = self._repo.create(**metadata, processing_status="pending")
        self._repo.commit()
        return image.id

    def index_image(self, image_path: str) -> UUID | None:
        from app.pipeline.orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        return orchestrator.process_image(self._session, image_path)

    def bulk_index(self, directory: str, recursive: bool = True, extensions: list[str] | None = None) -> dict:
        ext_set = set(extensions) if extensions else None
        paths = discover_images(directory, recursive=recursive, extensions=ext_set)

        queued = 0
        skipped = 0
        errors = []

        for path in paths:
            existing = self._repo.get_by(file_path=str(path.resolve()))
            if existing and existing.processing_status == "completed":
                skipped += 1
                continue
            try:
                result = self.index_image(str(path))
                if result:
                    queued += 1
                else:
                    skipped += 1
            except Exception as e:
                errors.append(f"{path}: {e}")

        return {"queued": queued, "skipped": skipped, "errors": errors}

    def delete(self, image_id: UUID) -> bool:
        from app.vector.client import get_qdrant
        from app.vector.store import delete_image_vector

        Repository(self._session, ImageFace).delete_many(image_id=image_id)
        Repository(self._session, ImageObject).delete_many(image_id=image_id)
        Repository(self._session, ImageTag).delete_many(image_id=image_id)

        success = self._repo.delete(image_id)
        if success:
            try:
                delete_image_vector(get_qdrant(), image_id)
            except Exception:
                pass
            self._repo.commit()
        return success

    def clear_and_requeue_faces(self) -> int:
        from app.vector.client import get_qdrant
        from app.vector.store import COLLECTION_FACES

        face_repo = Repository(self._session, ImageFace)
        face_repo.delete_many()
        self._repo.commit()

        try:
            qdrant = get_qdrant()
            qdrant.delete_collection(COLLECTION_FACES)
        except Exception:
            pass

        completed = self._repo.list(limit=10000, processing_status="completed")
        count = 0
        for img in completed:
            img.processing_status = "faces_pending"
            count += 1
        self._repo.commit()
        return count

    def toggle_favorite(self, image_id: UUID) -> bool | None:
        img = self._repo.get(image_id)
        if not img:
            return None
        img.is_favorite = not img.is_favorite
        self._repo.commit()
        return img.is_favorite

    def get_folder_tree(self, root: str | None = None) -> dict:
        from collections import defaultdict

        all_paths = self._session.query(Image.file_path).filter(
            Image.processing_status == "completed"
        ).all()
        if not all_paths:
            return {"root": root or "/", "folders": [], "direct_images": 0}

        folder_counts: dict[str, int] = defaultdict(int)
        for (fp,) in all_paths:
            folder = str(Path(fp).parent)
            folder_counts[folder] += 1

        if not root:
            all_folder_paths = [Path(f) for f in folder_counts]
            common = Path(all_folder_paths[0].parts[0])
            for part_idx in range(1, min(len(p.parts) for p in all_folder_paths)):
                candidate = set(p.parts[part_idx] for p in all_folder_paths)
                if len(candidate) == 1:
                    common = common / candidate.pop()
                else:
                    break
            root = str(common)

        root = root.rstrip("/")
        root_depth = len(Path(root).parts)

        immediate_children: dict[str, int] = defaultdict(int)
        for folder, count in folder_counts.items():
            if folder == root:
                continue
            if not folder.startswith(root + "/"):
                continue
            parts = Path(folder).parts
            child_path = str(Path(*parts[: root_depth + 1]))
            immediate_children[child_path] += count

        all_folders = sorted(folder_counts.keys())
        folders = []
        for child_path, total_count in sorted(immediate_children.items(), key=lambda x: x[0].lower()):
            direct_count = folder_counts.get(child_path, 0)
            has_subfolders = any(
                f != child_path and f.startswith(child_path + "/")
                for f in all_folders
            )
            folders.append({
                "path": child_path,
                "name": Path(child_path).name or child_path,
                "image_count": direct_count,
                "total_count": total_count,
                "has_children": has_subfolders,
            })

        return {
            "root": root,
            "folders": folders,
            "direct_images": folder_counts.get(root, 0),
        }

    def list_images_in_folder(self, folder: str, skip: int = 0, limit: int = 100) -> tuple[list[Image], int]:
        from sqlalchemy import select, func

        folder = folder.rstrip("/")
        base = (
            select(Image)
            .where(Image.file_path.like(folder + "/%"))
            .where(~Image.file_path.like(folder + "/%/%"))
            .where(Image.processing_status == "completed")
        )

        total = self._session.execute(
            select(func.count()).select_from(base.subquery())
        ).scalar_one()

        items = self._session.execute(
            base.order_by(Image.file_path).offset(skip).limit(limit)
        ).scalars().all()

        return list(items), total
