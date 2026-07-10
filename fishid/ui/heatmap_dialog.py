# fishid/ui/heatmap_dialog.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox
from PySide6.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import pandas as pd
from fishid.core.analysis_manager import AnalysisDataManager


class HeatmapDialog(QDialog):
    def __init__(self, parent=None, analysis_manager: AnalysisDataManager = None):
        super().__init__(parent)
        self.analysis_manager = analysis_manager
        self.setWindowTitle("🔥 Carte de Densité")
        self.setMinimumSize(900, 700)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Contrôles
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Classe:"))
        self.class_combo = QComboBox()
        self.class_combo.addItem("Toutes les classes")
        self.populate_class_combo()
        self.class_combo.currentTextChanged.connect(self.update_plot)
        controls_layout.addWidget(self.class_combo)
        controls_layout.addStretch()
        
        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(self.close)
        controls_layout.addWidget(btn_close)
        
        layout.addLayout(controls_layout)
        
        # Graphique
        self.figure = Figure(figsize=(10, 8), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # Charger les données
        self.update_plot()
    
    def populate_class_combo(self):
        """Remplit la combo avec les classes disponibles."""
        if self.analysis_manager and hasattr(self.analysis_manager, 'all_class_names'):
            for name in sorted(self.analysis_manager.all_class_names):
                self.class_combo.addItem(name)
    
    def update_plot(self):
        """Met à jour le graphique heatmap."""
        self.figure.clear()
        
        if self.analysis_manager is None or self.analysis_manager.df_detections is None:
            self._show_no_data("Aucune donnée disponible")
            return
        
        if self.analysis_manager.df_detections.empty:
            self._show_no_data("Aucune détection trouvée")
            return
        
        # Filtrer par classe
        selected_class = self.class_combo.currentText()
        df = self.analysis_manager.df_detections
        
        if selected_class != "Toutes les classes":
            df = df[df['class_name'] == selected_class]
        
        if df.empty:
            self._show_no_data(f"Aucune donnée pour '{selected_class}'")
            return
        
        # ⭐ Vérifier que les coordonnées sont valides
        # Si toutes les coordonnées sont à 0, utiliser des positions aléatoires
        # ou afficher un message d'information
        if 'x_min' not in df.columns or df['x_min'].sum() == 0:
            # On utilise des positions aléatoires pour simuler une heatmap
            # ou on affiche un message
            self._show_no_data("Coordonnées des détections non disponibles.\nUtilisez une vidéo avec des bounding boxes.")
            return
        
        # Créer la heatmap (2D histogram)
        ax = self.figure.add_subplot(111)
        
        # Normaliser les coordonnées (0-1)
        # On suppose que les coordonnées sont dans l'intervalle [0, 224]
        if df['x_min'].max() > 1 or df['y_min'].max() > 1:
            # Coordonnées en pixels
            x = df['x_min'] / 224.0
            y = df['y_min'] / 224.0
        else:
            # Coordonnées déjà normalisées
            x = df['x_min']
            y = df['y_min']
        
        # Filtrer les valeurs valides (0 <= x <= 1, 0 <= y <= 1)
        mask = (x >= 0) & (x <= 1) & (y >= 0) & (y <= 1)
        x = x[mask]
        y = y[mask]
        
        if len(x) < 2:
            self._show_no_data("Pas assez de détections valides pour la heatmap")
            return
        
        # Créer l'histogramme 2D
        heatmap, xedges, yedges = np.histogram2d(x, y, bins=20, range=[[0, 1], [0, 1]])
        
        # Afficher la heatmap
        im = ax.imshow(heatmap.T, origin='lower', cmap='hot', aspect='auto', 
                       extent=[0, 1, 0, 1])
        
        ax.set_xlabel("Position X normalisée")
        ax.set_ylabel("Position Y normalisée")
        ax.set_title(f"Carte de densité - {selected_class} ({(len(x))} détections)")
        
        # Ajouter les ticks
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1])
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1])
        
        # Colorbar
        cbar = self.figure.colorbar(im, ax=ax, label="Nombre de détections")
        
        # Afficher le nombre de détections
        ax.text(0.5, -0.12, f"Total: {len(x)} détections", 
                transform=ax.transAxes, ha='center', va='center', fontsize=10)
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def _show_no_data(self, message):
        """Affiche un message quand il n'y a pas de données."""
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, f"⚠️ {message}", 
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=14, color='gray')
        ax.set_title("Carte de Densité")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        self.canvas.draw()