# fishid/controllers/report_handler.py
import os
import tempfile
import webbrowser
import shutil
import datetime
from PySide6.QtWidgets import QFileDialog, QMessageBox
from fishid.core.report_generator import ReportGenerator
from fishid.utils import find_asset_path


class ReportHandler:
    def __init__(self, duplicate_checker, detections_panel, get_author, get_video_name):
        self.duplicate_checker = duplicate_checker
        self.detections_panel = detections_panel
        self.get_author = get_author
        self.get_video_name = get_video_name

    def export_report(self, parent_widget):
        stats = self.detections_panel.get_all_stats()
        best_images = {}
        for class_name in self.detections_panel.class_items.keys():
            class_dir = os.path.join(self.duplicate_checker.output_dir, class_name)
            if os.path.exists(class_dir):
                images = [f for f in os.listdir(class_dir) if f.endswith(('.jpg', '.png'))]
                if images:
                    best_images[class_name] = os.path.join(class_dir, images[-1])

        tmp_dir = tempfile.gettempdir()
        logo_src = find_asset_path("assets/logos/icon.png")
        logo_dst = None
        if logo_src and os.path.exists(logo_src):
            logo_dst = os.path.join(tmp_dir, "visionlab_logo_temp.png")
            try:
                shutil.copy2(logo_src, logo_dst)
            except:
                logo_dst = None

        tmp_name = f"visionlab_preview_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        tmp_path = os.path.join(tmp_dir, tmp_name)

        generator = ReportGenerator(
            output_dir=tmp_dir,
            video_name=self.get_video_name(),
            author=self.get_author(),
            logo_path=logo_dst
        )
        try:
            generator.generate(stats, best_images, filename=tmp_name)
        except Exception as e:
            QMessageBox.critical(parent_widget, "Erreur", f"Impossible de générer l'aperçu : {e}")
            if logo_dst:
                try: os.remove(logo_dst)
                except: pass
            return

        try:
            webbrowser.open(tmp_path)
        except Exception:
            QMessageBox.warning(parent_widget, "Aperçu",
                f"L'aperçu a été généré mais n'a pas pu être ouvert automatiquement.\n{tmp_path}")

        reply = QMessageBox.question(
            parent_widget,
            "Aperçu du rapport",
            "Un aperçu a été ouvert.\nVoulez-vous enregistrer définitivement ce rapport ?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            default_name = f"rapport_visionlab_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            save_path, _ = QFileDialog.getSaveFileName(
                parent_widget,
                "Enregistrer le rapport PDF",
                os.path.join(self.duplicate_checker.output_dir, default_name),
                "Fichiers PDF (*.pdf)"
            )
            if save_path:
                try:
                    shutil.copy2(tmp_path, save_path)
                    return save_path
                except Exception as e:
                    QMessageBox.critical(parent_widget, "Erreur", f"Impossible d'enregistrer : {e}")
            try: os.remove(tmp_path)
            except: pass
        else:
            try: os.remove(tmp_path)
            except: pass
        if logo_dst:
            try: os.remove(logo_dst)
            except: pass
        return None