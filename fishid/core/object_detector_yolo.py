# core/object_detector_yolov8.py
import cv2
import numpy as np
import onnxruntime as ort
from PySide6.QtCore import QObject, Signal

class YOLOv8Detector(QObject):
    model_loaded = Signal(bool)
    status_message = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, model_path="models/yolov10n.onnx", conf_threshold=0.2, nms_threshold=0.1):
        super().__init__()
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.nms_threshold = nms_threshold
        self.session = None
        self.input_width = 640
        self.input_height = 640
        self.class_names = []
        self._load_names()

    def load_model(self, use_gpu: bool = False) -> bool:
        """Charge YOLOv8 ONNX. Si use_gpu=True, tente CUDA."""
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if use_gpu else ['CPUExecutionProvider']
        try:
            self.session = ort.InferenceSession(self.model_path, providers=providers)
            self.input_name = self.session.get_inputs()[0].name
            shape = self.session.get_inputs()[0].shape
            self.input_height, self.input_width = shape[2], shape[3]
            self._load_names()
            self.status_message.emit(f"✅ YOLOv8 chargé ({self.model_path})")
            self.model_loaded.emit(True)
            return True
        except Exception as e:
            if use_gpu:
                self.error_occurred.emit(f"GPU échoué, tentative CPU...")
                return self.load_model(use_gpu=False)
            self.error_occurred.emit(f"Erreur chargement YOLOv8 : {e}")
            return False

    def _load_names(self):
        # Charger les noms COCO (80 classes)
        names_file = "models/coco.names"
        if __import__('os').path.exists(names_file):
            with open(names_file, 'r') as f:
                self.class_names = [line.strip() for line in f.readlines()]
        else:
            # Classes COCO simplifiées
            self.class_names = [str(i) for i in range(80)]

    def detect_objects(self, frame: np.ndarray) -> list:
        if frame is None or self.session is None:
            return []

        # Prétraitement
        img = cv2.resize(frame, (self.input_width, self.input_height))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.astype(np.float32) / 255.0
        img = np.transpose(img, (2, 0, 1))
        img = np.expand_dims(img, axis=0)

        # Inférence
        outputs = self.session.run(None, {self.input_name: img})
        # Sortie typique : [1, 84, 8400]  (84 = 4 + 80 classes)
        preds = outputs[0][0]  # shape (84, nb_boxes) si batch=1
        preds = np.transpose(preds)  # (nb_boxes, 84)

        # Décodage
        boxes = []
        scores = []
        class_ids = []
        for pred in preds:
            # Les 4 premiers sont (x_center, y_center, width, height)
            xc, yc, w, h = pred[:4]
            conf = pred[4:].max()
            cls = pred[4:].argmax()
            if conf >= self.conf_threshold:
                # Conversion en xyxy
                x1 = xc - w/2
                y1 = yc - h/2
                x2 = xc + w/2
                y2 = yc + h/2
                # Mise à l'échelle
                orig_h, orig_w = frame.shape[:2]
                x1 *= orig_w / self.input_width
                y1 *= orig_h / self.input_height
                x2 *= orig_w / self.input_width
                y2 *= orig_h / self.input_height
                boxes.append([x1, y1, x2, y2])
                scores.append(float(conf))
                class_ids.append(int(cls))

        # NMS
        if boxes:
            indices = cv2.dnn.NMSBoxes(boxes, scores, self.conf_threshold, self.nms_threshold)
            detections = []
            if len(indices) > 0:
                for i in indices.flatten():
                    x1, y1, x2, y2 = boxes[i]
                    detections.append({
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': scores[i],
                        'class_id': class_ids[i],
                        'class_name': self.class_names[class_ids[i]] if class_ids[i] < len(self.class_names) else f"cls_{class_ids[i]}"
                    })
            return detections
        return []

    def crop_object(self, frame, bbox, margin=10):
        x1, y1, x2, y2 = bbox
        h, w = frame.shape[:2]
        x1 = max(0, x1 - margin)
        y1 = max(0, y1 - margin)
        x2 = min(w, x2 + margin)
        y2 = min(h, y2 + margin)
        if x2 <= x1 or y2 <= y1:
            return None
        return frame[y1:y2, x1:x2].copy()