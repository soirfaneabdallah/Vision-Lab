# fishid/ui/detections_panel.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTreeWidget,
                                QTreeWidgetItem, QLabel, QPushButton, QHBoxLayout,
                                QFrame, QGraphicsEffect, QSizePolicy, QScrollArea)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPalette, QFont, QLinearGradient, QPainter, QPolygon
import datetime


class DetectionsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("rightPanel")
        self.setObjectName("detectionsPanel")
        self.class_items = {}          # class_name -> {'item': QTreeWidgetItem, 'count': int, 'last_conf': float}
        self.total_detections = 0
        self.total_anomalies = 0
        self.start_time = None
        self.mode = "fish"  # 'fish' ou 'waste'


        # ⭐ STYLE PROFESSIONNEL
        self.setup_styles()
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)


        # ⭐ HEADER PROF (avec dégradé)
        self.header = self._create_prof_header()
        layout.addWidget(self.header)


        # ⭐ RÉSUMÉ GLOBAL (cartes avec icônes)
        self.summary_card = self._create_summary_card()
        layout.addWidget(self.summary_card)


        # ⭐ ARBRE DES DÉTECTIONS (style moderne)
        self.detection_tree = self._create_detection_tree()
        layout.addWidget(self.detection_tree)


        # ⭐ BOUTONS ACTION (style moderne)
        self.actions_bar = self._create_actions_bar()
        layout.addWidget(self.actions_bar)


        layout.addStretch()


    def setup_styles(self):
        """Définir le style professionnel."""
        # Palette de couleurs professionnelle
        self.colors = {
            'primary': '#89B4FA',        # Bleu moderne
            'secondary': '#A6C3FC',      # Bleu clair
            'accent': '#F5A9B8',         # Rose moderne
            'success': '#B4E9BF',        # Vert moderne
            'warning': '#FFD9A5',        # Orange moderne
            'danger': '#FFB3BA',         # Rouge moderne
            'info': '#BAE1FF',           # Bleu info
            'background': '#1E2433',     # Fond sombre
            'surface': '#2A3244',        # Surface
            'text_primary': '#FFFFFF',   # Texte principal
            'text_secondary': '#A0A8B8', # Texte secondaire
            'border': '#3A4254',         # Bordure
        }


    def _create_prof_header(self):
        """Créer un header professionnel avec dégradé."""
        header = QFrame()
        header.setObjectName("headerProf")
        header.setStyleSheet("""
            QFrame#headerProf {
                background: linear-gradient(135deg, #89B4FA 0%, #A6C3FC 100%);
                border-radius: 12px;
                padding: 16px;
            }
        """)
        
        layout = QVBoxLayout(header)
        layout.setSpacing(8)
        layout.setContentsMargins(20, 20, 20, 20)


        # ⭐ TITRE (grand, gras, avec icône)
        title_layout = QHBoxLayout()
        title_layout.setSpacing(12)


        # Icône dynamique
        icon_label = QLabel()
        icon_label.setText("📊")
        icon_label.setStyleSheet("font-size: 28px;")


        # Titre principal
        self.title_label = QLabel("STATISTIQUES DE DÉTECTION")
        self.title_label.setObjectName("headerTitle")
        self.title_label.setStyleSheet("""
            QLabel#headerTitle {
                color: #FFFFFF;
                font-size: 24px;
                font-weight: bold;
                letter-spacing: 1px;
            }
        """)


        title_layout.addWidget(icon_label)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()


        # Sous-titre (mode)
        self.mode_label = QLabel("Mode: POISSONS")
        self.mode_label.setObjectName("headerSubtitle")
        self.mode_label.setStyleSheet("""
            QLabel#headerSubtitle {
                color: #E0E8F0;
                font-size: 14px;
                font-weight: normal;
            }
        """)


        layout.addLayout(title_layout)
        layout.addWidget(self.mode_label)


        return header


    def _create_summary_card(self):
        """Créer une carte de résumé professionnelle."""
        card = QFrame()
        card.setObjectName("summaryCard")
        card.setStyleSheet("""
            QFrame#summaryCard {
                background-color: #2A3244;
                border: 1px solid #3A4254;
                border-radius: 12px;
            }
        """)


        layout = QVBoxLayout(card)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)


        # ⭐ TITRE RÉSUMÉ
        summary_title = QLabel("📈 RÉSUMÉ GLOBAL")
        summary_title.setObjectName("summaryTitle")
        summary_title.setStyleSheet("""
            QLabel#summaryTitle {
                color: #89B4FA;
                font-size: 16px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }
        """)
        layout.addWidget(summary_title)


        # ⭐ STATISTIQUES (4 cartes)
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)


        # Carte 1: Total détections
        self.stat_1 = self._create_stat_card("🔍", "Total", "0", "#89B4FA")
        stats_layout.addWidget(self.stat_1)


        # Carte 2: Espèces distinctes
        self.stat_2 = self._create_stat_card("🐟", "Espèces", "0", "#B4E9BF")
        stats_layout.addWidget(self.stat_2)


        # Carte 3: Inconnues
        self.stat_3 = self._create_stat_card("❓", "Inconnues", "0", "#FFB3BA")
        stats_layout.addWidget(self.stat_3)


        # Carte 4: Durée
        self.stat_4 = self._create_stat_card("⏱️", "Durée", "0 min", "#BAE1FF")
        stats_layout.addWidget(self.stat_4)


        layout.addLayout(stats_layout)


        # ⭐ RÉSUMÉ TEXTUEL
        self.summary_label = QLabel("Prêt")
        self.summary_label.setObjectName("summaryText")
        self.summary_label.setStyleSheet("""
            QLabel#summaryText {
                color: #A0A8B8;
                font-size: 13px;
                line-height: 1.6;
            }
        """)
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)


        return card


    def _create_stat_card(self, icon, label, value, color):
        """Créer une petite carte de statistique."""
        card = QFrame()
        card.setObjectName("statCard")
        card.setStyleSheet("""
            QFrame#statCard {
                background-color: #3A4254;
                border-radius: 8px;
                padding: 12px;
            }
        """)


        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card.setMinimumHeight(70)


        layout = QVBoxLayout(card)
        layout.setSpacing(6)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setAlignment(Qt.AlignCenter)


        # Icône
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 24px;")


        # Label
        label_widget = QLabel(label)
        label_widget.setStyleSheet("""
            QLabel {
                color: #A0A8B8;
                font-size: 11px;
                font-weight: normal;
            }
        """)


        # Valeur
        value_widget = QLabel(value)
        value_widget.setObjectName("statValue")
        value_widget.setStyleSheet(f"""
            QLabel#statValue {
                color: {color};
                font-size: 18px;
                font-weight: bold;
            }
        """)


        layout.addWidget(icon_label)
        layout.addWidget(label_widget)
        layout.addWidget(value_widget)


        return card


    def _create_detection_tree(self):
        """Créer l'arbre de détections moderne."""
        tree_container = QFrame()
        tree_container.setObjectName("treeContainer")
        tree_container.setStyleSheet("""
            QFrame#treeContainer {
                background-color: #2A3244;
                border: 1px solid #3A4254;
                border-radius: 12px;
            }
        """)


        layout = QVBoxLayout(tree_container)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)


        # ⭐ TITRE ARBRE
        tree_title = QLabel("📋 DÉTECTIONS PAR ESPÈCE")
        tree_title.setObjectName("treeTitle")
        tree_title.setStyleSheet("""
            QLabel#treeTitle {
                color: #89B4FA;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        layout.addWidget(tree_title)


        # ⭐ ARBRE (style moderne)
        self.tree = QTreeWidget()
        self.tree.setObjectName("detectionTreeModern")
        self.tree.setStyleSheet("""
            QTreeWidget#detectionTreeModern {
                background-color: #1E2433;
                border: none;
                border-radius: 8px;
                font-size: 13px;
            }
            QTreeWidget#detectionTreeModern::item {
                height: 35px;
                padding: 8px;
                border-radius: 6px;
            }
            QTreeWidget#detectionTreeModern::item:selected {
                background-color: #3A4254;
            }
            QTreeWidget#detectionTreeModern::item:hover {
                background-color: #2A3244;
            }
            QTreeWidget#detectionTreeModern::header {
                background-color: #3A4254;
                color: #89B4FA;
                font-weight: bold;
                font-size: 12px;
                height: 30px;
            }
        """)


        self.tree.setHeaderLabels(["Espèce", "Nb", "Confiance"])
        self.tree.setColumnWidth(0, 150)
        self.tree.setColumnWidth(1, 60)
        self.tree.setColumnWidth(2, 80)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSortingEnabled(True)


        layout.addWidget(self.tree)


        return tree_container


    def _create_actions_bar(self):
        """Créer la barre d'actions professionnelle."""
        actions = QFrame()
        actions.setObjectName("actionsBar")
        actions.setStyleSheet("""
            QFrame#actionsBar {
                background-color: #2A3244;
                border: 1px solid #3A4254;
                border-radius: 12px;
            }
        """)


        layout = QHBoxLayout(actions)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)


        # ⭐ BOUTON VIDER
        self.btn_clear = QPushButton("🗑 VIDER LES STATISTIQUES")
        self.btn_clear.setObjectName("btnClearProf")
        self.btn_clear.setStyleSheet("""
            QPushButton#btnClearProf {
                background-color: #FFB3BA;
                color: #FFFFFF;
                font-size: 13px;
                font-weight: bold;
                border-radius: 8px;
                padding: 12px 20px;
                border: none;
            }
            QPushButton#btnClearProf:hover {
                background-color: #FF9BA5;
            }
            QPushButton#btnClearProf:pressed {
                background-color: #FF7F8F;
            }
        """)
        self.btn_clear.clicked.connect(self.clear_all)


        # ⭐ BOUTON EXPORTER
        self.btn_export = QPushButton("💾 EXPORTER REPORT")
        self.btn_export.setObjectName("btnExportProf")
        self.btn_export.setStyleSheet("""
            QPushButton#btnExportProf {
                background-color: #89B4FA;
                color: #FFFFFF;
                font-size: 13px;
                font-weight: bold;
                border-radius: 8px;
                padding: 12px 20px;
                border: none;
            }
            QPushButton#btnExportProf:hover {
                background-color: #6FA3F0;
            }
            QPushButton#btnExportProf:pressed {
                background-color: #5593E0;
            }
        """)
        self.btn_export.clicked.connect(self._on_export)


        layout.addWidget(self.btn_clear)
        layout.addWidget(self.btn_export)


        return actions


    def _on_export(self):
        """Action d'exporter (à connecter)."""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Export", "Report exporté !")


    def set_mode(self, mode: str):
        """Changer le mode (fish/waste)."""
        self.mode = mode
        if mode == "fish":
            self.mode_label.setText("Mode: POISSONS 🐟")
            self.title_label.setText("STATISTIQUES DE DÉTECTION")
        else:
            self.mode_label.setText("Mode: DÉCHETS 🗑")
            self.title_label.setText("STATISTIQUES DE DÉCHETS")


    def add_detection(self, class_name: str, filename: str = "", confidence: float = 0.0):
        """Ajoute une détection et met à jour l'affichage."""
        if self.start_time is None:
            self.start_time = datetime.datetime.now()


        self.total_detections += 1
        if class_name == "Inconnu" or class_name == "Incertain":
            self.total_anomalies += 1


        # Créer ou récupérer le nœud de l'espèce
        if class_name not in self.class_items:
            item = QTreeWidgetItem(self.tree)
            item.setText(0, class_name)
            item.setText(1, "0")
            item.setText(2, "")
            
            # ⭐ STYLE MODERNE POUR L'ITEM
            item.setForeground(0, QColor("#89B4FA"))
            font = item.font(0)
            font.setBold(True)
            font.setPointSize(13)
            item.setFont(0, font)
            
            self.class_items[class_name] = {'item': item, 'count': 0, 'last_conf': 0.0}


        data = self.class_items[class_name]
        data['count'] += 1
        data['last_conf'] = confidence
        data['item'].setText(1, str(data['count']))
        data['item'].setText(2, f"{confidence:.0%}")


        # ⭐ METTRE À JOUR LE RÉSUMÉ
        self._update_summary()


    def _update_summary(self):
        """Mettre à jour toutes les statistiques."""
        duration = ""
        if self.start_time:
            delta = datetime.datetime.now() - self.start_time
            minutes, seconds = divmod(int(delta.total_seconds()), 60)
            if minutes > 0:
                duration = f"{minutes} min {seconds} s"
            else:
                duration = f"{seconds} s"


        nb_classes = len(self.class_items)


        # ⭐ METTRE À JOUR LES 4 CARTES
        self.stat_1.findChild(QLabel, "statValue").setText(str(self.total_detections))
        self.stat_2.findChild(QLabel, "statValue").setText(str(nb_classes))
        self.stat_3.findChild(QLabel, "statValue").setText(str(self.total_anomalies))
        self.stat_4.findChild(QLabel, "statValue").setText(duration)


        # ⭐ RÉSUMÉ TEXTUEL
        text = (f"🔍 Total détections : {self.total_detections}\n"
                f"🐟 Espèces distinctes : {nb_classes}\n"
                f"❓ Images inconnues : {self.total_anomalies}\n"
                f"⏱️ Durée analyse : {duration}")
        self.summary_label.setText(text)


    def add_detection_batch(self, detections: list):
        """Ajouter un batch de détections."""
        for det in detections:
            self.add_detection(det.get('class_name', '?'), '', det.get('confidence', 0.0))


    def clear_all(self):
        """Vider toutes les statistiques."""
        self.tree.clear()
        self.class_items.clear()
        self.total_detections = 0
        self.total_anomalies = 0
        self.start_time = None


        # ⭐ METTRE À JOUR LES CARTES
        self.stat_1.findChild(QLabel, "statValue").setText("0")
        self.stat_2.findChild(QLabel, "statValue").setText("0")
        self.stat_3.findChild(QLabel, "statValue").setText("0")
        self.stat_4.findChild(QLabel, "statValue").setText("0 min")


        self.summary_label.setText("Prêt")


    def export_requested(self):
        """Émettre le signal d'export."""
        pass