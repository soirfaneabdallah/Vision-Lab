# fishid/ui/header_bar.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy
from PySide6.QtCore import Qt, QPoint, QSize
from PySide6.QtGui import QMouseEvent, QColor, QPixmap, QIcon, QPalette
from PySide6.QtWidgets import QApplication
import sys, os
from fishid.utils import resource_path, load_svg_icon, load_app_icon


class HeaderBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("titleBar")
        self._parent = parent
        self._drag_pos = None
        self._current_theme = "dark"  # thème par défaut
        self._icon_color = QColor("#FFFFFF")  # couleur par défaut

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(8)

        # --- Logo agrandi (40x40) ---
        self.logo_label = QLabel()
        app_icon = load_app_icon()   # icône multi‑taille
        if not app_icon.isNull():
            # Extraire un pixmap 40x40 de l'icône
            pixmap = app_icon.pixmap(40, 40)
            self.logo_label.setPixmap(pixmap)
        else:
            # fallback texte
            self.logo_label.setText("VL")
            self.logo_label.setStyleSheet("color: #89B4FA; font-weight: bold; font-size: 16px;")
        self.logo_label.setFixedSize(40, 40)
        layout.addWidget(self.logo_label)

        # --- Titre et sous‑titre ---
        title_label = QLabel("Vision Lab")
        title_label.setObjectName("titleLabel")
        layout.addWidget(title_label)

        subtitle = QLabel("·  Identification intelligente")
        subtitle.setObjectName("titleSubLabel")
        subtitle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(subtitle)

        # --- Boutons de contrôle de la fenêtre ---
        self.btn_min = QPushButton()
        self.btn_min.setObjectName("windowMinButton")
        self.btn_min.setFixedSize(35, 30)
        self.btn_min.clicked.connect(self._parent.showMinimized)

        self.btn_max = QPushButton()
        self.btn_max.setObjectName("windowMaxButton")
        self.btn_max.setFixedSize(35, 30)
        self.btn_max.clicked.connect(self._toggle_maximize)

        self.btn_close = QPushButton()
        self.btn_close.setObjectName("windowCloseButton")
        self.btn_close.setFixedSize(35, 30)
        self.btn_close.clicked.connect(self._parent.close)

        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_max)
        layout.addWidget(self.btn_close)

        # --- Initialiser les icônes avec le thème sombre par défaut ---
        self._update_button_icons()

        # --- Surveiller le changement de thème ---
        QApplication.instance().paletteChanged.connect(self._on_palette_changed)

    def _get_theme_colors(self):
        """Récupérer les couleurs selon le thème actuel"""
        if self._current_theme == "dark":
            return {
                "icon_color": QColor("#FFFFFF"),
                "icon_hover": QColor("#E0E6F0"),
                "close_hover": QColor("#F38BA8"),
                "close_hover_icon": QColor("#0B0E14")
            }
        else:  # light
            return {
                "icon_color": QColor("#64748B"),
                "icon_hover": QColor("#1E293B"),
                "close_hover": QColor("#DC3545"),
                "close_hover_icon": QColor("#FFFFFF")
            }

    def _update_button_icons(self):
        """Actualiser les icônes des boutons selon le thème"""
        colors = self._get_theme_colors()
        size = 18

        self.btn_min.setIcon(load_svg_icon("minimize.svg", colors["icon_color"], size))
        self.btn_close.setIcon(load_svg_icon("close.svg", colors["icon_color"], size))

        if self._parent.isMaximized():
            self.btn_max.setIcon(load_svg_icon("restore.svg", colors["icon_color"], size))
        else:
            self.btn_max.setIcon(load_svg_icon("maximize.svg", colors["icon_color"], size))

    def update_icons(self, color: QColor):
        """
        Met à jour les icônes avec une couleur spécifique.
        Appelée depuis main_window lors du changement de thème.
        """
        self._icon_color = color
        size = 18
        
        self.btn_min.setIcon(load_svg_icon("minimize.svg", color, size))
        self.btn_close.setIcon(load_svg_icon("close.svg", color, size))
        
        if self._parent.isMaximized():
            self.btn_max.setIcon(load_svg_icon("restore.svg", color, size))
        else:
            self.btn_max.setIcon(load_svg_icon("maximize.svg", color, size))

    def _toggle_maximize(self):
        if self._parent.isMaximized():
            self._parent.showNormal()
        else:
            self._parent.showMaximized()
        self._update_button_icons()

    def set_icon_color(self, color: QColor):
        """Définit la couleur des icônes (utilisé par update_icons)"""
        self._icon_color = color
        self.update_icons(color)

    def _on_palette_changed(self):
        """Surveiller le changement de palette/thème"""
        # Déterminer le thème actuel selon la couleur de fond
        app = QApplication.instance()
        try:
            bg_color = app.palette().color(QPalette.Window).color()
            brightness = (bg_color.red() + bg_color.green() + bg_color.blue()) / 3

            # Si fond sombre (< 128), thème sombre; sinon thème clair
            if brightness < 128:
                self._current_theme = "dark"
            else:
                self._current_theme = "light"
        except:
            # En cas d'erreur, garder le thème sombre par défaut
            self._current_theme = "dark"

        self._update_button_icons()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self._parent.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton and self._drag_pos is not None:
            self._parent.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def set_theme(self, theme: str):
        """Définir explicitement le thème (dark ou light)"""
        self._current_theme = theme
        self._update_button_icons()