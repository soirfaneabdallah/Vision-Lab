# fishid/core/qt_video_reader.py
import numpy as np
from PySide6.QtCore import QUrl, QObject, Signal, Slot, QTimer
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QVideoSink
from PySide6.QtGui import QImage
import cv2


class QtVideoReader(QObject):
    """
    Lecteur vidéo basé sur QMediaPlayer (fichiers locaux, avec son).
    Signaux :
        frame_ready(frame_bgr, frame_idx)
        video_opened(nom, total_frames, fps)
        playback_finished()
        error_occurred(message)
        progress_updated(current_frame, total_frames, fps)
    """

    frame_ready       = Signal(object, int)
    video_opened      = Signal(str, int, float)
    playback_finished = Signal()
    error_occurred    = Signal(str)
    progress_updated  = Signal(int, int, float)  # (current, total, fps)

    # ──────────────────────────────────────────────────────────────────
    def __init__(self):
        super().__init__()

        # ── Lecteur multimédia Qt ──
        self.player       = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.video_sink   = QVideoSink()

        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoSink(self.video_sink)
        self.audio_output.setVolume(0.5)

        # ── État interne ──
        self.current_frame_idx = 0
        self.total_frames      = 0
        self.fps               = 30.0
        self.video_path        = ""
        self.is_playing        = False
        self._media_loaded     = False
        self._seeking          = False   # verrou pendant un seek
        self._last_position_ms = -1      # anti-spam des émissions
        
        self._media_loaded = False
        # ── Connexions Qt ──
        self.video_sink.videoFrameChanged.connect(self._on_frame_received)
        self.player.playbackStateChanged.connect(self._on_state_changed)
        self.player.errorOccurred.connect(self._on_error)
        self.player.mediaStatusChanged.connect(self._on_media_status)
        self.player.positionChanged.connect(self._on_position_changed)

        # ── Timer de progression (250 ms, démarré/arrêté avec la lecture) ──
        self._progress_timer = QTimer(self)
        self._progress_timer.setInterval(250)
        self._progress_timer.timeout.connect(self._emit_progress)

    # ──────────────────────────────────────────────────────────────────
    # API publique
    # ──────────────────────────────────────────────────────────────────

    def open_media(self, file_path: str) -> bool:
        self.stop()
        self.video_path        = file_path
        self._media_loaded     = False
        self.current_frame_idx = 0
        self._last_position_ms = -1
        self.player.setSource(QUrl.fromLocalFile(file_path))
        return True

    def play(self):
        self.player.play()
        self.is_playing = True
        self._progress_timer.start()

    def pause(self):
        self.player.pause()
        self.is_playing = False
        self._progress_timer.stop()
        self._emit_progress()           # snapshot immédiat à la pause

    def stop(self):
        self.player.stop()
        self.is_playing        = False
        self.current_frame_idx = 0
        self._last_position_ms = -1
        self._progress_timer.stop()

    def close(self):
        self.stop()
        self.player.setSource(QUrl())

    def seek(self, position_ms: int):
        """
        Seek à la position donnée en ms.
        Émet immédiatement progress_updated pour synchroniser le slider.
        """
        if not self._media_loaded:
            return
        duration    = self.player.duration()
        position_ms = max(0, min(position_ms, duration if duration > 0 else position_ms))

        self._seeking = True
        self.player.setPosition(position_ms)
        self._seeking = False

        # Mise à jour immédiate du slider
        self._emit_progress_at(position_ms)

    def set_volume(self, volume: float):
        self.audio_output.setVolume(max(0.0, min(1.0, volume)))

    def set_muted(self, muted: bool):
        self.audio_output.setMuted(muted)

    @property
    def duration_ms(self) -> int:
        return self.player.duration()

    @property
    def position_ms(self) -> int:
        return self.player.position()

    # ──────────────────────────────────────────────────────────────────
    # Calcul et émission de la progression
    # ──────────────────────────────────────────────────────────────────

    def _frame_from_ms(self, position_ms: int) -> int:
        if self.fps <= 0:
            return 0
        return max(0, min(int(position_ms / 1000.0 * self.fps), self.total_frames))

    def _emit_progress(self):
        """Appelé par le timer : émet uniquement si la position a changé."""
        if self.total_frames <= 0:
            return
        pos_ms = self.player.position()
        if pos_ms == self._last_position_ms:
            return
        self._last_position_ms = pos_ms
        self.progress_updated.emit(
            self._frame_from_ms(pos_ms),
            self.total_frames,
            self.fps
        )

    def _emit_progress_at(self, position_ms: int):
        """Émet la progression pour une position donnée (seek immédiat)."""
        if self.total_frames <= 0:
            return
        self._last_position_ms = position_ms
        self.progress_updated.emit(
            self._frame_from_ms(position_ms),
            self.total_frames,
            self.fps
        )

    # ──────────────────────────────────────────────────────────────────
    # Slots Qt (privés)
    # ──────────────────────────────────────────────────────────────────

    @Slot(int)
    def _on_position_changed(self, position_ms: int):
        """N'émet que pendant un seek pour une réactivité immédiate."""
        if self._seeking:
            self._emit_progress_at(position_ms)

    @Slot(QMediaPlayer.MediaStatus)
    def _on_media_status(self, status: QMediaPlayer.MediaStatus):
        if status == QMediaPlayer.MediaStatus.LoadedMedia and not self._media_loaded:
            self._media_loaded     = True
            duration_ms            = self.player.duration()
            self.fps               = 30.0
            self.total_frames      = int(duration_ms / 1000.0 * self.fps) if duration_ms > 0 else 0
            self.current_frame_idx = 0
            self._last_position_ms = -1

            name = self.video_path.replace("\\", "/").split("/")[-1]
            self.video_opened.emit(name, self.total_frames, self.fps)
            # Position initiale → slider à 0
            self.progress_updated.emit(0, self.total_frames, self.fps)

    @Slot(QMediaPlayer.PlaybackState)
    def _on_state_changed(self, state: QMediaPlayer.PlaybackState):
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self._progress_timer.stop()
            self.is_playing = False
            if self.total_frames > 0:
                self.progress_updated.emit(self.total_frames, self.total_frames, self.fps)
            self.playback_finished.emit()

        elif state == QMediaPlayer.PlaybackState.PlayingState:
            self.is_playing = True
            self._progress_timer.start()

        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.is_playing = False
            self._progress_timer.stop()
            self._emit_progress()

    @Slot(QMediaPlayer.Error, str)
    def _on_error(self, error, error_string: str):
        self.error_occurred.emit(f"Erreur média : {error_string}")

    @Slot()
    def _on_frame_received(self, frame):
        """Convertit QVideoFrame → NumPy BGR et émet frame_ready."""
        if not frame.isValid():
            return
        image = frame.toImage()
        if image.isNull():
            return
        image = image.convertToFormat(QImage.Format.Format_RGBA8888)
        w, h  = image.width(), image.height()
        arr   = np.frombuffer(image.bits(), dtype=np.uint8).reshape((h, w, 4)).copy()
        bgr   = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
        self.frame_ready.emit(bgr, self.current_frame_idx)
        self.current_frame_idx += 1
