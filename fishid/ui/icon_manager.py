# fishid/ui/icon_manager.py
from PySide6.QtGui import QColor
from fishid.utils import load_svg_icon


def update_all_icons(app):
    """
    Met à jour TOUTES les icônes de l'application en une seule fonction.
    """
    color = QColor("#FFFFFF") if app.current_theme == "dark" else QColor("#1A2A3A")
    
    # 1. Barre de contrôle
    _update_control_bar_icons(app, color)
    
    # 2. Barre de titre
    if hasattr(app, 'header_bar'):
        app.header_bar.update_icons(color)
    
    # 3. Play/Pause
    if hasattr(app, 'player_controls'):
        app.player_controls.update_play_pause_icon()


def _update_control_bar_icons(app, color):
    """Met à jour les icônes de la barre de contrôle."""
    buttons = [
        ('btn_load', 'open.svg'),
        ('btn_webcam', 'webcam.svg'),
        ('btn_phone_browser', 'smartphone.svg'),
        ('btn_stop', 'stop.svg'),
        ('btn_settings', 'settings.svg'),
        ('btn_toggle_detections', 'detections.svg'),
        ('btn_manual_review', 'edit.svg'),
        ('btn_mosaic', 'mosaic.svg'),
    ]
    
    for attr_name, icon_name in buttons:
        if hasattr(app, attr_name):
            button = getattr(app, attr_name)
            button.setIcon(load_svg_icon(icon_name, color, 24))
    
    # Icône du volume
    if hasattr(app, 'volume_slider') and hasattr(app, 'btn_volume_icon'):
        value = app.volume_slider.value()
        if value == 0:
            app.btn_volume_icon.setIcon(load_svg_icon("volume_off.svg", color, 24))
        elif value <= 30:
            app.btn_volume_icon.setIcon(load_svg_icon("volume_low.svg", color, 24))
        elif value <= 70:
            app.btn_volume_icon.setIcon(load_svg_icon("volume_medium.svg", color, 24))
        else:
            app.btn_volume_icon.setIcon(load_svg_icon("volume_up.svg", color, 24))
    
    # Menu mosaïque
    if hasattr(app, 'mosaic_single_action'):
        app.mosaic_single_action.setIcon(load_svg_icon("image_single.svg", color, 18))
    if hasattr(app, 'mosaic_folder_action'):
        app.mosaic_folder_action.setIcon(load_svg_icon("image_folder.svg", color, 18))