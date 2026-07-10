# fishid/core/video_player_with_overlay.py
from PySide6.QtCore import QUrl, QObject, Signal, Slot, Qt
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QBrush
from PySide6.QtWidgets import QWidget, QVBoxLayout


class OverlayWidget(QWidget):
    """Widget transparent qui affiche les annotations par-dessus la vidéo."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # laisser les clics passer
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.annotations = []  # liste de (bbox, text, color)

    def set_annotations(self, annotations):
        """annotations : liste de dict avec 'bbox', 'text', 'color'"""
        self.annotations = annotations
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        for ann in self.annotations:
            bbox = ann['bbox']
            x1, y1, x2, y2 = bbox
            color = QColor(ann['color'])
            painter.setPen(QPen(color, 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(x1, y1, x2 - x1, y2 - y1)
            painter.setPen(QPen(Qt.white, 1))
            painter.setBrush(QBrush(color))
            painter.drawText(x1, y1 - 5, x2 - x1, 20, Qt.AlignCenter, ann['text'])


class VideoPlayerWithOverlay(QObject):
    frame_for_analysis = Signal(object, int)  # frame (numpy), frame_idx
    playback_finished = Signal()
    error_occurred = Signal(str)
    video_opened = Signal(str, int, float)  # name, total_frames, fps

    def __init__(self, parent_widget):
        super().__init__()
        self.parent_widget = parent_widget
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.video_widget = QVideoWidget()
        self.overlay = OverlayWidget(self.video_widget)

        # Layout pour superposer l'overlay
        layout = QVBoxLayout(self.video_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.overlay)

        self.player.setVideoOutput(self.video_widget)
        self.player.playbackStateChanged.connect(self._on_state_changed)
        self.player.errorOccurred.connect(self._on_error)
        self.player.mediaStatusChanged.connect(self._on_media_status)

        self.current_frame_idx = 0
        self.total_frames = 0
        self.fps = 30.0
        self.video_path = ""
        self.is_playing = False
        self._media_loaded = False

        self.audio_output.setVolume(0.8)

    def get_widget(self):
        """Retourne le widget vidéo à placer dans l'interface."""
        return self.video_widget

    def open_media(self, file_path):
        self.stop()
        self.video_path = file_path
        url = QUrl.fromLocalFile(file_path)
        self.player.setSource(url)
        self._media_loaded = False
        self.current_frame_idx = 0
        return True

    def set_volume(self, volume):
        self.audio_output.setVolume(volume)

    def set_muted(self, muted):
        self.audio_output.setMuted(muted)

    def play(self):
        self.player.play()
        self.is_playing = True

    def pause(self):
        self.player.pause()
        self.is_playing = False

    def stop(self):
        self.player.stop()
        self.is_playing = False
        self.current_frame_idx = 0

    def seek(self, position_ms):
        self.player.setPosition(position_ms)

    def close(self):
        self.player.stop()
        self.player.setSource(QUrl())

    def update_annotations(self, annotations):
        """Appelé par le contrôleur pour afficher les détections."""
        self.overlay.set_annotations(annotations)

    @Slot(QMediaPlayer.MediaStatus)
    def _on_media_status(self, status):
        if status == QMediaPlayer.LoadedMedia and not self._media_loaded:
            self._media_loaded = True
            duration_ms = self.player.duration()
            self.fps = 30.0
            self.total_frames = int(duration_ms / 1000 * self.fps) if duration_ms > 0 else 0
            name = self.video_path.split('/')[-1]
            self.video_opened.emit(name, self.total_frames, self.fps)

    @Slot(QMediaPlayer.PlaybackState)
    def _on_state_changed(self, state):
        if state == QMediaPlayer.StoppedState:
            self.playback_finished.emit()
            self.is_playing = False
        elif state == QMediaPlayer.PlayingState:
            self.is_playing = True
        elif state == QMediaPlayer.PausedState:
            self.is_playing = False

    @Slot(QMediaPlayer.Error, str)
    def _on_error(self, error, error_string):
        self.error_occurred.emit(f"Erreur média: {error_string}")