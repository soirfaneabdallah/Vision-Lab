# core/detection.py
class Detection:
    def __init__(self, frame_idx: int, timestamp_ms: int, class_id: int, class_name: str, confidence: float, bbox: list[int]):
        """
        Args:
            frame_idx (int): Index de la frame où la détection a eu lieu.
            timestamp_ms (int): Timestamp de la frame en millisecondes.
            class_id (int): ID numérique de la classe détectée.
            class_name (str): Nom textuel de la classe détectée.
            confidence (float): Score de confiance de la détection.
            bbox (list[int]): Boîte englobante [x_min, y_min, x_max, y_max].
        """
        self.frame_idx = frame_idx
        self.timestamp_ms = timestamp_ms
        self.class_id = class_id
        self.class_name = class_name
        self.confidence = confidence
        self.bbox = bbox # Format: [x_min, y_min, x_max, y_max]
