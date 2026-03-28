from __future__ import annotations


class EmotionPipeline:
    def analyze(self, face_img) -> dict:
        try:
            from deepface import DeepFace
            analysis = DeepFace.analyze(
                img_path=face_img,
                actions=["emotion"],
                enforce_detection=False,
                detector_backend="skip",
            )
            if analysis:
                return {
                    "dominant_emotion": analysis[0].get("dominant_emotion"),
                    "emotions": analysis[0].get("emotion", {}),
                }
        except Exception:
            pass
        return {"dominant_emotion": None, "emotions": {}}
