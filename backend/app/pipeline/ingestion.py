from __future__ import annotations

import logging
import mimetypes
import os
from pathlib import Path
from typing import Generator

import imagehash
from PIL import Image

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".webp", ".bmp", ".tiff", ".gif"}

SKIP_DIRS = {
    ".git", ".svn", ".hg", "node_modules", "__pycache__", ".venv", "venv",
    ".cache", ".Trash", ".npm", ".yarn", ".cargo", ".rustup",
    "Library", "Applications", ".local", ".config",
    ".docker", ".kube", "snap", ".gradle", ".m2",
}


def discover_images(directory: str | Path, recursive: bool = True, extensions: set[str] | None = None) -> list[Path]:
    return list(walk_images(directory, recursive, extensions))


def walk_images(
    directory: str | Path, recursive: bool = True, extensions: set[str] | None = None
) -> Generator[Path, None, None]:
    exts = extensions or SUPPORTED_EXTENSIONS
    root = str(Path(directory).resolve())

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if d not in SKIP_DIRS and not d.startswith(".")
        ]

        for fname in filenames:
            if fname.startswith("."):
                continue
            ext = os.path.splitext(fname)[1].lower()
            if ext in exts:
                yield Path(dirpath) / fname

        if not recursive:
            break


def compute_phash(image_path: str | Path) -> str:
    img = Image.open(image_path)
    return str(imagehash.phash(img))


def extract_basic_metadata(image_path: str | Path) -> dict:
    p = Path(image_path)
    stat = p.stat()
    mime, _ = mimetypes.guess_type(str(p))

    try:
        img = Image.open(p)
        width, height = img.size
    except Exception:
        width, height = None, None

    return {
        "file_path": str(p.resolve()),
        "file_size": stat.st_size,
        "mime_type": mime or "image/unknown",
        "width": width,
        "height": height,
    }


def is_duplicate(file_hash: str, existing_hashes: set[str], threshold: int = 6) -> bool:
    target = imagehash.hex_to_hash(file_hash)
    for h in existing_hashes:
        if target - imagehash.hex_to_hash(h) <= threshold:
            return True
    return False
