# fishid/ui/camera_dialog.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from fishid.utils import resource_path
from PySide6.QtGui import QPixmap, QIcon

class CameraDialog(QDialog):
    def __init__(self, parent, prefill_url="", qr_pixmap=None, info_text=""):
        super().__init__(parent)
        from fishid.utils import add_logo_to_dialog
        # dans __init__ :
        add_logo_to_dialog(self)

        self.setWindowTitle("Connexion à une caméra")
        self.setMinimumWidth(450)
        layout = QVBoxLayout(self)

        if info_text:
            info_label = QLabel(info_text)
            info_label.setWordWrap(True)
            layout.addWidget(info_label)

        if qr_pixmap and not qr_pixmap.isNull():
            qr_label = QLabel()
            qr_label.setPixmap(qr_pixmap)
            qr_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(qr_label)

        self.url_edit = QLineEdit(prefill_url)
        self.url_edit.setPlaceholderText("http://192.168.1.45:8080/video")
        layout.addWidget(self.url_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Connecter")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_url(self):
        return self.url_edit.text().strip()