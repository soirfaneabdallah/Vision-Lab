# fishid/ui/detections_panel.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTreeWidget, QTreeWidgetItem, QLabel, QPushButton,
    QFrame, QGroupBox, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QBrush, QPen
import datetime, math

# ----------------------------------------------------------------------
# Petite carte indicateur (tuile colorée)
# ----------------------------------------------------------------------
class IndicatorTile(QFrame):
    def __init__(self, title, value="0", color="#89B4FA", parent=None):
        super().__init__(parent)
        self.setObjectName("indicatorTile")
        self.setMinimumSize(150, 80)
        self.setFrameShape(QFrame.StyledPanel)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(2)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #A0A8C0; font-size: 11px;")
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: bold;")
        lay.addWidget(self.title_label)
        lay.addWidget(self.value_label)
        self._color = QColor(color)

    def set_value(self, value_str):
        self.value_label.setText(str(value_str))

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self._color.darker(150)))
        painter.drawRect(0, 0, 4, self.height())

# ----------------------------------------------------------------------
# Petite carte pour un indice (Shannon, Simpson, Pielou)
# ----------------------------------------------------------------------
class DiversityCard(QFrame):
    def __init__(self, title, value="--", color="#89B4FA", parent=None):
        super().__init__(parent)
        self.setObjectName("diversityCard")
        self.setFixedHeight(70)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        self.icon_label = QLabel(title[0])
        self.icon_label.setFixedSize(36, 36)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet(
            f"background-color: {color}22; color: {color}; border-radius: 8px; font-weight: bold; font-size: 16px;"
        )
        text_layout = QVBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #A0A8C0; font-size: 11px;")
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"color: {color}; font-size: 15px; font-weight: bold;")
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.value_label)
        lay.addWidget(self.icon_label)
        lay.addLayout(text_layout)
        lay.addStretch()

    def set_value(self, value_str):
        self.value_label.setText(value_str)

# ----------------------------------------------------------------------
# Panneau principal
# ----------------------------------------------------------------------
class DetectionsPanel(QWidget):
    export_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("rightPanel")
        self.class_items = {}
        self.total_detections = 0
        self.total_anomalies = 0
        self.start_time = None
        self.current_mode = "fish"
        self._init_ui()

    def set_mode(self, mode):
        self.current_mode = mode

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        title = QLabel("📊 Tableau de bord")
        title.setObjectName("detectionTitle")
        main_layout.addWidget(title)

        indicators_layout = QGridLayout()
        self.tile_abundance = IndicatorTile("Abondance totale", "0")
        self.tile_species = IndicatorTile("Espèces", "0", color="#FFB74D")
        self.tile_anomalies = IndicatorTile("Inconnues", "0", color="#FF5252")
        self.tile_duration = IndicatorTile("Durée", "0 min", color="#69F0AE")
        indicators_layout.addWidget(self.tile_abundance, 0, 0)
        indicators_layout.addWidget(self.tile_species, 0, 1)
        indicators_layout.addWidget(self.tile_anomalies, 1, 0)
        indicators_layout.addWidget(self.tile_duration, 1, 1)
        main_layout.addLayout(indicators_layout)

        div_group = QGroupBox("Diversité")
        div_layout = QHBoxLayout(div_group)
        self.card_shannon = DiversityCard("Shannon (H')", color="#89B4FA")
        self.card_simpson = DiversityCard("Simpson (1-D)", color="#FFB74D")
        self.card_pielou = DiversityCard("Pielou (J')", color="#69F0AE")
        div_layout.addWidget(self.card_shannon)
        div_layout.addWidget(self.card_simpson)
        div_layout.addWidget(self.card_pielou)
        main_layout.addWidget(div_group)

        tree_group = QGroupBox("🐟 Espèces détectées")
        tree_layout = QVBoxLayout(tree_group)

        self.tree = QTreeWidget()
        self.tree.setObjectName("detectionTree")
        self.tree.setHeaderLabels(["Espèce", "Nombre", "Confiance", "% Abondance"])
        self.tree.setColumnWidth(0, 200)
        self.tree.setColumnWidth(1, 100)
        self.tree.setColumnWidth(2, 80)
        self.tree.setColumnWidth(3, 80)
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(False)
        self.tree.setSelectionMode(QAbstractItemView.NoSelection)
        self.tree.setFocusPolicy(Qt.NoFocus)
        tree_layout.addWidget(self.tree)
        main_layout.addWidget(tree_group, 1)

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)

        self.btn_clear = QPushButton("🗑 Vider")
        self.btn_clear.setObjectName("clearButton")
        self.btn_clear.clicked.connect(self.clear_all)

        self.btn_export = QPushButton("📄 Exporter PDF")
        self.btn_export.setObjectName("exportButton")
        self.btn_export.clicked.connect(self.export_requested.emit)

        actions_layout.addWidget(self.btn_clear)
        actions_layout.addWidget(self.btn_export)
        actions_layout.addStretch()
        main_layout.addLayout(actions_layout)

    # ------------------------------------------------------------------
    # Signature corrigée : class_name, confidence, filename (filename optionnel)
    # Assurez-vous que le signal detection_added dans VideoHandler émet trois arguments :
    # detection_added.emit(class_name, confidence, filename)
    # ------------------------------------------------------------------
    def add_detection(self, class_name, confidence, filename=""):
        """
        Ajoute ou met à jour une détection.
        :param class_name: nom de la classe (ou "?" pour temporaire)
        :param confidence: confiance (float entre 0 et 1)
        :param filename: optionnel, nom du fichier sauvegardé
        """
        if class_name in ("Incertain",):
            return

        is_temporary = (class_name == "?")
        if not is_temporary:
            if self.start_time is None:
                self.start_time = datetime.datetime.now()
            self.total_detections += 1
            if class_name == "Inconnu":
                self.total_anomalies += 1

        # Préfixer l'emoji selon le mode
        if class_name == "?":
            display_name = "⏳ Détection en cours..."
        elif class_name == "Inconnu":
            display_name = "❓ Inconnu"
        elif self.current_mode == "waste":
            display_name = f"🗑️ {class_name}"
        else:
            display_name = f"🐟 {class_name}"

        if class_name in self.class_items:
            data = self.class_items[class_name]
            if not is_temporary:
                data['count'] += 1
            data['last_conf'] = confidence
            data['item'].setText(1, str(data['count']))
            # Afficher la confiance en pourcentage (par ex. "87%")
            data['item'].setText(2, f"{confidence:.0%}")
            self._update_abundance()
            self._update_indicators()
            self.tree.resizeColumnToContents(2)
            self.tree.viewport().update()
            return

        # Nouvelle classe
        item = QTreeWidgetItem(self.tree)
        item.setText(0, display_name)
        item.setText(1, "0" if is_temporary else "1")
        item.setText(2, f"{confidence:.0%}" if confidence > 0 else "")
        item.setText(3, "")
        # Couleur
        if class_name == "?":
            item.setForeground(0, QColor("#888888"))
        elif class_name == "Inconnu":
            item.setForeground(0, QColor("#FF5252"))
        elif self.current_mode == "waste":
            item.setForeground(0, QColor("#FFB74D"))
        else:
            item.setForeground(0, QColor("#89B4FA"))
        font = item.font(0)
        font.setBold(True)
        item.setFont(0, font)

        self.class_items[class_name] = {
            'item': item,
            'count': 0 if is_temporary else 1,
            'last_conf': confidence
        }
        if not is_temporary:
            self._update_abundance()
        self._update_indicators()
        self.tree.expandAll()
        self.tree.resizeColumnToContents(2)
        self.tree.viewport().update()

    def update_detection(self, old_class_name, new_class_name, confidence):
        """Remplace une classe temporaire par une vraie classe."""
        if old_class_name not in self.class_items:
            self.add_detection(new_class_name, confidence)
            return
        data = self.class_items.pop(old_class_name)
        item = data['item']
        index = self.tree.indexOfTopLevelItem(item)
        if index >= 0:
            self.tree.takeTopLevelItem(index)
        self.add_detection(new_class_name, confidence)

    def _update_abundance(self):
        total = sum(d['count'] for d in self.class_items.values() if d['count'] > 0)
        if total == 0:
            return
        for name, data in self.class_items.items():
            if name == "?":
                continue
            pct = (data['count'] / total) * 100
            data['item'].setText(3, f"{pct:.1f} %")

    def _update_indicators(self):
        total = self.total_detections
        nb = len([c for c in self.class_items if c != "?"])
        duration = ""
        if self.start_time:
            delta = datetime.datetime.now() - self.start_time
            minutes, seconds = divmod(int(delta.total_seconds()), 60)
            duration = f"{minutes} min {seconds}s"
        self.tile_abundance.set_value(total)
        self.tile_species.set_value(nb)
        self.tile_anomalies.set_value(self.total_anomalies)
        self.tile_duration.set_value(duration)

        counts = [d['count'] for d in self.class_items.values() if d['count'] > 0 and d['count'] is not None]
        n = len(counts)
        if total > 0 and n > 0:
            proportions = [c / total for c in counts]
            shannon = -sum(p * math.log(p) for p in proportions if p > 0)
            simpson = 1 - sum(p**2 for p in proportions)
            pielou = (shannon / math.log(n)) if n > 1 else 0.0
            self.card_shannon.set_value(f"{shannon:.3f}")
            self.card_simpson.set_value(f"{simpson:.4f}")
            self.card_pielou.set_value(f"{pielou:.4f}")
        else:
            self.card_shannon.set_value("--")
            self.card_simpson.set_value("--")
            self.card_pielou.set_value("--")

    def add_detection_batch(self, detections: list):
        for det in detections:
            self.add_detection(det.get('class_name', '?'), det.get('confidence', 0.0))

    def clear_all(self):
        self.tree.clear()
        self.class_items.clear()
        self.total_detections = 0
        self.total_anomalies = 0
        self.start_time = None
        self.tile_abundance.set_value("0")
        self.tile_species.set_value("0")
        self.tile_anomalies.set_value("0")
        self.tile_duration.set_value("0 min")
        self.card_shannon.set_value("--")
        self.card_simpson.set_value("--")
        self.card_pielou.set_value("--")

    def get_all_stats(self):
        counts = [d['count'] for d in self.class_items.values() if d['count'] > 0 and d['count'] is not None]
        total = sum(counts)
        n = len(counts)
        duration = ""
        if self.start_time:
            delta = datetime.datetime.now() - self.start_time
            minutes, seconds = divmod(int(delta.total_seconds()), 60)
            duration = f"{minutes} min {seconds}s"
        shannon = simpson = pielou = 0.0
        if total > 0 and n > 0:
            proportions = [c / total for c in counts]
            shannon = -sum(p * math.log(p) for p in proportions if p > 0)
            simpson = 1 - sum(p**2 for p in proportions)
            pielou = (shannon / math.log(n)) if n > 1 else 0.0
        species_list = []
        for name, data in self.class_items.items():
            if name == "?":
                continue
            pct = (data['count'] / total * 100) if total > 0 else 0
            species_list.append({
                'name': name, 'count': data['count'],
                'confidence': data.get('last_conf', 0.0), 'abundance': pct
            })
        return {
            'total': total, 'species': n, 'anomalies': self.total_anomalies,
            'duration': duration, 'richness': n,
            'shannon': shannon, 'simpson': simpson, 'pielou': pielou,
            'species_list': species_list
        }