# core/processor.py
import cv2
import numpy as np
import time
import os
from PySide6.QtCore import QThread, Signal
from fishid.core.tracker_wrapper import BoTSORTWrapper

class ProcessingWorker(QThread):
    frame_processed = Signal(np.ndarray)
    object_classified = Signal(str, float, bool, list)
    image_saved = Signal(str, str)
    progress_updated = Signal(int, int)
    finished = Signal()
    error_occurred = Signal(str)
    stats_updated = Signal(dict)

    def __init__(self, video_reader, object_detector, feature_extractor,
                 anomaly_detector, classifier, duplicate_checker,
                 frame_interval=1, conf_threshold=0.2,
                 anomaly_threshold=0.9, mode="fish",
                 processing_speed=1.0):
        super().__init__()
        self.video_reader = video_reader
        self.object_detector = object_detector
        self.extractor = feature_extractor
        self.anomaly_detector = anomaly_detector
        self.classifier = classifier
        self.duplicate_checker = duplicate_checker
        self.frame_interval = frame_interval
        self.conf_threshold = conf_threshold
        self.anomaly_threshold = anomaly_threshold   # conservé mais non utilisé en mode binaire
        self.mode = mode
        self.processing_speed = processing_speed
        self._is_running = False
        self.video_name = ""

        self.tracker = BoTSORTWrapper(
            lost_track_buffer=30,
            frame_rate=self.video_reader.fps or 30,
            track_activation_threshold=0.6,
            minimum_consecutive_frames=2,
            high_conf_det_threshold=0.5,
            enable_cmc=True,
            cmc_method="sparseOptFlow",
            cmc_downscale=2,
        )

        self.classified_tracks = {}
        self.track_features = {}
        self.reid_interval = 10
        self.reid_similarity_threshold = 0.7

    def set_video_name(self, name):
        self.video_name = name

    def set_mode(self, mode):
        self.mode = mode

    def set_processing_speed(self, speed):
        self.processing_speed = speed

    def run(self):
        self._is_running = True
        frame_count = 0
        fps = self.video_reader.fps or 30
        frame_delay = 1.0 / (fps * self.processing_speed)

        while self._is_running:
            loop_start = time.time()
            ret, frame = self.video_reader.read_frame_safe()
            if not ret or frame is None:
                break
            frame_count += 1

            if frame_count % self.frame_interval == 0:
                detections = self.object_detector.detect_objects(frame)
                tracks = self.tracker.update(detections, frame)

                if frame_count % (self.frame_interval * self.reid_interval) == 0:
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
                                # ----- Détection d'anomalie (binaire) -----
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
                                    'frame_classified': frame_count
                                }
                                self.track_features[tid] = features.copy()
                                self.object_classified.emit(class_name, confidence, is_anom, bbox)
                            else:
                                class_name = "?"
                                self.classified_tracks[tid] = {
                                    'class_name': class_name, 'confidence': 0.0,
                                    'is_anomaly': True, 'best_image': None,
                                    'best_score': 0.0, 'frame_classified': frame_count
                                }
                                self.track_features.pop(tid, None)
                        else:
                            class_name = "?"
                            self.classified_tracks[tid] = {
                                'class_name': class_name, 'confidence': 0.0,
                                'is_anomaly': True, 'best_image': None,
                                'best_score': 0.0, 'frame_classified': frame_count
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
                                data['frame_classified'] = frame_count

                    annotated = self._draw_track_box(annotated, bbox, tid, class_name)

                self.frame_processed.emit(annotated)
            else:
                self.frame_processed.emit(frame)

            total = self.video_reader.get_frame_count()
            self.progress_updated.emit(frame_count, total)

            elapsed = time.time() - loop_start
            sleep_time = frame_delay - elapsed
            if sleep_time > 0:
                self.msleep(int(sleep_time * 1000))

        for tid, data in self.classified_tracks.items():
            if data['best_image'] is not None and data['class_name'] not in ("?", "Incertain"):
                self.duplicate_checker.save_image(
                    image=data['best_image'],
                    class_name=data['class_name'],
                    video_name=f"{self.video_name}_track{tid}",
                    frame_idx=data['frame_classified'],
                    confidence=data['confidence']
                )

        self.finished.emit()

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

    def stop(self):
        self._is_running = False