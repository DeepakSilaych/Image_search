from __future__ import annotations

import numpy as np

IMAGE_TYPE_LABELS = {
    "selfie": "a selfie photo taken by holding the camera",
    "group_photo": "a group photo with multiple people",
    "portrait": "a portrait photo of one person",
    "landscape": "a landscape or scenery photo with no people",
    "screenshot": "a screenshot from a phone or computer",
    "document": "a photo of a document or paper",
    "meme": "an internet meme or funny image with text",
    "food": "a photo of food or a meal",
    "pet": "a photo of a pet or animal",
    "other": "a miscellaneous photo",
}


class ImageClassifier:
    def classify(self, image_path: str) -> dict:
        try:
            from app.pipeline.understanding.embedding import CLIPEmbedder
            embedder = CLIPEmbedder.get()
            image_vec = embedder.encode_image(image_path)

            scores = {}
            for label, prompt in IMAGE_TYPE_LABELS.items():
                text_vec = embedder.encode_text(f"a photo that is {prompt}")
                scores[label] = float(np.dot(image_vec, text_vec))

            best = max(scores, key=scores.get)
            return {"image_type": best, "type_scores": scores}
        except Exception:
            return {"image_type": None, "type_scores": {}}
