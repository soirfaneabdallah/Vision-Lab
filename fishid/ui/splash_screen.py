# fishid/ui/splash_screen.py
from PySide6.QtWidgets import QSplashScreen, QApplication
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QBrush
import math
from fishid.utils import find_asset_path

class SplashScreen(QSplashScreen):
    def __init__(self):
        # Chargement du logo
        logo_path = find_asset_path("assets/logos/icon3.png")
        if logo_path is None:
            pixmap = QPixmap(500, 400)
            pixmap.fill(QColor("#0B0E14"))
        else:
            pixmap = QPixmap(logo_path)

        super().__init__(pixmap)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setFixedSize(500, 400)

        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._timer.start(40)          # 25 fps

        self._message = "Chargement des modèles..."
        self._version = "Vision Lab v1.0"

    def _rotate(self):
        self._angle = (self._angle + 4) % 360
        self.repaint()

    def drawContents(self, painter):
        painter.setRenderHint(QPainter.Antialiasing)

        # Fond sombre si le logo est petit
        if self.pixmap().width() < 300:
            painter.fillRect(self.rect(), QColor("#0B0E14"))
        else:
            painter.fillRect(self.rect(), QColor(11, 14, 20, 120))

        # Logo centré
        logo_rect = self.pixmap().rect()
        logo_x = (self.width() - logo_rect.width()) // 2
        logo_y = (self.height() - logo_rect.height()) // 2 - 30
        painter.drawPixmap(logo_x, logo_y, self.pixmap())

        # --- Spinner (remonté) ---
        cx = self.width() // 2
        cy = self.height() // 2 - 10        # était +60, maintenant -20 => remonté de 80 pixels
        radius = 28
        n = 12

        for i in range(n):
            angle = math.radians(self._angle + i * (360 / n))
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)

            progress = i / n
            opacity = 1.0 - progress * 0.8
            size = 6 - progress * 3

            color = QColor(137, 180, 250, int(255 * opacity))
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(x, y), size, size)

        # --- Message ---
        message_y = self.height() - 130
        painter.setPen(QColor("#CDD6F4"))
        painter.setFont(QFont("Segoe UI", 12, QFont.Bold, italic=True))
        painter.drawText(0, message_y, self.width(), 20,
                         Qt.AlignHCenter | Qt.AlignVCenter, self._message)

        # --- Version ---
        version_y = self.height() - 110
        painter.setPen(QColor("#6C7086"))
        painter.setFont(QFont("Segoe UI", 9,QFont.Bold, italic=True))
        painter.drawText(0, version_y, self.width(), 16,
                         Qt.AlignHCenter | Qt.AlignVCenter, self._version)

    def set_message(self, msg):
        self._message = msg
        self.repaint()
        QApplication.processEvents()