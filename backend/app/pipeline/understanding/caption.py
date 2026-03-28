from __future__ import annotations

import base64
from pathlib import Path

from app.config import get_settings

CAPTION_PROMPT = """Analyze this image and provide:
1. A short caption (1 sentence)
2. A detailed description (2-3 sentences covering people, objects, scene, activities, clothing, mood)
3. Scene type (one of: indoor, outdoor, beach, mountain, city, office, restaurant, home, park, wedding, party, gym, travel, nature, other)
4. Image type (one of: selfie, group_photo, portrait, landscape, screenshot, document, meme, food, pet, object, other)

Respond in this exact JSON format:
{
    "caption": "...",
    "caption_detailed": "...",
    "scene_type": "...",
    "image_type": "..."
}"""


class CaptionPipeline:
    _client = None

    def _get_client(self):
        if self._client is None:
            import google.generativeai as genai
            genai.configure(api_key=get_settings().gemini_api_key)
            self._client = genai.GenerativeModel("gemini-2.0-flash")
        return self._client

    def generate(self, image_path: str | Path) -> dict:
        import json
        from PIL import Image

        try:
            model = self._get_client()
            img = Image.open(image_path)
            response = model.generate_content([CAPTION_PROMPT, img])
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(text)
        except Exception as e:
            return {
                "caption": None,
                "caption_detailed": None,
                "scene_type": None,
                "image_type": None,
                "error": str(e),
            }
