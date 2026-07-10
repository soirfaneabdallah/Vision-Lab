# fishid/controllers/settings_handler.py
from PySide6.QtWidgets import QDialog
from PySide6.QtGui import QColor
from fishid.ui.settings_dialog import SettingsDialog
from fishid.ui.styles import DARK_THEME, LIGHT_THEME
from fishid.utils import load_svg_icon


class SettingsHandler:
    def __init__(self, parent, model_manager, duplicate_checker, app_settings):
        self.parent = parent
        self.model_manager = model_manager
        self.duplicate_checker = duplicate_checker
        self.app_settings = app_settings
        self.settings_dialog = None

    def show(self):
        if self.settings_dialog is None:
            self.settings_dialog = SettingsDialog(self.parent)

        # Charger valeurs actuelles
        self.settings_dialog.frame_spin.setValue(self.app_settings["frame_interval"])
        self.settings_dialog.conf_slider.setValue(int(self.app_settings["conf_threshold"] * 100))
        self.settings_dialog.anom_slider.setValue(int(self.app_settings["anomaly_threshold"] * 100))
        self.settings_dialog.theme_combo.setCurrentIndex(0 if self.app_settings["theme"] == "dark" else 1)
        self.settings_dialog.mode_combo.setCurrentIndex(0 if self.app_settings["mode"] == "fish" else 1)
        self.settings_dialog.save_checkbox.setChecked(self.app_settings["save_predictions"])
        self.settings_dialog.folder_edit.setText(self.duplicate_checker.output_dir)
        self.settings_dialog.save_mode_combo.setCurrentIndex(0 if self.app_settings["save_mode"] == "best" else 1)
        self.settings_dialog.author_edit.setText(self.app_settings["report_author"])
        self.settings_dialog.gpu_checkbox.setChecked(self.app_settings["use_gpu"])

        self.settings_dialog.setStyleSheet(self.parent.styleSheet())
        self.settings_dialog.ensurePolished()

        if self.settings_dialog.exec() == QDialog.Accepted:
            # Récupérer les nouvelles valeurs
            self.app_settings["frame_interval"] = self.settings_dialog.frame_spin.value()
            self.app_settings["conf_threshold"] = self.settings_dialog.conf_slider.value() / 100.0
            self.app_settings["anomaly_threshold"] = self.settings_dialog.anom_slider.value() / 100.0
            self.app_settings["save_predictions"] = self.settings_dialog.save_checkbox.isChecked()
            self.app_settings["save_mode"] = self.settings_dialog.get_save_mode()
            self.app_settings["report_author"] = self.settings_dialog.get_author()
            new_folder = self.settings_dialog.folder_edit.text()
            if new_folder:
                self.app_settings["output_dir"] = new_folder
                self.duplicate_checker.set_output_dir(new_folder)
            new_mode = self.settings_dialog.get_mode()
            if new_mode != self.app_settings["mode"]:
                self.app_settings["mode"] = new_mode
            new_theme = self.settings_dialog.get_theme()
            if new_theme != self.app_settings["theme"]:
                self.app_settings["theme"] = new_theme
                self.parent.current_theme = new_theme
                self.parent.apply_theme()
            new_use_gpu = self.settings_dialog.get_use_gpu()
            if new_use_gpu != self.app_settings["use_gpu"]:
                self.app_settings["use_gpu"] = new_use_gpu
                self.model_manager.load_models(use_gpu=new_use_gpu)
            # Sauvegarder dans QSettings
            from fishid.controllers.app_controller import save_settings
            save_settings(self.app_settings)
            return True
        return False