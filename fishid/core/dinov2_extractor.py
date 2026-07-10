# core/dinov2_extractor.py
import cv2
import numpy as np
import onnxruntime as ort
from PySide6.QtCore import QObject, Signal


class DINOv2Extractor(QObject):
    """
    Extracteur de caractéristiques DINOv2.
    Utilise un modèle ONNX exporté (facebook/dinov2-small).
    """

    model_loaded = Signal(bool)
    status_message = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, model_path: str = "models/dinov2_backbone.onnx"):
        super().__init__()
        self.model_path = model_path
        self.session = None
        self.input_name = None
        self.input_width = 224
        self.input_height = 224
        self.feature_dim = 384  # DINOv2‑small → 384 dimensions

    def load_model(self, use_gpu: bool = False) -> bool:
        """Charge DINOv2 ONNX. Si use_gpu=True, tente d'utiliser CUDA."""
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if use_gpu else ['CPUExecutionProvider']
        try:
            self.session = ort.InferenceSession(self.model_path, providers=providers)
            self.input_name = self.session.get_inputs()[0].name
            output_shape = self.session.get_outputs()[1].shape
            if len(output_shape) >= 2:
                self.feature_dim = output_shape[1]
            self.status_message.emit(f"✅ DINOv2 chargé ({self.feature_dim} features)")
            self.model_loaded.emit(True)
            return True
        except Exception as e:
            if use_gpu:
                # Fallback CPU si GPU échoue
                self.error_occurred.emit(f"GPU échoué, tentative CPU...")
                return self.load_model(use_gpu=False)
            self.error_occurred.emit(f"Erreur DINOv2 : {e}")
            self.model_loaded.emit(False)
            return False

    def extract_features(self, image: np.ndarray) -> np.ndarray:
        """
        Extrait les features DINOv2 d'une image BGR.
        Retourne un vecteur numpy de taille (feature_dim,).
        """
        if self.session is None or image is None:
            return None

        try:
            # Prétraitement DINOv2 standard
            img = cv2.resize(image, (self.input_width, self.input_height))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = img.astype(np.float32) / 255.0

            mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
            std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
            img = (img - mean) / std

            # Mise en forme ONNX : (1, 3, H, W)
            img = np.transpose(img, (2, 0, 1))
            img = np.expand_dims(img, axis=0)

            # Inférence
            outputs = self.session.run(None, {self.input_name: img})
            # outputs[0] = last_hidden_state (batch, 197, 384)
            # outputs[1] = pooler_output (batch, 384) ← ce qu'il faut
            features = outputs[1][0]  # première (et unique) image du batch

            return features.astype(np.float32)

        except Exception as e:
            self.error_occurred.emit(f"Erreur extraction : {e}")
            return None

    def extract_features_batch(self, images: list) -> np.ndarray:
        """Extrait les features pour un lot d'images."""
        features_list = []
        for img in images:
            feat = self.extract_features(img)
            if feat is not None:
                features_list.append(feat)
        if features_list:
            return np.array(features_list)
        return None