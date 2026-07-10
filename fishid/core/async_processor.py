# core/async_processor.py
import cv2, numpy as np, time, os, threading, queue
from PySide6.QtCore import QObject, Signal
import queue  # module standard
import threading
import time
import numpy as np
import cv2
class CaptureThread(threading.Thread):
    """Thread de lecture vidéo : lit en continu et empile les frames brutes."""
    def __init__(self, video_reader, raw_queue, max_frames=30):
        super().__init__(daemon=True)
        self.video_reader = video_reader
        self.raw_queue = raw_queue
        self.max_frames = max_frames
        self._stop_event = threading.Event()

    def run(self):
        while not self._stop_event.is_set():
            ret, frame = self.video_reader.read_frame_safe()
            if not ret or frame is None:
                break
            if self.raw_queue.full():
                try:
                    self.raw_queue.get_nowait()
                except queue.Empty:
                    pass
            self.raw_queue.put(frame)

    def stop(self):
        self._stop_event.set()


class InferenceThread(threading.Thread):
    """Thread d'inférence : consomme les frames brutes et produit les frames annotées."""
    frame_annotated = Signal(np.ndarray)

    def __init__(self, raw_queue, annotated_queue, object_detector,
                 feature_extractor, anomaly_detector, classifier,
                 duplicate_checker, tracker, frame_interval=1,
                 conf_threshold=0.2, anomaly_threshold=0.9,
                 mode="fish"):
        super().__init__(daemon=True)
        self.raw_queue = raw_queue
        self.annotated_queue = annotated_queue
        self.object_detector = object_detector
        self.extractor = feature_extractor
        self.anomaly_detector = anomaly_detector
        self.classifier = classifier
        self.duplicate_checker = duplicate_checker
        self.tracker = tracker
        self.frame_interval = frame_interval
        self.conf_threshold = conf_threshold
        self.anomaly_threshold = anomaly_threshold
        self.mode = mode
        self._stop_event = threading.Event()
        self.classified_tracks = {}
        self.track_features = {}
        self.reid_interval = 10
        self.reid_similarity_threshold = 0.7
        self.frame_count = 0

    def run(self):
        while not self._stop_event.is_set():
            try:
               frame = self.raw_queue.get_nowait()
            except queue.Empty:
                time.sleep(0.01)
                continue

            self.frame_count += 1
            if self.frame_count % self.frame_interval != 0:
                continue

            # 1. Détection YOLO
            detections = self.object_detector.detect_objects(frame)
            # 2. Tracking
            tracks = self.tracker.update(detections, frame)
            # 3. Vérification d'identité périodique
            if self.frame_count % (self.frame_interval * self.reid_interval) == 0:
                self._verify_tracks(tracks, frame)

            annotated = frame.copy()
            for trk in tracks:
                bbox = trk['bbox']
                tid = trk['track_id']
                if tid not in self.classified_tracks:
                    cropped = self.object_detector.crop_object(frame, bbox)
                    if cropped is not None and cropped.shape[0] * cropped.shape[1] > 800:
                        features = self.extractor.extract_features(cropped)
                        if features is not None:
                            if self.anomaly_detector.is_anomaly(features):
                                class_name = "Inconnu"
                                confidence = 1.0
                                is_anom = True
                            else:
                                is_anom = False
                                res = self.classifier.classify_from_features(features)
                                if res and res['confidence'] >= self.conf_threshold:
                                    class_name = res['class_name']
                                    confidence = res['confidence']
                                else:
                                    class_name = "Incertain"
                                    confidence = res['confidence'] if res else 0.0
                            self.classified_tracks[tid] = {
                                'class_name': class_name,
                                'confidence': confidence,
                                'is_anomaly': is_anom,
                                'best_image': cropped.copy(),
                                'best_score': self._image_quality(cropped),
                                'frame_classified': self.frame_count
                            }
                            self.track_features[tid] = features.copy()
                        else:
                            class_name = "?"
                            self.classified_tracks[tid] = {
                                'class_name': class_name, 'confidence': 0.0,
                                'is_anomaly': True, 'best_image': None,
                                'best_score': 0.0, 'frame_classified': self.frame_count
                            }
                            self.track_features.pop(tid, None)
                    else:
                        class_name = "?"
                        self.classified_tracks[tid] = {
                            'class_name': class_name, 'confidence': 0.0,
                            'is_anomaly': True, 'best_image': None,
                            'best_score': 0.0, 'frame_classified': self.frame_count
                        }
                        self.track_features.pop(tid, None)
                else:
                    data = self.classified_tracks[tid]
                    class_name = data['class_name']
                    cropped = self.object_detector.crop_object(frame, bbox)
                    if cropped is not None:
                        score = self._image_quality(cropped)
                        if score > data['best_score']:
                            data['best_image'] = cropped.copy()
                            data['best_score'] = score
                            data['frame_classified'] = self.frame_count

                annotated = self._draw_track_box(annotated, bbox, tid, class_name)

            # Placer la frame annotée (écrase la plus ancienne si la queue est pleine)
            if self.annotated_queue.full():
                try:
                    self.annotated_queue.get_nowait()
                except queue.Empty:
                    pass
            self.annotated_queue.put(annotated)

    def stop(self):
        self._stop_event.set()

    def _verify_tracks(self, tracks, frame):
        for trk in tracks:
            tid = trk['track_id']
            if tid not in self.classified_tracks or tid not in self.track_features:
                continue
            stored = self.track_features[tid]
            bbox = trk['bbox']
            cropped = self.object_detector.crop_object(frame, bbox)
            if cropped is None or cropped.shape[0] * cropped.shape[1] < 800:
                continue
            current = self.extractor.extract_features(cropped)
            if current is None:
                continue
            sim = np.dot(current, stored) / (np.linalg.norm(current) * np.linalg.norm(stored) + 1e-8)
            if sim < self.reid_similarity_threshold:
                del self.classified_tracks[tid]
                del self.track_features[tid]

    def _draw_track_box(self, frame, bbox, track_id, class_name):
        x1, y1, x2, y2 = bbox
        color = (0, 255, 0) if class_name not in ("Inconnu", "?", "Incertain") else (0, 0, 255)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = f"ID:{track_id} {class_name}"
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        return frame

    def _image_quality(self, image):
        if image is None:
            return 0.0
        h, w = image.shape[:2]
        area = h * w
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        return area * 0.5 + laplacian_var * 0.5