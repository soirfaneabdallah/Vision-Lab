# ui/icon_utils.py
import sys
import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QIcon, QPainter, QColor
from PySide6.QtSvg import QSvgRenderer

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def icon_path(name):
    return resource_path(f"assets/icons/{name}")

def load_svg_icon(svg_path: str, color: QColor = QColor("#FFFFFF"), size: int = 24) -> QIcon:
    renderer = QSvgRenderer(svg_path)
    if not renderer.isValid():
        return QIcon()
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    # Colorisation simple
    image = pixmap.toImage()
    for y in range(image.height()):
        for x in range(image.width()):
            pixel = image.pixelColor(x, y)
            if pixel.alpha() > 0:
                image.setPixelColor(x, y, color)
    return QIcon(QPixmap.fromImage(image))