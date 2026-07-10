# core/worker.py
from PySide6.QtCore import QThread, Signal
import numpy as np
import time


class DetectionWorker(QThread):
    """
    Thread de détection thread-safe.
    Utilise read_frame_safe() pour éviter les conflits avec le thread principal.
    """

    frame_processed = Signal(np.ndarray)
    detections_ready = Signal(list)
    progress_updated = Signal(int, int)
    finished = Signal()
    error_occurred = Signal(str)

    def __init__(self, video_reader, detector, frame_interval: int = 5):
        super().__init__()
        self.video_reader = video_reader
        self.detector = detector
        self.frame_interval = frame_interval
        self._is_running = False
        self._paused = False

    def run(self):
        self._is_running = True
        self._paused = False
        frame_count = 0
        
        try:
            while self._is_running:
                if self._paused:
                    self.msleep(100)
                    continue

                # Lecture thread-safe
                ret, frame = self.video_reader.read_frame_safe()
                
                if not ret or frame is None:
                    break  # Fin de la vidéo

                frame_count += 1
                current_pos = frame_count  # Approximation (assez proche)

                # Traiter 1 frame sur N
                if frame_count % self.frame_interval == 0:
                    try:
                        annotated, detections = self.detector.detect_and_draw(frame)
                        self.frame_processed.emit(annotated)
                        if detections:
                            self.detections_ready.emit(detections)
                    except Exception as e:
                        self.error_occurred.emit(f"Erreur détection : {e}")
                        # Continuer avec la frame brute
                        self.frame_processed.emit(frame)
                else:
                    self.frame_processed.emit(frame)

                total = self.video_reader.get_frame_count()
                self.progress_updated.emit(current_pos, total)
                
                # Petit délai pour ne pas surcharger
                self.msleep(1)

        except Exception as e:
            self.error_occurred.emit(f"Erreur worker : {e}")
        finally:
            self._is_running = False
            self.finished.emit()

    def stop(self):
        self._is_running = False

    def pause_processing(self):
        self._paused = True

    def resume_processing(self):
        self._paused = False