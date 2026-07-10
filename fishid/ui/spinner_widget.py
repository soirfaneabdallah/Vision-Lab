# fishid/ui/spinner_widget.py
from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtCore import Qt, QTimer, QRect, QPoint
from PySide6.QtGui import QPainter, QPen, QColor, QConicalGradient, QBrush, QLinearGradient


class ElegantSpinner(QWidget):
    """Spinner circulaire parfait avec animation fluide et design élégant."""


    def __init__(self, parent=None, size=60, color="#89B4FA", text="Pré-traitement vidéo..."):
        super().__init__(parent)
        self.setFixedSize(size, size + 35)
        self.spinner_size = size
        self.color = QColor(color)
        self.text = text
        self.angle = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self._rotate)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")


        # Label de texte avec style élégant
        self.label = QLabel(text, self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet(f"""
            color: {color};
            font-size: 12px;
            font-weight: 600;
            background-color: transparent;
            letter-spacing: 0.5px;
        """)
        
        # Positionner le texte parfaitement centré sous le spinner
        text_height = 20
        self.label.setGeometry(
            0, 
            size + 5, 
            size, 
            text_height
        )
        
        self.hide()


    def _rotate(self):
        """Animation fluide avec incrément optimisé."""
        self.angle = (self.angle + 8) % 360
        self.update()


    def set_text(self, text):
        """Change le texte affiché sous le spinner."""
        self.text = text
        self.label.setText(text)


    def start(self):
        """Démarre l'animation du spinner."""
        self.show()
        self.angle = 0
        self.timer.start(16)  # ~60 FPS


    def stop(self):
        """Arrête l'animation et cache le spinner."""
        self.timer.stop()
        self.hide()


    def paintEvent(self, event):
        """Rendu du spinner circulaire élégant avec gradient."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)


        # Centre et rectangle du cercle
        center = self.spinner_size // 2
        rect = QRect(
            5, 
            5, 
            self.spinner_size - 10, 
            self.spinner_size - 10
        )


        # Gradient conique pour effet de rotation élégant
        gradient = QConicalGradient(center, center, self.angle)
        gradient.setColorAt(0.0, self.color)
        gradient.setColorAt(0.25, self.color.lighter(130))
        gradient.setColorAt(0.5, self.color.lighter(180))
        gradient.setColorAt(0.75, self.color.lighter(120))
        gradient.setColorAt(1.0, QColor(0, 0, 0, 0))


        # Pénne avec style élégant
        pen = QPen()
        pen.setBrush(QBrush(gradient))
        pen.setWidth(5)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)


        # Arc de cercle avec angle dynamique
        start_angle = self.angle * 16
        span_angle = 240 * 16  # 240° pour un effet plus moderne
        painter.drawArc(rect, start_angle, span_angle)


        # Ajouter un point lumineux à la tête du spinner
        painter.setPen(Qt.NoPen)
        head_angle = self.angle + (240 / 2)
        head_x = center + (rect.width() / 2 - 2.5) * self._cos(head_angle)
        head_y = center + (rect.height() / 2 - 2.5) * self._sin(head_angle)
        
        # Point lumineux avec dégradé
        head_gradient = QConicalGradient(head_x, head_y, 8)
        head_gradient.setColorAt(0.0, self.color.lighter(250))
        head_gradient.setColorAt(1.0, self.color.lighter(100))
        
        painter.setBrush(QBrush(head_gradient))
        painter.drawEllipse(QPoint(head_x, head_y), 4, 4)


    def _cos(self, angle_deg):
        """Calcul cosinus en degrés."""
        import math
        return math.cos(angle_deg * math.pi / 180)


    def _sin(self, angle_deg):
        """Calcul sinus en degrés."""
        import math
        return math.sin(angle_deg * math.pi / 180)