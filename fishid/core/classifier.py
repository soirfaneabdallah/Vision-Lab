# fishid/core/classifier.py
import numpy as np
import onnxruntime as ort
from PySide6.QtCore import QObject, Signal


class FishClassifier(QObject):
    model_loaded = Signal(bool)
    error_occurred = Signal(str)
    status_message = Signal(str)

    def __init__(self, model_path: str = "models/classify.onnx"):
        super().__init__()
        self.model_path = model_path
        self.session = None
        self.input_name = None
        self.class_names = []

    def load_model(self, use_gpu: bool = False) -> bool:
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if use_gpu else ['CPUExecutionProvider']
        try:
            self.session = ort.InferenceSession(self.model_path, providers=providers)
            self.input_name = self.session.get_inputs()[0].name
            self.status_message.emit("✅ Classifieur chargé")
            self.model_loaded.emit(True)
            return True
        except Exception as e:
            if use_gpu:
                self.error_occurred.emit(f"GPU échoué, tentative CPU...")
                return self.load_model(use_gpu=False)
            self.status_message.emit(f"⚠️ Classifieur non trouvé : {self.model_path}")
            self.model_loaded.emit(False)
            return False

    def set_class_names(self, names: list):
        self.class_names = names

    def classify_from_features(self, features: np.ndarray) -> dict:
        if self.session is None or features is None:
            return None
        try:
            features = np.array(features).reshape(1, -1).astype(np.float32)
            outputs = self.session.run(None, {self.input_name: features})
            probs = outputs[0][0]  # déjà des probabilités (softmax intégré)
            
            class_id = int(np.argmax(probs))
            confidence = float(probs[class_id])
           
            class_name = self.class_names[class_id] if class_id < len(self.class_names) else f"classe_{class_id}"
            return {
                'class_name': class_name,
                'class_id': class_id,
                'confidence': confidence,
                'all_probs': probs.tolist()
            }
        except Exception as e:
            self.error_occurred.emit(f"Erreur classification : {e}")
            return None

    def classify(self, image: np.ndarray) -> dict:
        return self.classify_from_features(image)

    def unload_model(self):
        self.session = None
        self.status_message.emit("🔽 Classifieur déchargé")