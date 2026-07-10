# ui/status_bar.py
from PySide6.QtWidgets import QStatusBar, QLabel, QProgressBar, QHBoxLayout, QWidget
from PySide6.QtCore import Qt


class AppStatusBar(QStatusBar):
    """Barre de statut avec message, progression et version."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statusBar")

        self.message_label = QLabel("🔵 Prêt. Aucune vidéo chargée.")
        self.message_label.setObjectName("statusMessage")

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.setFixedHeight(16)
        self.progress_bar.setVisible(False)

        self.version_label = QLabel("Vision Lab v1.0")
        self.version_label.setObjectName("statusVersion")

        self.addWidget(self.message_label, 1)
        self.addPermanentWidget(self.progress_bar)
        self.addPermanentWidget(self.version_label)

    def set_busy(self, message: str):
        self.message_label.setText(message)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indéterminé

    def set_progress(self, value: int, max_val: int = 100):
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, max_val)
        self.progress_bar.setValue(value)

    def set_ready(self, message: str = "🔵 Prêt"):
        self.message_label.setText(message)
        self.progress_bar.setVisible(False)