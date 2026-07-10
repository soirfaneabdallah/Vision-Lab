# fishid/ui/manual_review.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QMessageBox, QInputDialog, QGroupBox, QFrame,
    QSizePolicy, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage, QIcon
from PIL import Image as PILImage
import os, shutil
from fishid.utils import add_logo_to_dialog, resource_path


class ManualReviewDialog(QDialog):
    def __init__(self, parent, output_dir, class_names, session_prefix):
        super().__init__(parent)

        from fishid.utils import add_logo_to_dialog
        # dans __init__ :
        add_logo_to_dialog(self)

        self.setWindowTitle("Correction manuelle – en direct")
        self.setMinimumSize(1100, 680)
        self.output_dir = output_dir
        self.class_names = class_names
        self.session_prefix = session_prefix   # ex: "ma_video_20260523_143022"
        self.image_data = []
        self.current_index = -1
        self.custom_classes_path = os.path.join(self.output_dir, "custom_classes.txt")

        self._load_custom_classes()
        self.setStyleSheet(parent.styleSheet())

        self._init_ui()
        self._refresh_images()

    def _load_custom_classes(self):
        if os.path.exists(self.custom_classes_path):
            with open(self.custom_classes_path, 'r', encoding='utf-8') as f:
                for line in f:
                    cls = line.strip()
                    if cls and cls not in self.class_names:
                        self.class_names.append(cls)

    def _save_custom_class(self, new_class):
        with open(self.custom_classes_path, 'a', encoding='utf-8') as f:
            f.write(new_class + "\n")

    def _refresh_images(self):
        """Charge uniquement les images dont le nom commence par session_prefix."""
        self.image_data.clear()
        for class_name in os.listdir(self.output_dir):
            class_dir = os.path.join(self.output_dir, class_name)
            if os.path.isdir(class_dir) and class_name != "corrigees":
                for filename in os.listdir(class_dir):
                    if filename.lower().endswith(('.jpg', '.jpeg', '.png')) and filename.startswith(self.session_prefix):
                        path = os.path.join(class_dir, filename)
                        self.image_data.append((path, class_name))
        self.image_data.sort(key=lambda x: x[0])
        if self.image_data:
            if self.current_index < 0 or self.current_index >= len(self.image_data):
                self.current_index = 0
            self._load_image(self.current_index)
        else:
            self.image_label.setText("Aucune image pour cette session.")
            self.progress_label.setText("Image 0 / 0")

    # ------------------------------------------------------------------
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # --- Barre d'outils supérieure ---
        toolbar = QHBoxLayout()
        self.progress_label = QLabel("Image 0 / 0")
        self.progress_label.setObjectName("detectionStats")
        self.progress_label.setAlignment(Qt.AlignCenter)
        toolbar.addWidget(self.progress_label)
        toolbar.addStretch()
        self.refresh_btn = QPushButton("🔄 Rafraîchir")
        self.refresh_btn.setProperty("class", "controlButton")
        self.refresh_btn.clicked.connect(self._refresh_images)
        toolbar.addWidget(self.refresh_btn)
        main_layout.addLayout(toolbar)

        # --- Splitter horizontal : image à gauche, contrôles à droite ---
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet("QSplitter::handle { background-color: #1E2433; }")

        # Zone image (gauche)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(650, 450)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setObjectName("viewerWidget")
        splitter.addWidget(self.image_label)

        # Panneau de contrôle (droite)
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(16)

        # Détails
        details_group = QGroupBox("Détails")
        details_layout = QVBoxLayout(details_group)
        self.predicted_class_title = QLabel("Classe prédite")
        self.predicted_class_title.setObjectName("detectionTitle")
        self.predicted_class_value = QLabel("")
        self.predicted_class_value.setObjectName("detectionStats")
        details_layout.addWidget(self.predicted_class_title)
        details_layout.addWidget(self.predicted_class_value)
        right_layout.addWidget(details_group)

        # Correction
        correction_group = QGroupBox("Correction")
        correction_layout = QVBoxLayout(correction_group)
        correction_layout.addWidget(QLabel("Nouvelle classe :"))
        self.class_combo = QComboBox()
        self.class_combo.addItems(self.class_names)
        self.class_combo.setMinimumWidth(200)
        correction_layout.addWidget(self.class_combo)

        self.apply_btn = QPushButton("✔ Appliquer")
        self.apply_btn.setProperty("class", "controlButton")
        self.apply_btn.clicked.connect(self._apply_correction)
        correction_layout.addWidget(self.apply_btn)

        self.add_class_btn = QPushButton("＋ Nouvelle classe")
        self.add_class_btn.setProperty("class", "controlButton")
        self.add_class_btn.clicked.connect(self._add_new_class)
        correction_layout.addWidget(self.add_class_btn)
        right_layout.addWidget(correction_group)

        # Navigation
        nav_group = QGroupBox("Navigation")
        nav_layout = QVBoxLayout(nav_group)
        btn_layout = QHBoxLayout()
        self.prev_btn = QPushButton("◀ Précédent")
        self.prev_btn.setProperty("class", "controlButton")
        self.prev_btn.clicked.connect(self._prev_image)
        self.next_btn = QPushButton("Suivant ▶")
        self.next_btn.setProperty("class", "controlButton")
        self.next_btn.clicked.connect(self._next_image)
        btn_layout.addWidget(self.prev_btn)
        btn_layout.addWidget(self.next_btn)
        nav_layout.addLayout(btn_layout)
        right_layout.addWidget(nav_group)

        right_layout.addStretch()

        # Terminer
        self.finish_btn = QPushButton("Terminer")
        self.finish_btn.setObjectName("stopButton")
        self.finish_btn.clicked.connect(self.accept)
        right_layout.addWidget(self.finish_btn)

        splitter.addWidget(right_panel)
        splitter.setSizes([650, 350])
        main_layout.addWidget(splitter, 1)

    # ------------------------------------------------------------------
    def _load_image(self, index):
        if 0 <= index < len(self.image_data):
            self.current_index = index
            path, pred_class = self.image_data[index]

            try:
                pil_img = PILImage.open(path).convert('RGB')
                label_size = self.image_label.size()
                max_w, max_h = label_size.width(), label_size.height()
                w, h = pil_img.size
                scale = min(max_w / w, max_h / h, 1.0)
                new_w, new_h = int(w * scale), int(h * scale)
                pil_img = pil_img.resize((new_w, new_h), PILImage.LANCZOS)
                data = pil_img.tobytes("raw", "RGB")
                qimage = QImage(data, new_w, new_h, new_w * 3, QImage.Format_RGB888)
                self.image_label.setPixmap(QPixmap.fromImage(qimage))
            except Exception:
                self.image_label.setText("Erreur de chargement")

            self.predicted_class_value.setText(pred_class)
            idx = self.class_combo.findText(pred_class)
            if idx >= 0:
                self.class_combo.setCurrentIndex(idx)
            self.progress_label.setText(f"Image {index + 1} / {len(self.image_data)}")
            self.prev_btn.setEnabled(index > 0)
            self.next_btn.setEnabled(index < len(self.image_data) - 1)

    def _apply_correction(self):
        if self.current_index < 0:
            return
        path, old_class = self.image_data[self.current_index]
        new_class = self.class_combo.currentText()
        if new_class != old_class:
            dest_dir = os.path.join(self.output_dir, new_class)
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, os.path.basename(path))
            shutil.move(path, dest_path)
            self.image_data[self.current_index] = (dest_path, new_class)
            self.predicted_class_value.setText(new_class)
            idx = self.class_combo.findText(new_class)
            if idx >= 0:
                self.class_combo.setCurrentIndex(idx)
        if self.current_index < len(self.image_data) - 1:
            self._load_image(self.current_index + 1)
        else:
            QMessageBox.information(self, "Terminé", "Toutes les images ont été révisées.")
            self.accept()

    def _add_new_class(self):
        new_class, ok = QInputDialog.getText(
            self, "Nouvelle classe", "Nom de la nouvelle classe :"
        )
        if ok and new_class.strip():
            new_class = new_class.strip()
            existing = [self.class_combo.itemText(i) for i in range(self.class_combo.count())]
            if new_class not in existing:
                self.class_combo.addItem(new_class)
                self.class_combo.setCurrentText(new_class)
                self._save_custom_class(new_class)

    def _prev_image(self):
        if self.current_index > 0:
            self._load_image(self.current_index - 1)

    def _next_image(self):
        if self.current_index < len(self.image_data) - 1:
            self._load_image(self.current_index + 1)
            
    def _open_manual_review(self):
        if not self.session_prefix:
            QMessageBox.warning(self, "Aucune session", "Aucune analyse en cours.")
            return

        class_names = list(self.classifier_fish.class_names) + ["Inconnu", "Incertain"]
        dialog = ManualReviewDialog(
            self,
            self.duplicate_checker.output_dir,
            class_names,
            session_prefix=self.session_prefix
        )
        dialog.exec()