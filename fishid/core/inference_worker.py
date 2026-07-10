# fishid/core/inference_worker.py
import numpy as np
from PySide6.QtCore import QThread, Signal
import cv2


class InferenceWorker(QThread):
    result_ready = Signal(int, str, float, object, int, object)  # track_id, class_name, confidence, cropped_image, frame_idx, bbox

    def __init__(self, frame, tracks_to_classify, dinov2, anomaly_detector, classifier,
                 conf_threshold, anomaly_threshold, mode, video_name, frame_idx,
                 is_single_object_mode=False, use_direct_classifier=False):
        super().__init__()
        self.frame = frame
        self.tracks_to_classify = tracks_to_classify
        self.dinov2 = dinov2
        self.anomaly_detector = anomaly_detector
        self.classifier = classifier          # classifieur classique (pour poissons)
        self.direct_classifier = None         # classifieur direct (pour déchets)
        self.conf_threshold = conf_threshold
        self.anomaly_threshold = anomaly_threshold
        self.mode = mode
        self.video_name = video_name
        self.frame_idx = frame_idx
        self.is_single_object_mode = is_single_object_mode
        self.use_direct_classifier = use_direct_classifier

    def run(self):
        for track in self.tracks_to_classify:
            track_id = track['track_id']
            bbox = track['bbox']
            x1, y1, x2, y2 = map(int, bbox)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(self.frame.shape[1], x2), min(self.frame.shape[0], y2)

            if self.is_single_object_mode:
                cropped = self.frame
            else:
                if x2 <= x1 or y2 <= y1:
                    continue
                cropped = self.frame[y1:y2, x1:x2]

            if cropped is None or cropped.size == 0:
                continue

            # ---- Mode direct (déchets) ----
            if self.use_direct_classifier and self.direct_classifier is not None:
                try:
                    # Détecter automatiquement le type d'entrée si non défini
                    if not hasattr(self.direct_classifier, 'input_type'):
                        # Essayer de détecter via la forme du modèle
                        if hasattr(self.direct_classifier, 'session'):
                            input_shape = self.direct_classifier.session.get_inputs()[0].shape
                            if len(input_shape) == 4:
                                self.direct_classifier.input_type = "image"
                            elif len(input_shape) == 2:
                                self.direct_classifier.input_type = "features"
                            else:
                                self.direct_classifier.input_type = "unknown"

                    # Choisir la bonne méthode
                    if self.direct_classifier.input_type == "image":
                        result = self.direct_classifier.classify_image(cropped)
                    elif self.direct_classifier.input_type == "features":
                        # Extraire les features DINOv2
                        features = self.dinov2.extract_features(cropped)
                        if features is None:
                            continue
                        # Vérifier que le classifieur a bien la méthode
                        if hasattr(self.direct_classifier, 'classify_from_features'):
                            result = self.direct_classifier.classify_from_features(features)
                        else:
                            # Fallback : utiliser le classifieur standard avec les features
                            result = self.classifier.classify_from_features(features)
                    else:
                        # Type inconnu : essayer image d'abord, puis features
                        try:
                            result = self.direct_classifier.classify_image(cropped)
                        except:
                            features = self.dinov2.extract_features(cropped)
                            if features is None:
                                continue
                            if hasattr(self.direct_classifier, 'classify_from_features'):
                                result = self.direct_classifier.classify_from_features(features)
                            else:
                                result = self.classifier.classify_from_features(features)

                except Exception as e:
                    print(f"Erreur dans InferenceWorker (direct_classifier) : {e}")
                    continue

                if result is None:
                    continue

                class_name = result['class_name']
                confidence = result['confidence']
                if confidence < self.conf_threshold:
                    class_name = "Incertain"

                self.result_ready.emit(
                    track_id,
                    class_name,
                    confidence,
                    cropped,
                    self.frame_idx,
                    bbox
                )
                continue

            # ---- Pipeline standard (DINOv2 + classifieur) ----
            features = self.dinov2.extract_features(cropped)
            if features is None:
                continue

            # Détection d'anomalie (avec gestion d'erreur)
            is_anomaly = False
            if self.anomaly_detector is not None:
                try:
                    if hasattr(self.anomaly_detector, 'predict'):
                        is_anomaly = self.anomaly_detector.predict(features)
                    elif hasattr(self.anomaly_detector, 'predict_anomaly'):
                        is_anomaly = self.anomaly_detector.predict_anomaly(features)
                    elif hasattr(self.anomaly_detector, 'detect'):
                        is_anomaly = self.anomaly_detector.detect(features)
                except Exception as e:
                    print(f"Erreur détection anomalie : {e}")
                    is_anomaly = False

            if is_anomaly:
                class_name = "Inconnu"
                confidence = 0.0
            else:
                result = self.classifier.classify_from_features(features)
                if result is None:
                    continue
                class_name = result['class_name']
                confidence = result['confidence']

            if confidence < self.conf_threshold:
                class_name = "Incertain"

            self.result_ready.emit(
                track_id,
                class_name,
                confidence,
                cropped,
                self.frame_idx,
                bbox
            )