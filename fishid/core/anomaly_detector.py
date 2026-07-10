# core/anomaly_detector.py
import numpy as np
import os
from PySide6.QtCore import QObject, Signal
from sklearn.ensemble import IsolationForest

class AnomalyDetector(QObject):
    model_loaded = Signal(bool)
    status_message = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, model_path: str = "models/isolation_forest.pkl",
                contamination: float = 0.1):
        super().__init__()
        self.model_path = model_path
        self.contamination = contamination
        self.model = None
        self._is_fitted = False

    def load_model(self) -> bool:
        """Charge un modèle pré‑entraîné (joblib ou pickle), sinon crée un modèle neutre."""
        if os.path.exists(self.model_path):
            try:
                import joblib
                self.model = joblib.load(self.model_path)
                self._is_fitted = True
                self.status_message.emit("✅ Détecteur d'anomalies chargé")
                self.model_loaded.emit(True)
                return True
            except Exception as e:
                self.error_occurred.emit(f"Erreur joblib : {e}")

        # Fallback : modèle non entraîné (tout est normal)
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_estimators=100
        )
        self._is_fitted = False
        self.status_message.emit("⚠️ Aucun modèle d'anomalies – tout sera normal")
        self.model_loaded.emit(False)
        return False

    def is_anomaly(self, features: np.ndarray) -> bool:
        """Retourne True si les caractéristiques sont anormales (prédiction -1)."""
        if not self._is_fitted or self.model is None:
            return False
        if features is None:
            return True
        features = np.array(features).reshape(1, -1)
        pred = self.model.predict(features)[0]
        return pred == -1

    def set_contamination(self, value: float):
        self.contamination = max(0.01, min(0.5, value))
        if self.model is not None:
            self.model.set_params(contamination=self.contamination)