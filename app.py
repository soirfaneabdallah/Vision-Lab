# main.py
import sys
import traceback
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer
from fishid.main_window import FishIDApp
from fishid.ui.splash_screen import SplashScreen

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("FishApp")
    app.setOrganizationName("MarineBiologyLab")
    app.setStyle("Fusion")

    # Splash screen
    splash = SplashScreen()
    splash.show()
    splash.set_message("Chargement des modèles...")
    app.processEvents()

    screen_geometry = app.primaryScreen().availableGeometry()
    splash.move(screen_geometry.center() - splash.rect().center())

    try:
        window = FishIDApp()
    except Exception as e:
        # Afficher l'erreur dans une boîte de dialogue
        error_msg = f"Une erreur est survenue au lancement :\n\n{str(e)}\n\n{traceback.format_exc()}"
        QMessageBox.critical(None, "Erreur de lancement", error_msg)
        splash.close()
        sys.exit(1)

    # Afficher la fenêtre après un délai (pour que le splash reste visible)
    import time
    start = time.time()
    window.show()
    elapsed = time.time() - start
    remaining_ms = max(0, int((5.0 - elapsed) * 1000))
    QTimer.singleShot(remaining_ms, splash.close)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()