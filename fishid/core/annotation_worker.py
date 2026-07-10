# core/annotation_worker.py
import threading
import numpy as np
from fishid.core.tracker_wrapper import BoTSORTWrapper

class AnnotationWorker(threading.Thread):
    """Thread qui traite les frames en arrière-plan et stocke les annotations."""

    def __init__(self, video_reader, object_detector, feature_extractor,
                anomaly_detector, classifier, duplicate_checker,
                frame_interval=1, conf_threshold=0.2,
                anomaly_threshold=0.9, mode="fish"):
        super().__init__(daemon=True)
        self.video_reader = video_reader
        self.object_detector = object_detector
        self.extractor = feature_extractor
        self.anomaly_detector = anomaly_detector
        self.classifier = classifier
        self.duplicate_checker = duplicate_checker
        self.frame_interval = frame_interval
        self.conf_threshold = conf_threshold
        self.anomaly_threshold = anomaly_threshold
        self.mode = mode
        self._stop_event = threading.Event()
        self.classified_tracks = {}   # pour éviter de reclassifier
        self.track_features = {}
        self.reid_interval = 10
        self.reid_similarity_threshold = 0.7
        self.frame_count = 0

        # Dictionnaire partagé : frame_idx -> liste d'annotations
        self.annotations = {}
        self.lock = threading.Lock()

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

    def run(self):
        while not self._stop_event.is_set():
            ret, frame = self.video_reader.read_frame_safe()
            if not ret or frame is None:
                continue
            self.frame_count += 1
            if self.frame_count % self.frame_interval != 0:
                continue

            # Détection + tracking + classification + anomaly (comme avant)
            # ... (le même traitement que dans ProcessingWorker)
            # Stocker les annotations dans self.annotations[self.frame_count] = liste de dicts

            # Exemple simplifié (à compléter avec votre logique exacte)
            detections = self.object_detector.detect_objects(frame)
            tracks = self.tracker.update(detections, frame)
            frame_annotations = []
            for trk in tracks:
                bbox = trk['bbox']
                tid = trk['track_id']
                # classification / anomalie...
                class_name = "..."   # placeholder
                frame_annotations.append({
                    'bbox': bbox,
                    'track_id': tid,
                    'class_name': class_name,
                })
            with self.lock:
                self.annotations[self.frame_count] = frame_annotations

    def stop(self):
        self._stop_event.set()