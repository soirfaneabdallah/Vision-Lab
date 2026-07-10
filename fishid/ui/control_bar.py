# fishid/ui/control_bar.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSlider, QLabel, QMenu, QToolButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from fishid.utils import load_svg_icon


def create_control_bar(parent, icon_color):
    """Crée la barre de contrôle en bas de la fenêtre."""
    control_bar = QWidget()
    control_bar.setObjectName("controlBar")
    control_bar.setFixedHeight(60)
    layout = QHBoxLayout(control_bar)
    layout.setContentsMargins(20, 10, 20, 10)
    layout.setSpacing(12)

    # ========== BOUTONS EXISTANTS ==========
    # Bouton Load (charger vidéo)
    parent.btn_load = QPushButton()
    parent.btn_load.setIcon(load_svg_icon("open.svg", icon_color, 24))
    parent.btn_load.setToolTip("Charger une vidéo")
    parent.btn_load.setFixedSize(40, 40)
    parent.btn_load.setObjectName("controlButton")
    parent.btn_load.clicked.connect(parent._on_load_video)
    layout.addWidget(parent.btn_load)

    # Bouton Webcam
    parent.btn_webcam = QPushButton()
    parent.btn_webcam.setIcon(load_svg_icon("webcam.svg", icon_color, 24))
    parent.btn_webcam.setToolTip("Webcam locale")
    parent.btn_webcam.setFixedSize(40, 40)
    parent.btn_webcam.setObjectName("controlButton")
    parent.btn_webcam.clicked.connect(parent._on_webcam)
    layout.addWidget(parent.btn_webcam)

    # Bouton Smartphone
    parent.btn_phone_browser = QPushButton()
    parent.btn_phone_browser.setIcon(load_svg_icon("smartphone.svg", icon_color, 24))
    parent.btn_phone_browser.setToolTip("Connecter un smartphone")
    parent.btn_phone_browser.setFixedSize(40, 40)
    parent.btn_phone_browser.setObjectName("controlButton")
    parent.btn_phone_browser.clicked.connect(parent._on_browser_camera_requested)
    layout.addWidget(parent.btn_phone_browser)

    # ========== BOUTON MOSAÏQUE AVEC MENU ==========
    parent.btn_mosaic = QToolButton()
    parent.btn_mosaic.setIcon(load_svg_icon("mosaic.svg", icon_color, 24))
    parent.btn_mosaic.setToolTip("Analyser une image ou assembler des photos drone")
    parent.btn_mosaic.setFixedSize(40, 40)
    parent.btn_mosaic.setObjectName("controlButton")
    parent.btn_mosaic.setPopupMode(QToolButton.InstantPopup)
    
    # Créer le menu et stocker les actions pour mise à jour ultérieure
    mosaic_menu = QMenu(parent)
    
    action_single = mosaic_menu.addAction("  Analyser une image seule")
    action_single.setIcon(load_svg_icon("image_single.svg", icon_color, 18))
    action_single.setToolTip("Ouvrir une image (JPEG, PNG, BMP) et l'analyser avec l'IA")
    action_single.triggered.connect(parent._on_analyze_single_image)

    mosaic_menu.addSeparator()

    action_folder = mosaic_menu.addAction("  Analyser un dossier d'images")
    action_folder.setIcon(load_svg_icon("image_folder.svg", icon_color, 18))
    action_folder.setToolTip("Analyser toutes les images d'un dossier une par une")
    action_folder.triggered.connect(parent._on_process_image_folder)
    
    parent.btn_mosaic.setMenu(mosaic_menu)
    layout.addWidget(parent.btn_mosaic)

    # ========== BOUTONS DE LECTURE ==========
    parent.btn_play_pause = QPushButton()
    parent.btn_play_pause.setIcon(load_svg_icon("play.svg", icon_color, 24))
    parent.btn_play_pause.setToolTip("Démarrer / Pause (Espace)")
    parent.btn_play_pause.setFixedSize(40, 40)
    parent.btn_play_pause.setObjectName("controlButton")
    parent.btn_play_pause.setEnabled(False)
    parent.btn_play_pause.clicked.connect(parent._toggle_play_pause)
    layout.addWidget(parent.btn_play_pause)

    # Bouton Stop
    parent.btn_stop = QPushButton()
    parent.btn_stop.setIcon(load_svg_icon("stop.svg", icon_color, 24))
    parent.btn_stop.setToolTip("Arrêter")
    parent.btn_stop.setFixedSize(40, 40)
    parent.btn_stop.setObjectName("controlButton")
    parent.btn_stop.setEnabled(False)
    parent.btn_stop.clicked.connect(parent._stop_processing)
    layout.addWidget(parent.btn_stop)

    # ========== CONTROLE VOLUME ==========
    parent.btn_volume_icon = QPushButton()
    parent.btn_volume_icon.setIcon(load_svg_icon("volume_up.svg", icon_color, 24))
    parent.btn_volume_icon.setToolTip("Couper le son")
    parent.btn_volume_icon.setFixedSize(40, 40)
    parent.btn_volume_icon.setObjectName("controlButton")
    parent.btn_volume_icon.clicked.connect(parent._toggle_mute)
    layout.addWidget(parent.btn_volume_icon)

    parent.volume_slider = QSlider(Qt.Horizontal)
    parent.volume_slider.setRange(0, 100)
    parent.volume_slider.setValue(80)
    parent.volume_slider.setFixedWidth(100)
    parent.volume_slider.setToolTip("Volume : 80%")
    parent.volume_slider.valueChanged.connect(parent._volume_changed)
    layout.addWidget(parent.volume_slider)

    # ========== PROGRESSION ==========
    parent.position_slider = QSlider(Qt.Horizontal)
    parent.position_slider.setRange(0, 100)
    parent.position_slider.setEnabled(False)
    parent.position_slider.setObjectName("positionSlider")
    layout.addWidget(parent.position_slider, 1)

    # ========== LABEL TEMPS ==========
    parent.lbl_time = QLabel("00:00:00")
    parent.lbl_time.setObjectName("timeLabel")
    parent.lbl_time.setEnabled(False)
    parent.lbl_time.setMinimumWidth(140)
    parent.lbl_time.setAlignment(Qt.AlignCenter)
    layout.addWidget(parent.lbl_time)

    # ========== BOUTONS OUTILS ==========
    parent.btn_settings = QPushButton()
    parent.btn_settings.setIcon(load_svg_icon("settings.svg", icon_color, 24))
    parent.btn_settings.setToolTip("Paramètres")
    parent.btn_settings.setFixedSize(40, 40)
    parent.btn_settings.setObjectName("controlButton")
    parent.btn_settings.clicked.connect(parent._show_settings_dialog)
    layout.addWidget(parent.btn_settings)

    # ========== NOUVEAU BOUTON ANALYSE AVEC MENU ==========
    parent.btn_analysis = QToolButton()
    parent.btn_analysis.setIcon(load_svg_icon("chart_line.svg", icon_color, 24))
    parent.btn_analysis.setToolTip("Outils d'analyse (graphiques, heatmap, ...)")
    parent.btn_analysis.setFixedSize(40, 40)
    parent.btn_analysis.setObjectName("controlButton")
    parent.btn_analysis.setPopupMode(QToolButton.InstantPopup)
    
    # Créer le menu Analyse
    analysis_menu = QMenu(parent)
    
    # Action Graphique Temporel
    action_temporal_graph = analysis_menu.addAction("  Graphique Temporel")
    action_temporal_graph.setIcon(load_svg_icon("chart_line.svg", icon_color, 18))
    action_temporal_graph.setToolTip("Afficher l'évolution des espèces au fil du temps")
    action_temporal_graph.triggered.connect(parent._show_temporal_graph)
    
    # Action Carte de Densité (Heatmap)
    action_heatmap = analysis_menu.addAction("  Carte de Densité (Heatmap)")
    action_heatmap.setIcon(load_svg_icon("heatmap.svg", icon_color, 18))
    action_heatmap.setToolTip("Afficher les zones d'apparition fréquente")
    action_heatmap.triggered.connect(parent._show_heatmap)
    action_heatmap.setEnabled(True)  # Activer si vous avez implémenté la fonction
    
    parent.btn_analysis.setMenu(analysis_menu)
    layout.addWidget(parent.btn_analysis)

    # Bouton Correction manuelle
    parent.btn_manual_review = QPushButton()
    parent.btn_manual_review.setIcon(load_svg_icon("edit.svg", icon_color, 24))
    parent.btn_manual_review.setToolTip("Correction manuelle des prédictions")
    parent.btn_manual_review.setFixedSize(40, 40)
    parent.btn_manual_review.setObjectName("controlButton")
    parent.btn_manual_review.clicked.connect(parent._open_manual_review)
    layout.addWidget(parent.btn_manual_review)

    # ========== STOCKER LES RÉFÉRENCES ==========
    parent.mosaic_single_action = action_single
    parent.mosaic_folder_action = action_folder
    parent.mosaic_menu = mosaic_menu
    
    parent.analysis_temporal_graph_action = action_temporal_graph
    parent.analysis_heatmap_action = action_heatmap
    parent.analysis_menu = analysis_menu

    return control_bar


def update_control_bar_icons(parent, icon_color):
    """
    Met à jour les icônes de TOUS les boutons de la barre de contrôle.
    À appeler lors du changement de thème.
    """
    # Mettre à jour les boutons principaux
    buttons = [
        ('btn_load', 'open.svg'),
        ('btn_webcam', 'webcam.svg'),
        ('btn_phone_browser', 'smartphone.svg'),
        ('btn_play_pause', 'play.svg'),
        ('btn_stop', 'stop.svg'),
        ('btn_settings', 'settings.svg'),
        ('btn_toggle_detections', 'detections.svg'),
        ('btn_manual_review', 'edit.svg'),
        ('btn_mosaic', 'mosaic.svg'),
        ('btn_analysis', 'chart_line.svg'),
    ]
    
    for attr_name, icon_name in buttons:
        if hasattr(parent, attr_name):
            button = getattr(parent, attr_name)
            if attr_name == 'btn_play_pause' and hasattr(parent, 'player_controls'):
                parent.player_controls.update_play_pause_icon()
            else:
                button.setIcon(load_svg_icon(icon_name, icon_color, 24))
    
    # Mettre à jour l'icône du volume selon sa valeur
    if hasattr(parent, 'volume_slider') and hasattr(parent, 'btn_volume_icon'):
        value = parent.volume_slider.value()
        if value == 0:
            parent.btn_volume_icon.setIcon(load_svg_icon("volume_off.svg", icon_color, 24))
        elif value <= 30:
            parent.btn_volume_icon.setIcon(load_svg_icon("volume_low.svg", icon_color, 24))
        elif value <= 70:
            parent.btn_volume_icon.setIcon(load_svg_icon("volume_medium.svg", icon_color, 24))
        else:
            parent.btn_volume_icon.setIcon(load_svg_icon("volume_up.svg", icon_color, 24))
    
    # Mettre à jour les icônes du menu mosaïque
    if hasattr(parent, 'mosaic_single_action'):
        parent.mosaic_single_action.setIcon(load_svg_icon("image_single.svg", icon_color, 18))
    if hasattr(parent, 'mosaic_folder_action'):
        parent.mosaic_folder_action.setIcon(load_svg_icon("image_folder.svg", icon_color, 18))
    
    # Mettre à jour les icônes du menu Analyse
    if hasattr(parent, 'analysis_temporal_graph_action'):
        parent.analysis_temporal_graph_action.setIcon(load_svg_icon("chart_line.svg", icon_color, 18))
    if hasattr(parent, 'analysis_heatmap_action'):
        parent.analysis_heatmap_action.setIcon(load_svg_icon("heatmap.svg", icon_color, 18))