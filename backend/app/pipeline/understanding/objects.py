from __future__ import annotations

from pathlib import Path


class ObjectDetectionPipeline:
    _model = None

    def _get_model(self):
        if self._model is None:
            from ultralytics import YOLO
            self._model = YOLO("yolov8n.pt")
        return self._model

    def detect(self, image_path: str | Path) -> list[dict]:
        try:
            model = self._get_model()
            results = model(str(image_path), verbose=False)
            detections = []
            for result in results:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    label = result.names[cls_id]
                    conf = float(box.conf[0])
                    if conf < 0.3:
                        continue
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    detections.append({
                        "label": label,
                        "confidence": conf,
                        "bbox": {"x": x1, "y": y1, "w": x2 - x1, "h": y2 - y1},
                    })
            return detections
        except Exception:
            return []
