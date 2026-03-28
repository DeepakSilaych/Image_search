from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://imagesearch:imagesearch@localhost:5434/imagesearch"
    qdrant_url: str = "http://localhost:6333"
    gemini_api_key: str = ""
    image_storage_path: str = str(Path.home() / "Pictures")

    clip_model: str = "ViT-B-32"
    clip_pretrained: str = "openai"

    face_model: str = "ArcFace"
    face_detector: str = "mtcnn"
    face_distance_threshold: float = 0.6
    face_min_confidence: float = 0.9

    processing_batch_size: int = 16
    worker_concurrency: int = 4
    pipeline_parallelism: int = 4
    search_default_limit: int = 50
    search_vector_candidates: int = 200

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
