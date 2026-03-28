from __future__ import annotations

SCENE_LABELS = [
    "indoor", "outdoor", "beach", "mountain", "city", "street",
    "office", "restaurant", "home", "living room", "bedroom", "kitchen",
    "park", "garden", "wedding", "party", "gym", "stadium",
    "airport", "hotel", "hospital", "school", "church", "museum",
    "forest", "lake", "river", "desert", "snow", "night",
]


class ScenePipeline:
    def classify(self, image_path: str) -> dict:
        try:
            from app.pipeline.understanding.embedding import CLIPEmbedder
            embedder = CLIPEmbedder.get()
            image_vec = embedder.encode_image(image_path)

            import numpy as np
            scene_prompts = [f"a photo of a {label}" for label in SCENE_LABELS]
            scores = []
            for prompt in scene_prompts:
                text_vec = embedder.encode_text(prompt)
                sim = float(np.dot(image_vec, text_vec))
                scores.append(sim)

            ranked = sorted(zip(SCENE_LABELS, scores), key=lambda x: -x[1])
            return {
                "scene_type": ranked[0][0],
                "scene_scores": {label: round(score, 4) for label, score in ranked[:5]},
            }
        except Exception:
            return {"scene_type": None, "scene_scores": {}}
