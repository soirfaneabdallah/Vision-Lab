# fishid/ui/settings_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QCheckBox, QLineEdit, QPushButton, QSpinBox, QSlider,
    QDialogButtonBox, QFileDialog, QGroupBox, QMessageBox,
)
from PySide6.QtCore import Qt
from fishid.utils import add_logo_to_dialog

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paramètres")
        self.setMinimumWidth(520)
        add_logo_to_dialog(self)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # ================================================================
        # SECTION 1 : Général
        # ================================================================
        general_group = QGroupBox("Général")
        general_layout = QVBoxLayout(general_group)
        general_layout.setSpacing(12)

        # Mode
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode :"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["🐟 Poissons", "🗑️ Déchets"])
        self.mode_combo.setMinimumWidth(160)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        general_layout.addLayout(mode_layout)

        # Thème
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Thème :"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["🌙 Sombre", "☀️ Clair"])
        self.theme_combo.setMinimumWidth(160)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        general_layout.addLayout(theme_layout)

        # Auteur du rapport
        author_layout = QHBoxLayout()
        author_layout.addWidget(QLabel("Auteur du rapport :"))
        self.author_edit = QLineEdit()
        self.author_edit.setPlaceholderText("Nom de l'auteur")
        author_layout.addWidget(self.author_edit)
        general_layout.addLayout(author_layout)

        layout.addWidget(general_group)

        # ================================================================
        # SECTION 2 : Sauvegarde
        # ================================================================
        save_group = QGroupBox("Sauvegarde des images")
        save_layout = QVBoxLayout(save_group)
        save_layout.setSpacing(12)

        self.save_checkbox = QCheckBox("Enregistrer les images de prédiction")
        save_layout.addWidget(self.save_checkbox)

        # Mode de sauvegarde
        save_mode_layout = QHBoxLayout()
        save_mode_layout.addWidget(QLabel("Mode de sauvegarde :"))
        self.save_mode_combo = QComboBox()
        self.save_mode_combo.addItems(["Meilleure image par individu", "Toutes les occurrences"])
        self.save_mode_combo.setMinimumWidth(180)
        save_mode_layout.addWidget(self.save_mode_combo)
        save_mode_layout.addStretch()
        save_layout.addLayout(save_mode_layout)

        # Dossier de sortie
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Dossier :"))
        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("Choisir un dossier...")
        folder_layout.addWidget(self.folder_edit)
        browse_btn = QPushButton("Parcourir...")
        browse_btn.setProperty("class", "controlButton")
        browse_btn.clicked.connect(self._browse_folder)
        folder_layout.addWidget(browse_btn)
        save_layout.addLayout(folder_layout)

        layout.addWidget(save_group)

        # ================================================================
        # SECTION 3 : Analyse
        # ================================================================
        analysis_group = QGroupBox("Analyse")
        analysis_layout = QVBoxLayout(analysis_group)
        analysis_layout.setSpacing(12)

        # Intervalle de frames
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Intervalle d'analyse :"))
        self.frame_spin = QSpinBox()
        self.frame_spin.setRange(1, 30)
        self.frame_spin.setSuffix(" frames")
        interval_layout.addWidget(self.frame_spin)
        interval_layout.addStretch()
        analysis_layout.addLayout(interval_layout)

        # Seuil de confiance
        conf_layout = QHBoxLayout()
        conf_layout.addWidget(QLabel("Seuil de confiance classification :"))
        self.conf_slider = QSlider(Qt.Horizontal)
        self.conf_slider.setRange(10, 99)
        self.conf_label = QLabel("40%")
        self.conf_label.setFixedWidth(35)
        self.conf_label.setAlignment(Qt.AlignCenter)
        self.conf_slider.valueChanged.connect(lambda v: self.conf_label.setText(f"{v}%"))
        conf_layout.addWidget(self.conf_slider)
        conf_layout.addWidget(self.conf_label)
        analysis_layout.addLayout(conf_layout)

        # Seuil d'anomalie
        anom_layout = QHBoxLayout()
        anom_layout.addWidget(QLabel("Seuil d'anomalie (score < seuil → Inconnu) :"))
        self.anom_slider = QSlider(Qt.Horizontal)
        self.anom_slider.setRange(50, 99)
        self.anom_label = QLabel("90%")
        self.anom_label.setFixedWidth(35)
        self.anom_label.setAlignment(Qt.AlignCenter)
        self.anom_slider.valueChanged.connect(lambda v: self.anom_label.setText(f"{v}%"))
        anom_layout.addWidget(self.anom_slider)
        anom_layout.addWidget(self.anom_label)
        analysis_layout.addLayout(anom_layout)

        layout.addWidget(analysis_group)

        # ================================================================
        # SECTION 4 : Buffer (Pré-traitement)
        # ================================================================
        buffer_group = QGroupBox("Pré-traitement (Buffer)")
        buffer_layout = QVBoxLayout(buffer_group)
        buffer_layout.setSpacing(12)

        self.buffer_enabled_checkbox = QCheckBox("Activer le pré-traitement des frames (buffer)")
        self.buffer_enabled_checkbox.setToolTip(
            "Prétraite les frames en avance pour une lecture plus fluide sur machines lentes"
        )
        buffer_layout.addWidget(self.buffer_enabled_checkbox)

        buffer_frames_layout = QHBoxLayout()
        buffer_frames_layout.addWidget(QLabel("Nombre de frames à pré-traiter :"))
        self.buffer_frames_spin = QSpinBox()
        self.buffer_frames_spin.setRange(15, 300)
        self.buffer_frames_spin.setSuffix(" frames")
        self.buffer_frames_spin.setToolTip(
            "Plus le nombre est élevé, plus le démarrage est lent mais la lecture plus fluide"
        )
        buffer_frames_layout.addWidget(self.buffer_frames_spin)
        buffer_frames_layout.addStretch()
        buffer_layout.addLayout(buffer_frames_layout)

        layout.addWidget(buffer_group)

        # ================================================================
        # SECTION 5 : Avancé
        # ================================================================
        advanced_group = QGroupBox("Avancé")
        advanced_layout = QVBoxLayout(advanced_group)
        advanced_layout.setSpacing(12)

        gpu_available = self._check_gpu_available()
        self.gpu_checkbox = QCheckBox("Utiliser le GPU (accélération matérielle si disponible)")
        advanced_layout.addWidget(self.gpu_checkbox)

        self.gpu_info_label = QLabel("")
        self.gpu_info_label.setWordWrap(True)
        self._update_gpu_info(gpu_available)
        advanced_layout.addWidget(self.gpu_info_label)

        self.gpu_checkbox.toggled.connect(self._on_gpu_toggled)
        layout.addWidget(advanced_group)

        # ================================================================
        # Boutons OK / Annuler
        # ================================================================
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Initialisation des valeurs
        self._init_values(parent)

    def _init_values(self, parent):
        """Initialise les widgets avec les valeurs depuis parent.app_settings."""
        if not parent:
            return
        settings = parent.app_settings
        self.frame_spin.setValue(settings.get("frame_interval", 10))
        self.conf_slider.setValue(int(settings.get("conf_threshold", 0.4) * 100))
        self.anom_slider.setValue(int(settings.get("anomaly_threshold", 0.9) * 100))
        self.mode_combo.setCurrentIndex(0 if settings.get("mode", "fish") == "fish" else 1)
        self.theme_combo.setCurrentIndex(0 if settings.get("theme", "dark") == "dark" else 1)
        self.save_checkbox.setChecked(settings.get("save_predictions", False))
        self.save_mode_combo.setCurrentIndex(0 if settings.get("save_mode", "best") == "best" else 1)
        self.author_edit.setText(settings.get("report_author", "Vision Lab"))
        
        # Buffer settings
        self.buffer_enabled_checkbox.setChecked(settings.get("buffer_enabled", True))
        self.buffer_frames_spin.setValue(settings.get("buffer_frames", 60))
        
        # Dossier de sortie
        if hasattr(parent, 'processing_ctrl') and hasattr(parent.processing_ctrl, 'duplicate_checker'):
            self.folder_edit.setText(parent.processing_ctrl.duplicate_checker.output_dir)
        elif hasattr(parent, 'duplicate_checker'):
            self.folder_edit.setText(parent.duplicate_checker.output_dir)
        else:
            self.folder_edit.setText(settings.get("output_dir", "output"))
        self.gpu_checkbox.setChecked(settings.get("use_gpu", False))

    # ------------------------------------------------------------------
    def _check_gpu_available(self):
        try:
            import onnxruntime as ort
            providers = ort.get_available_providers()
            return 'CUDAExecutionProvider' in providers or 'TensorrtExecutionProvider' in providers
        except Exception:
            return False

    def _update_gpu_info(self, gpu_available):
        if gpu_available:
            self.gpu_info_label.setText("✅ GPU compatible détecté.")
            self.gpu_info_label.setStyleSheet("color: #00BFA6;")
        else:
            self.gpu_info_label.setText("❌ Aucun GPU compatible trouvé. L'inférence utilisera le CPU.")
            self.gpu_info_label.setStyleSheet("color: #FF5252;")

    def _on_gpu_toggled(self, checked):
        if checked:
            gpu_available = self._check_gpu_available()
            if not gpu_available:
                QMessageBox.warning(
                    self,
                    "GPU non disponible",
                    "Aucun GPU compatible n'a été détecté sur cette machine.\nL'inférence continuera d'utiliser le CPU."
                )
                self.gpu_checkbox.setChecked(False)
            else:
                self._update_gpu_info(True)

    def _browse_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Choisir le dossier de sortie")
        if path:
            self.folder_edit.setText(path)

    # --- Accesseurs ---
    def get_theme(self):
        return "dark" if self.theme_combo.currentIndex() == 0 else "light"

    def get_mode(self):
        return "fish" if self.mode_combo.currentIndex() == 0 else "waste"

    def get_save_mode(self):
        return "best" if self.save_mode_combo.currentIndex() == 0 else "all"

    def get_use_gpu(self):
        return self.gpu_checkbox.isChecked()

    def get_author(self):
        return self.author_edit.text().strip() or "Vision Lab"

    def get_buffer_enabled(self):
        return self.buffer_enabled_checkbox.isChecked()

    def get_buffer_frames(self):
        return self.buffer_frames_spin.value()