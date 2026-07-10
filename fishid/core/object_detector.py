# core/object_detector.py
import cv2
import numpy as np
from PySide6.QtCore import QObject, Signal

class YOLODetector(QObject):
    """Détecteur YOLOv3 via OpenCV DNN (à partir de .weights et .cfg)."""
    model_loaded = Signal(bool)
    status_message = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, weights_path="models/yolov3-tiny.weights", 
                 cfg_path="models/yolov3-tiny.cfg", 
                 names_path="models/coco.names",
                 conf_threshold=0.1, nms_threshold=0.1):
        super().__init__()
        self.weights_path = weights_path
        self.cfg_path = cfg_path
        self.names_path = names_path
        self.conf_threshold = conf_threshold
        self.nms_threshold = nms_threshold
        self.net = None
        self.class_names = []

    def load_model(self) -> bool:
        try:
            self.net = cv2.dnn.readNet(self.weights_path, self.cfg_path)
            # Charger les noms de classes
            if self.names_path:
                with open(self.names_path, 'r') as f:
                    self.class_names = [line.strip() for line in f.readlines()]
            else:
                self.class_names = ['objet']
            # Obtenir les couches de sortie
            layer_names = self.net.getLayerNames()
            self.output_layers = [layer_names[i - 1] for i in self.net.getUnconnectedOutLayers()]
            self.status_message.emit("✅ YOLOv3 chargé via OpenCV DNN")
            self.model_loaded.emit(True)
            return True
        except Exception as e:
            self.error_occurred.emit(f"Erreur chargement YOLO : {e}")
            return False

    def detect_objects(self, frame: np.ndarray) -> list:
        """Retourne une liste de détections {bbox, confidence, class_id, class_name}."""
        if frame is None or self.net is None:
            return []
        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0,0,0), True, crop=False)
        self.net.setInput(blob)
        outs = self.net.forward(self.output_layers)

        boxes = []
        confidences = []
        class_ids = []
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > self.conf_threshold:
                    center_x = int(detection[0] * w)
                    center_y = int(detection[1] * h)
                    bw = int(detection[2] * w)
                    bh = int(detection[3] * h)
                    x = int(center_x - bw/2)
                    y = int(center_y - bh/2)
                    boxes.append([x, y, bw, bh])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)

        indices = cv2.dnn.NMSBoxes(boxes, confidences, self.conf_threshold, self.nms_threshold)
        detections = []
        if len(indices) > 0:
            for i in indices.flatten():
                x, y, bw, bh = boxes[i]
                detections.append({
                    'bbox': [x, y, x+bw, y+bh],
                    'confidence': confidences[i],
                    'class_id': class_ids[i],
                    'class_name': self.class_names[class_ids[i]] if class_ids[i] < len(self.class_names) else 'objet'
                })
        return detections

    def crop_object(self, frame, bbox, margin=10):
        """Extrait la région de l'objet."""
        x1, y1, x2, y2 = bbox
        h, w = frame.shape[:2]
        x1 = max(0, x1 - margin)
        y1 = max(0, y1 - margin)
        x2 = min(w, x2 + margin)
        y2 = min(h, y2 + margin)
        if x2 <= x1 or y2 <= y1:
            return None
        return frame[y1:y2, x1:x2].copy()