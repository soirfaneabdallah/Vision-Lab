# main.py
import sys
import time
import traceback
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer
from fishid.main_window import FishIDApp
from fishid.ui.splash_screen import SplashScreen

def main():
    app = QApplication(sys.argv)
    # main.py
    app.setApplicationName("Vision Lab")
    app.setOrganizationName("VisionLab")
    app.setStyle("Fusion")

    # --- Splash screen ---
    splash = SplashScreen()
    splash.show()
    splash.set_message("Chargement des modèles...")
    app.processEvents()

    # Centrer le splash sur l'écran
    screen_geometry = app.primaryScreen().availableGeometry()
    splash.move(screen_geometry.center() - splash.rect().center())

    # Création de la fenêtre principale (chargement des modèles)
    try:
        window = FishIDApp()
    except Exception as e:
        error_msg = (
            f"Une erreur est survenue au lancement :\n\n"
            f"{str(e)}\n\n{traceback.format_exc()}"
        )
        QMessageBox.critical(None, "Erreur de lancement", error_msg)
        splash.close()
        sys.exit(1)

    # S'assurer que le splash reste affiché au moins 5 secondes
    start = time.time()
    elapsed = time.time() - start
    remaining_ms = max(0, int((5.0 - elapsed) * 1000))

    def show_main_window():
        splash.finish(window)   # ferme le splash proprement
        window.show()           # affiche la fenêtre principale

    QTimer.singleShot(remaining_ms, show_main_window)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()