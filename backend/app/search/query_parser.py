from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ParsedQuery:
    original: str
    persons: list[str] = field(default_factory=list)
    emotions: list[str] = field(default_factory=list)
    scenes: list[str] = field(default_factory=list)
    objects: list[str] = field(default_factory=list)
    clothing: list[str] = field(default_factory=list)
    time_refs: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    is_group: bool = False
    year: int | None = None
    semantic_text: str = ""

    def to_dict(self) -> dict:
        return {
            "original": self.original,
            "persons": self.persons,
            "emotions": self.emotions,
            "scenes": self.scenes,
            "objects": self.objects,
            "clothing": self.clothing,
            "time_refs": self.time_refs,
            "locations": self.locations,
            "is_group": self.is_group,
            "year": self.year,
            "semantic_text": self.semantic_text,
        }


EMOTION_KEYWORDS = {
    "happy", "sad", "angry", "laughing", "smiling", "crying",
    "surprised", "scared", "disgusted", "neutral", "serious",
}

SCENE_KEYWORDS = {
    "beach", "mountain", "city", "office", "restaurant", "home",
    "park", "wedding", "party", "gym", "airport", "hotel",
    "indoor", "outdoor", "night", "forest", "lake", "street",
}

GROUP_KEYWORDS = {"group", "friends", "family", "team", "together", "crowd", "people"}

CLOTHING_KEYWORDS = {
    "shirt", "dress", "suit", "jacket", "jeans", "shorts",
    "hat", "cap", "glasses", "sunglasses", "tie", "saree", "kurta",
}

COLOR_KEYWORDS = {
    "red", "blue", "green", "yellow", "white", "black",
    "pink", "purple", "orange", "brown", "grey", "gray",
}


class QueryParser:
    def __init__(self, known_persons: set[str] | None = None):
        self._known_persons = known_persons or set()

    def parse(self, query: str) -> ParsedQuery:
        parsed = ParsedQuery(original=query, semantic_text=query)
        lower = query.lower()
        words = re.findall(r'\b\w+\b', lower)

        for name in self._known_persons:
            if name.lower() in lower:
                parsed.persons.append(name)

        semantic = lower
        for name in parsed.persons:
            semantic = re.sub(re.escape(name.lower()), '', semantic)
        parsed.semantic_text = semantic.strip() or query

        for word in words:
            if word in EMOTION_KEYWORDS:
                parsed.emotions.append(word)
            if word in SCENE_KEYWORDS:
                parsed.scenes.append(word)
            if word in GROUP_KEYWORDS:
                parsed.is_group = True

        year_match = re.search(r'\b(20\d{2})\b', query)
        if year_match:
            parsed.year = int(year_match.group(1))

        time_patterns = [
            r'\b(last\s+(?:week|month|year))\b',
            r'\b(this\s+(?:week|month|year))\b',
            r'\b(yesterday|today|recent(?:ly)?)\b',
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b',
        ]
        for pattern in time_patterns:
            matches = re.findall(pattern, lower)
            parsed.time_refs.extend(matches)

        for i, word in enumerate(words):
            if word in CLOTHING_KEYWORDS:
                color = words[i - 1] if i > 0 and words[i - 1] in COLOR_KEYWORDS else None
                item = f"{color} {word}" if color else word
                parsed.clothing.append(item)

        return parsed
