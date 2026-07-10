# fishid/ui/menu_bar.py
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtGui import QAction
from fishid.ui.header_bar import HeaderBar


def create_menu_bar(parent):
    """Crée la barre de menus et retourne le widget conteneur (barre titre + menus)."""
    from PySide6.QtWidgets import QMenuBar
    menu_bar = QMenuBar(parent)
    menu_bar.setNativeMenuBar(False)

    # --- Fichier ---
    file_menu = menu_bar.addMenu("&Fichier")
    load_action = QAction("📂 Charger une vidéo", parent)
    load_action.setShortcut("Ctrl+O")
    load_action.triggered.connect(parent._on_load_video)
    file_menu.addAction(load_action)

    output_action = QAction("📁 Dossier de sortie...", parent)
    output_action.triggered.connect(parent._change_output_dir)
    file_menu.addAction(output_action)

    file_menu.addSeparator()
    quit_action = QAction("❌ Quitter", parent)
    quit_action.triggered.connect(parent.close)
    file_menu.addAction(quit_action)

    # --- Mode ---
    mode_menu = menu_bar.addMenu("&Mode")
    fish_action = QAction("🐟 Poissons", parent)
    fish_action.triggered.connect(lambda: parent._set_mode("fish"))
    mode_menu.addAction(fish_action)
    waste_action = QAction("🗑️ Déchets", parent)
    waste_action.triggered.connect(lambda: parent._set_mode("waste"))
    mode_menu.addAction(waste_action)

    # --- Traitement ---
    proc_menu = menu_bar.addMenu("&Traitement")
    start_action = QAction("▶ Démarrer l'analyse", parent)
    start_action.setShortcut("F5")
    start_action.triggered.connect(parent._start_processing)
    proc_menu.addAction(start_action)
    stop_action = QAction("⏹ Arrêter", parent)
    stop_action.triggered.connect(parent._stop_processing)
    proc_menu.addAction(stop_action)

    # --- Affichage ---
    view_menu = menu_bar.addMenu("&Affichage")
    theme_action = QAction("🌓 Thème jour / nuit", parent)
    theme_action.setShortcut("Ctrl+T")
    theme_action.triggered.connect(parent.toggle_theme)
    view_menu.addAction(theme_action)

    # --- Historique ---
    history_menu = menu_bar.addMenu("&Historique")
    history_action = QAction("📜 Voir l'historique", parent)
    history_action.triggered.connect(parent._show_history)
    history_menu.addAction(history_action)

    # --- Aide ---
    help_menu = menu_bar.addMenu("&Aide")
    about_action = QAction("ℹ️ À propos", parent)
    about_action.triggered.connect(parent._show_about)
    help_menu.addAction(about_action)

    # Conteneur (barre de titre + menu)
    container = QWidget()
    container_layout = QVBoxLayout(container)
    container_layout.setContentsMargins(0, 0, 0, 0)
    container_layout.setSpacing(0)
    container_layout.addWidget(HeaderBar(parent))
    container_layout.addWidget(menu_bar)
    parent.setMenuWidget(container)

    # Stocker la référence pour la mise à jour des icônes
    parent.header_bar = container_layout.itemAt(0).widget()