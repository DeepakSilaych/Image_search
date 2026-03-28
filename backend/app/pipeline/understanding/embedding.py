from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image

from app.config import get_settings


class CLIPEmbedder:
    _instance: CLIPEmbedder | None = None

    def __init__(self):
        import open_clip
        settings = get_settings()
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            settings.clip_model, pretrained=settings.clip_pretrained
        )
        self.tokenizer = open_clip.get_tokenizer(settings.clip_model)
        self.model.eval()
        self._dimension: int | None = None

    @classmethod
    def get(cls) -> CLIPEmbedder:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def dimension(self) -> int:
        if self._dimension is None:
            dummy = self.encode_text("test")
            self._dimension = len(dummy)
        return self._dimension

    def encode_image(self, image_path: str | Path) -> list[float]:
        import torch
        img = Image.open(image_path).convert("RGB")
        tensor = self.preprocess(img).unsqueeze(0)
        with torch.no_grad():
            features = self.model.encode_image(tensor)
            features = features / features.norm(dim=-1, keepdim=True)
        return features.squeeze().cpu().numpy().tolist()

    def encode_text(self, text: str) -> list[float]:
        import torch
        tokens = self.tokenizer([text])
        with torch.no_grad():
            features = self.model.encode_text(tokens)
            features = features / features.norm(dim=-1, keepdim=True)
        return features.squeeze().cpu().numpy().tolist()

    def encode_images_batch(self, paths: list[str | Path]) -> list[list[float]]:
        import torch
        tensors = []
        valid_indices = []
        for i, p in enumerate(paths):
            try:
                img = Image.open(p).convert("RGB")
                tensors.append(self.preprocess(img))
                valid_indices.append(i)
            except Exception:
                continue
        if not tensors:
            return []
        batch = torch.stack(tensors)
        with torch.no_grad():
            features = self.model.encode_image(batch)
            features = features / features.norm(dim=-1, keepdim=True)
        results: list[list[float]] = [[] for _ in paths]
        for idx, feat in zip(valid_indices, features.cpu().numpy()):
            results[idx] = feat.tolist()
        return results
