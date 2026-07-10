# ui/viewer_widget.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMenu
from PySide6.QtGui import QPixmap, QImage, QResizeEvent
from PySide6.QtCore import Qt, Signal
import numpy as np
import cv2
from fishid.ui.spinner_widget import ElegantSpinner

class ViewerWidget(QWidget):
    """Zone centrale d'affichage de la vidéo avec menu contextuel."""

    # Signaux pour le menu contextuel
    capture_requested = Signal()
    mode_change_requested = Signal(str)        # 'fish' ou 'waste'
    toggle_tracking_requested = Signal()
    toggle_annotations_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("viewerWidget")
        self._current_pixmap = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        self.label = QLabel("Aucune vidéo chargée")
        self.label.setObjectName("viewerLabel")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setMinimumSize(640, 480)
        self.label.setScaledContents(False)

        layout.addWidget(self.label)

        # Activer le menu contextuel
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos):
        """Affiche le menu contextuel au clic droit."""
        menu = QMenu(self)
        menu.setStyleSheet(self.styleSheet())  # hérite du thème

        # Action Capturer
        capture_action = menu.addAction("📷 Capturer cette frame")
        capture_action.triggered.connect(self.capture_requested.emit)

        menu.addSeparator()

        # Sous‑menu Mode
        mode_menu = menu.addMenu("🔀 Mode")
        fish_action = mode_menu.addAction("🐟 Poissons")
        fish_action.triggered.connect(lambda: self.mode_change_requested.emit("fish"))
        waste_action = mode_menu.addAction("🗑️ Déchets")
        waste_action.triggered.connect(lambda: self.mode_change_requested.emit("waste"))

        menu.addSeparator()

        # Toggle Tracking
        tracking_action = menu.addAction("👁 Activer/Désactiver le tracking")
        tracking_action.triggered.connect(self.toggle_tracking_requested.emit)

        # Toggle Annotations
        annotations_action = menu.addAction("🏷 Afficher/Masquer les annotations")
        annotations_action.triggered.connect(self.toggle_annotations_requested.emit)

        menu.exec(self.mapToGlobal(pos))

    def set_frame(self, frame):
        """
        Met à jour l'image affichée.
        Accepte soit un QPixmap, soit un numpy array (BGR).
        """
        if isinstance(frame, np.ndarray):
            self._current_pixmap = self._numpy_to_pixmap(frame)
        elif isinstance(frame, QPixmap):
            self._current_pixmap = frame
        else:
            return
        self._update_display()

    def _numpy_to_pixmap(self, frame: np.ndarray) -> QPixmap:
        if frame is None:
            return QPixmap()
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qt_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        return QPixmap.fromImage(qt_img)

    def _update_display(self):
        if self._current_pixmap and not self._current_pixmap.isNull():
            scaled = self._current_pixmap.scaled(
                self.label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.label.setPixmap(scaled)
            self.label.setText("")
        else:
            self.label.setText("Aucune vidéo chargée")

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self._update_display()
        
    def show_spinner(self, text="Pré-traitement vidéo..."):
        if not hasattr(self, 'spinner'):
            from fishid.ui.spinner_widget import ElegantSpinner
            self.spinner = ElegantSpinner(self, size=60, color="#89B4FA", text=text)
        self.spinner.set_text(text)
        self.spinner.start()
        self.spinner.move(self.width() // 2 - 30, self.height() // 2 - 45)

    def hide_spinner(self):
        if hasattr(self, 'spinner'):
            self.spinner.stop()