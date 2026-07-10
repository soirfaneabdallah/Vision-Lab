# core/video_reader.py
import cv2
import time
import subprocess
import cv2
import numpy as np
import threading
import queue
from PySide6.QtCore import QObject, Signal, QTimer, QMutex, QMutexLocker
from PySide6.QtGui import QImage, QPixmap
from .qt_video_reader import QtVideoReader
import os
import numpy as np
os.environ["OPENCV_FFMPEG_LOGLEVEL"] = "-8"


class VideoReader(QObject):
    """Lit une vidéo, une webcam, un flux réseau ou un serveur distant.
       Émet chaque frame brute (numpy) avec son index."""


    frame_ready = Signal(np.ndarray, int)
    progress_updated = Signal(int, int, float)
    playback_finished = Signal()
    video_opened = Signal(str, int, float)
    error_occurred = Signal(str)
    
    #  SIGNAUX DE BUFFERING POUR LE SPINNER
    buffering_started = Signal()
    buffering_finished = Signal()


    def __init__(self, parent=None):
        super().__init__(parent)
        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._next_frame)
        
        self.total_frames = 0
        self.current_frame_idx = 0
        self.fps = 0.0
        self.video_path = ""
        self.is_playing = False
        self.timer_interval = 33


        self._mutex = QMutex()
        self.remote_server = None


    # ------------------------------------------------------------------
    def load_video(self, path):
        # ⭐ Chemin absolu dès le départ
        abs_path = os.path.abspath(path)
        self._stop_completely()
        self._fallback_attempted = False
        self.current_reader = self.video_reader_file
        self.current_source_name = os.path.basename(abs_path)
        self._connect_signals(self.current_reader)

        self.current_reader.error_occurred.connect(self._on_qt_reader_error)
        self.current_reader.open_media(abs_path)   # ← utilisation du chemin absolu

        # Timer de timeout (5 secondes pour laisser le temps)
        if self._load_timeout is not None:
            self._load_timeout.stop()
        self._load_timeout = QTimer()
        self._load_timeout.setSingleShot(True)
        self._load_timeout.timeout.connect(lambda: self._check_media_loaded(abs_path))
        self._load_timeout.start(5000)  # ← 5s au lieu de 3s

        return True


    def open_webcam(self, camera_id: int = 0):
        self.close()
        self.remote_server = None
        with QMutexLocker(self._mutex):
            self.cap = cv2.VideoCapture(camera_id)
            if not self.cap.isOpened():
                self.error_occurred.emit(f"Impossible d'ouvrir la webcam {camera_id}")
                return False
            self.total_frames = 1000000
            self.fps = 30.0
            self.timer_interval = 33
            self.video_path = f"Webcam {camera_id}"
            ret, frame = self.cap.read()
            if ret:
                # ⭐ DÉMARRE LE BUFFERING (spinner) pour webcam
                self.buffering_started.emit()
                self.frame_ready.emit(frame.copy(), 0)
        self.video_opened.emit(f"Webcam {camera_id}", self.total_frames, self.fps)
        return True


  

    def open_ip_camera(self, url: str) -> bool:
        """Ouvre un flux vidéo depuis une caméra IP avec ffmpeg."""
        self.close()
        
        try:
            # Commande ffmpeg avec header ngrok
            cmd = [
                'ffmpeg',
                '-user_agent', 'Mozilla/5.0',
                '-headers', 'ngrok-skip-browser-warning: 1',
                '-i', url,
                '-f', 'image2pipe',
                '-pix_fmt', 'bgr24',
                '-vcodec', 'rawvideo',
                '-an',
                '-'
            ]
            
            self.process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.DEVNULL,
                bufsize=10**8
            )
            
            # Démarrer un thread pour lire les frames
            self.running = True
            self.ffmpeg_buffer = b''
            self.frame_queue = queue.Queue(maxsize=30)
            
            def read_ffmpeg_frames():
                frame_size = 640 * 480 * 3  # à adapter
                while self.running:
                    raw = self.process.stdout.read(frame_size)
                    if len(raw) != frame_size:
                        continue
                    frame = np.frombuffer(raw, dtype=np.uint8).reshape((480, 640, 3))
                    if self.frame_queue.full():
                        self.frame_queue.get()
                    self.frame_queue.put(frame)
            
            self.ffmpeg_thread = threading.Thread(target=read_ffmpeg_frames, daemon=True)
            self.ffmpeg_thread.start()
            
            self.video_path = url
            self.fps = 30
            self.total_frames = 1000000
            self.is_playing = False
            self.frame_width = 640
            self.frame_height = 480
            self.is_ffmpeg = True
            
            return True
        
        except Exception as e:
            print(f"Erreur ffmpeg: {e}")
            return False


    def set_remote_source(self, remote_server):
        self.close()
        self.remote_server = remote_server
        if remote_server:
            self.video_path = "Smartphone"
            self.total_frames = 1000000
            self.fps = 30.0
            self.timer_interval = 33
            # ⭐ DÉMARRE LE BUFFERING (spinner) pour remote
            self.buffering_started.emit()
            self.video_opened.emit("Smartphone", self.total_frames, self.fps)
        else:
            self.video_path = ""
            self.total_frames = 0
            self.fps = 0.0


    # ------------------------------------------------------------------
    def play(self):
        if self.is_playing:
            return
        if self.cap or self.remote_server:
            self.is_playing = True
            self.timer.start(self.timer_interval)


    def pause(self):
        self.is_playing = False
        self.timer.stop()


    def stop(self):
        self.pause()
        if self.remote_server:
            frame = self.remote_server.get_frame()
            if frame is not None:
                self.frame_ready.emit(frame.copy(), self.current_frame_idx)
            self.progress_updated.emit(0, self.total_frames, self.fps)
        elif self.cap:
            with QMutexLocker(self._mutex):
                if self.total_frames < 1000000:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.current_frame_idx = 0
                    ret, frame = self.cap.read()
                    if ret:
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        self.frame_ready.emit(frame.copy(), 0)
                else:
                    ret, frame = self.cap.read()
                    if ret:
                        self.frame_ready.emit(frame.copy(), self.current_frame_idx)
                self.progress_updated.emit(0, self.total_frames, self.fps)


    def seek(self, frame_idx):
        """
        Avance ou recule la vidéo à la frame demandée.
        Le son et l'image sont synchronisés.
        """
        if self.current_reader is None:
            return
        
        # Arrêter l'affichage temporairement
        if self.display_timer and self.display_timer.isActive():
            self.display_timer.stop()
        
        # Vider le buffer pour éviter les conflits
        self.frame_buffer.clear()
        self.current_frame_idx = frame_idx
        
        # Effectuer le seek
        if isinstance(self.current_reader, QtVideoReader):
            if self.fps > 0:
                ms = int(frame_idx / self.fps * 1000)
                self.current_reader.seek(ms)
        else:
            self.current_reader.seek(frame_idx)
        
        #  Forcer l'affichage immédiat
        if self.last_annotated_frame is not None:
            self.frame_ready.emit(self.last_annotated_frame)
        
        # Redémarrer l'affichage si nécessaire
        if not self.buffering and self.frame_buffer:
            self._start_display_timer()

    # ------------------------------------------------------------------
    def read_frame_safe(self):
        if self.remote_server:
            frame = self.remote_server.get_frame()
            if frame is not None:
                return True, frame.copy()
            return False, None
        else:
            with QMutexLocker(self._mutex):
                if not self.cap:
                    return False, None
                ret, frame = self.cap.read()
                if ret:
                    return True, frame.copy()
                return False, None


    def get_current_frame(self):
        if self.remote_server:
            frame = self.remote_server.get_frame()
            return frame.copy() if frame is not None else None
        with QMutexLocker(self._mutex):
            if not self.cap:
                return None
            ret, frame = self.cap.read()
            if ret:
                current = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, current - 1)
                return frame.copy()
            return None


    def get_frame_count(self):
        return self.total_frames


    def close(self):
        self.pause()
        with QMutexLocker(self._mutex):
            if self.cap:
                self.cap.release()
                self.cap = None
        self.remote_server = None
        self.total_frames = 0
        self.current_frame_idx = 0


    # ------------------------------------------------------------------
    def _next_frame(self):
        if self.remote_server:
            frame = self.remote_server.get_frame()
            if frame is not None:
                self.current_frame_idx += 1
                self.frame_ready.emit(frame.copy(), self.current_frame_idx)
                self.progress_updated.emit(self.current_frame_idx, self.total_frames, self.fps)
            return


        with QMutexLocker(self._mutex):
            if not self.cap or not self.is_playing:
                return
            ret, frame = self.cap.read()
            if not ret:
                if self.total_frames < 1000000:
                    self.pause()
                    self.playback_finished.emit()
                return
            self.current_frame_idx = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            self.frame_ready.emit(frame.copy(), self.current_frame_idx)
            self.progress_updated.emit(self.current_frame_idx, self.total_frames, self.fps)