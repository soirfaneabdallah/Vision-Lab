# fishid/ui/temporal_analysis_widget.py
"""
Widget d'analyse temporelle : courbes d'abondance par espèce au fil du temps.
Fonctionnalités :
- Types de graphiques : lignes, barres, aires, points, histogramme, boxplot, camembert, tendance
- Agrégation temporelle : 1s, 5s, 10s, 30s, 1min, 5min
- Filtrage par espèce (cases à cocher) et par plage temporelle
- Export PNG, SVG, CSV
- Légende interactive (clic pour masquer/afficher)
- Statistiques détaillées (min, max, moyenne, total par espèce)
- Zoom et déplacement (barre d'outils matplotlib intégrée)
- Thème clair/sombre synchronisé avec l'application
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import List, Dict, Optional

import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import pandas as pd
import numpy as np

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget, QComboBox, QSpinBox,
    QTextEdit, QFileDialog, QMessageBox, QGroupBox, QGridLayout,
    QDoubleSpinBox, QSlider, QSplitter, QFrame,
)
from PySide6.QtGui import QAction

from PySide6.QtGui import QMouseEvent, QColor
from fishid.core.analysis_manager import AnalysisDataManager
from fishid.utils import load_svg_icon
# Palette de couleurs (agrandie)
COLORS = [
    "#00b4d8", "#7b61ff", "#00e5a0", "#ff6b35",
    "#ffd166", "#ef476f", "#06d6a0", "#118ab2",
    "#f78c6b", "#e74c8b", "#2ecc71", "#3498db",
    "#f1c40f", "#9b59b6", "#1abc9c", "#e67e22",
]

class TemporalAnalysisWidget(QWidget):
    """Widget d'analyse temporelle enrichi."""

    # Signal émis quand les données changent
    data_changed = Signal()

    def __init__(self, analysis_manager: AnalysisDataManager, parent=None):
        super().__init__(parent)
        self._mgr = analysis_manager
        self._species_checks: Dict[str, QCheckBox] = {}
        self._current_plot_type = "line"
        self._interval_sec = 1
        self._time_min = 0.0
        self._time_max = 0.0
        self._time_range_slider_min = 0.0
        self._time_range_slider_max = 0.0
        self._visible_lines = {}  # pour suivre les lignes masquées

        self.setWindowTitle("Analyse temporelle")
        self.setMinimumSize(1100, 700)
        self.setStyleSheet("background: #0F172A; color: #E2E8F0;")
        self._build_ui()
        self.refresh()

    # ----------------------------------------------------------------------
    # Construction UI
    # ----------------------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # ---- Barre d'outils supérieure ----
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        # Type de graphique
        toolbar.addWidget(QLabel("Type:"))
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems([
            "Courbes", "Barres", "Aires", "Points",
            "Histogramme", "Boxplot", "Camembert", "Tendance"
        ])
        self.plot_type_combo.currentIndexChanged.connect(self._on_plot_type_changed)
        toolbar.addWidget(self.plot_type_combo)

        # Intervalle d'agrégation
        toolbar.addWidget(QLabel("Intervalle:"))
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["1s", "5s", "10s", "30s", "1min", "5min"])
        self.interval_combo.setCurrentIndex(0)
        self.interval_combo.currentIndexChanged.connect(self._on_interval_changed)
        toolbar.addWidget(self.interval_combo)

        toolbar.addStretch()

        # Boutons d'action
        icon_color = QColor("#E2E8F0")  # Blanc cassé

        # Bouton Exporter PNG
        self.btn_export_png = QPushButton()
        self.btn_export_png.setIcon(load_svg_icon("export.svg", icon_color, 20))
        self.btn_export_png.setToolTip("Exporter le graphique en PNG")
        self.btn_export_png.setFixedSize(32, 32)
        self.btn_export_png.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.08);
                border-color: #2A3442;
            }
        """)
        self.btn_export_png.clicked.connect(self._export_png)
        toolbar.addWidget(self.btn_export_png)

        # Bouton Exporter SVG
        self.btn_export_svg = QPushButton()
        self.btn_export_svg.setIcon(load_svg_icon("export.svg", icon_color, 20))
        self.btn_export_svg.setToolTip("Exporter le graphique en SVG")
        self.btn_export_svg.setFixedSize(32, 32)
        self.btn_export_svg.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.08);
                border-color: #2A3442;
            }
        """)
        self.btn_export_svg.clicked.connect(self._export_svg)
        toolbar.addWidget(self.btn_export_svg)

        # Bouton Exporter CSV
        self.btn_export_csv = QPushButton()
        self.btn_export_csv.setIcon(load_svg_icon("export.svg", icon_color, 20))
        self.btn_export_csv.setToolTip("Exporter les données en CSV")
        self.btn_export_csv.setFixedSize(32, 32)
        self.btn_export_csv.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.08);
                border-color: #2A3442;
            }
        """)
        self.btn_export_csv.clicked.connect(self._export_csv)
        toolbar.addWidget(self.btn_export_csv)

        # Séparateur visuel
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setStyleSheet("color: #2A3442;")
        separator.setFixedWidth(1)
        toolbar.addWidget(separator)

        # Bouton Réinitialiser la vue
        self.btn_reset_view = QPushButton()
        self.btn_reset_view.setIcon(load_svg_icon("reset_view.svg", icon_color, 20))
        self.btn_reset_view.setToolTip("Réinitialiser le zoom et la plage temporelle")
        self.btn_reset_view.setFixedSize(32, 32)
        self.btn_reset_view.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.08);
                border-color: #2A3442;
            }
        """)
        self.btn_reset_view.clicked.connect(self._reset_view)
        toolbar.addWidget(self.btn_reset_view)

        # Bouton Statistiques
        self.btn_toggle_stats = QPushButton()
        self.btn_toggle_stats.setIcon(load_svg_icon("stats.svg", icon_color, 20))
        self.btn_toggle_stats.setToolTip("Afficher/masquer les statistiques détaillées")
        self.btn_toggle_stats.setCheckable(True)
        self.btn_toggle_stats.setFixedSize(32, 32)
        self.btn_toggle_stats.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.08);
                border-color: #2A3442;
            }
            QPushButton:checked {
                background: rgba(56, 189, 248, 0.15);
                border-color: #38BDF8;
            }
        """)
        self.btn_toggle_stats.toggled.connect(self._toggle_stats)
        toolbar.addWidget(self.btn_toggle_stats)

        # Ajouter la barre d'outils au layout principal
        layout.addLayout(toolbar)

        # ---- Corps principal (splitter) ----
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Panneau gauche : filtres espèces
        left_panel = QWidget()
        left_panel.setFixedWidth(200)
        left_panel.setStyleSheet("background: #1E293B; border-radius: 8px;")
        lp_layout = QVBoxLayout(left_panel)
        lp_layout.setContentsMargins(10, 10, 10, 10)
        lp_layout.setSpacing(6)

        lp_layout.addWidget(QLabel("Espèces :"))
        self._species_scroll = QScrollArea()
        self._species_scroll.setWidgetResizable(True)
        self._species_scroll.setStyleSheet("border: none; background: transparent;")
        self._species_container = QWidget()
        self._species_layout = QVBoxLayout(self._species_container)
        self._species_layout.setSpacing(3)
        self._species_layout.setAlignment(Qt.AlignTop)
        self._species_scroll.setWidget(self._species_container)
        lp_layout.addWidget(self._species_scroll)

        btn_all = QPushButton("Tout cocher")
        btn_all.setStyleSheet("color: #94A3B8; font-size: 11px; background: transparent; border: 1px solid #334155; border-radius: 4px; padding: 4px;")
        btn_all.clicked.connect(lambda: self._toggle_all(True))
        btn_none = QPushButton("Tout décocher")
        btn_none.setStyleSheet("color: #94A3B8; font-size: 11px; background: transparent; border: 1px solid #334155; border-radius: 4px; padding: 4px;")
        btn_none.clicked.connect(lambda: self._toggle_all(False))
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_all)
        btn_layout.addWidget(btn_none)
        lp_layout.addLayout(btn_layout)

        splitter.addWidget(left_panel)

        # Partie droite : graphique + éventuellement stats
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)

        # Canvas + NavigationToolbar
        self.figure = Figure(figsize=(8, 5), facecolor="#0F172A")
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.setStyleSheet("border: 1px solid #2A3442; border-radius: 8px;")
        right_layout.addWidget(self.canvas)

        # Barre de navigation matplotlib (zoom, déplacement)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setStyleSheet("background: #1E293B; border: none;")
        right_layout.addWidget(self.toolbar)

        # Zone de statistiques (cachée par défaut)
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(150)
        self.stats_text.setStyleSheet("""
            QTextEdit {
                background: #1E293B;
                color: #E2E8F0;
                border: 1px solid #2A3442;
                border-radius: 8px;
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
                padding: 8px;
            }
        """)
        self.stats_text.hide()
        right_layout.addWidget(self.stats_text)

        splitter.addWidget(right_widget)
        splitter.setSizes([200, 900])

        # Ajouter le splitter au layout principal
        layout.addWidget(splitter)

        # ---- Plage temporelle (bas) ----
        range_layout = QHBoxLayout()
        range_layout.setSpacing(8)
        range_layout.addWidget(QLabel("Début (s):"))
        self.time_min_spin = QDoubleSpinBox()
        self.time_min_spin.setRange(0, 100000)
        self.time_min_spin.setSingleStep(1.0)
        self.time_min_spin.setDecimals(1)
        self.time_min_spin.setSuffix(" s")
        self.time_min_spin.valueChanged.connect(self._on_time_range_changed)
        range_layout.addWidget(self.time_min_spin)

        range_layout.addWidget(QLabel("Fin (s):"))
        self.time_max_spin = QDoubleSpinBox()
        self.time_max_spin.setRange(0, 100000)
        self.time_max_spin.setSingleStep(1.0)
        self.time_max_spin.setDecimals(1)
        self.time_max_spin.setSuffix(" s")
        self.time_max_spin.valueChanged.connect(self._on_time_range_changed)
        range_layout.addWidget(self.time_max_spin)

        range_layout.addStretch()
        layout.addLayout(range_layout)

    # ----------------------------------------------------------------------
    # Méthodes internes
    # ----------------------------------------------------------------------
    def _get_interval_sec(self) -> int:
        """Convertit le texte de l'intervalle en secondes."""
        text = self.interval_combo.currentText()
        mapping = {"1s": 1, "5s": 5, "10s": 10, "30s": 30, "1min": 60, "5min": 300}
        return mapping.get(text, 1)

    def _on_plot_type_changed(self):
        types = ["line", "bar", "area", "scatter", "hist", "box", "pie", "trend"]
        self._current_plot_type = types[self.plot_type_combo.currentIndex()]
        self._draw()

    def _on_interval_changed(self):
        self._interval_sec = self._get_interval_sec()
        if self._mgr and self._mgr.has_data:
            self._mgr._calculate_temporal_aggregation(interval_sec=self._interval_sec)
            self._update_time_range()
            self._draw()

    def _on_time_range_changed(self):
        self._time_min = self.time_min_spin.value()
        self._time_max = self.time_max_spin.value()
        self._draw()

    def _update_time_range(self):
        """Met à jour les spinbox de plage temporelle à partir des données."""
        if self._mgr and self._mgr.has_data and not self._mgr.df_temporal_agg.empty:
            df = self._mgr.df_temporal_agg
            min_t = df['time_bin'].min()
            max_t = df['time_bin'].max()
            self._time_min = min_t
            self._time_max = max_t
            self.time_min_spin.blockSignals(True)
            self.time_max_spin.blockSignals(True)
            self.time_min_spin.setRange(min_t, max_t)
            self.time_max_spin.setRange(min_t, max_t)
            self.time_min_spin.setValue(min_t)
            self.time_max_spin.setValue(max_t)
            self.time_min_spin.blockSignals(False)
            self.time_max_spin.blockSignals(False)

    def _toggle_stats(self, checked):
        self.stats_text.setVisible(checked)

    def _reset_view(self):
        """Réinitialise la vue (zoom, plage)."""
        self.canvas.figure.axes[0].relim()
        self.canvas.figure.axes[0].autoscale()
        self.canvas.draw()
        self._update_time_range()
        self._draw()

    def _export_png(self):
        self._export_figure("PNG", "png")

    def _export_svg(self):
        self._export_figure("SVG", "svg")

    def _export_figure(self, name, ext):
        if not self._mgr or not self._mgr.has_data:
            QMessageBox.warning(self, "Aucune donnée", "Aucune donnée à exporter.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, f"Exporter en {name}",
            f"temporal_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}",
            f"{name} (*.{ext})"
        )
        if path:
            self.figure.savefig(path, dpi=300, bbox_inches='tight')
            QMessageBox.information(self, "Export réussi", f"Fichier sauvegardé : {path}")

    def _export_csv(self):
        if not self._mgr or not self._mgr.has_data:
            QMessageBox.warning(self, "Aucune donnée", "Aucune donnée à exporter.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter en CSV",
            f"temporal_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV (*.csv)"
        )
        if path:
            df = self._mgr.get_temporal_data(interval_sec=self._interval_sec)
            df.to_csv(path, index=False)
            QMessageBox.information(self, "Export réussi", f"Données sauvegardées : {path}")

    # ----------------------------------------------------------------------
    # Rafraîchissement et dessin
    # ----------------------------------------------------------------------
    def refresh(self):
        """Recharge les données et redessine le graphique."""
        self._rebuild_species_filters()
        if self._mgr and self._mgr.has_data:
            self._mgr._calculate_temporal_aggregation(interval_sec=self._interval_sec)
            self._update_time_range()
        self._draw()

    def _rebuild_species_filters(self):
        while self._species_layout.count():
            item = self._species_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._species_checks.clear()

        if self._mgr and self._mgr.has_data:
            species_list = self._mgr.get_class_names()
            for i, sp in enumerate(species_list):
                cb = QCheckBox(sp)
                cb.setChecked(True)
                cb.setStyleSheet(f"""
                    QCheckBox {{
                        color: #E2E8F0;
                        font-size: 12px;
                        spacing: 4px;
                    }}
                    QCheckBox::indicator {{
                        width: 14px; height: 14px;
                        border: 1px solid #2A3442;
                        border-radius: 3px;
                        background: #0F172A;
                    }}
                    QCheckBox::indicator:checked {{
                        background: {COLORS[i % len(COLORS)]};
                        border: 1px solid {COLORS[i % len(COLORS)]};
                    }}
                """)
                cb.stateChanged.connect(self._draw)
                self._species_checks[sp] = cb
                self._species_layout.addWidget(cb)

        if not self._species_checks:
            lbl = QLabel("Aucune espèce")
            lbl.setStyleSheet("color: #94A3B8; font-size: 11px;")
            self._species_layout.addWidget(lbl)

    def _toggle_all(self, checked):
        for cb in self._species_checks.values():
            cb.setChecked(checked)

    def _selected_species(self) -> List[str]:
        return [sp for sp, cb in self._species_checks.items() if cb.isChecked()]

    def _draw(self):
        fig = self.figure
        fig.clear()

        if not self._mgr or not self._mgr.has_data:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, "Aucune donnée disponible.\nLancez une analyse vidéo.",
                    ha="center", va="center", color="#94A3B8", fontsize=12,
                    transform=ax.transAxes)
            ax.set_facecolor("#0F172A")
            fig.tight_layout()
            self.canvas.draw()
            return

        selected = self._selected_species()
        if not selected:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, "Sélectionnez au moins une espèce.",
                    ha="center", va="center", color="#94A3B8", fontsize=12,
                    transform=ax.transAxes)
            ax.set_facecolor("#0F172A")
            fig.tight_layout()
            self.canvas.draw()
            return

        df = self._mgr.get_temporal_data(interval_sec=self._interval_sec)
        if df.empty:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, "Données temporelles vides.",
                    ha="center", va="center", color="#94A3B8", fontsize=12,
                    transform=ax.transAxes)
            ax.set_facecolor("#0F172A")
            fig.tight_layout()
            self.canvas.draw()
            return

        # Filtrer par plage temporelle
        df = df[(df['time_bin'] >= self._time_min) & (df['time_bin'] <= self._time_max)]
        if df.empty:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, "Aucune donnée dans la plage temporelle sélectionnée.",
                    ha="center", va="center", color="#94A3B8", fontsize=12,
                    transform=ax.transAxes)
            ax.set_facecolor("#0F172A")
            fig.tight_layout()
            self.canvas.draw()
            return

        # Pivot pour avoir les espèces en colonnes
        df_pivot = df.pivot(index='time_bin', columns='class_name', values='count').fillna(0)

        # Sélectionner seulement les espèces sélectionnées
        df_pivot = df_pivot[[sp for sp in selected if sp in df_pivot.columns]]

        if df_pivot.empty:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, "Aucune donnée pour les espèces sélectionnées.",
                    ha="center", va="center", color="#94A3B8", fontsize=12,
                    transform=ax.transAxes)
            ax.set_facecolor("#0F172A")
            fig.tight_layout()
            self.canvas.draw()
            return

        # Créer le sous-graphique
        ax = fig.add_subplot(111)
        ax.set_facecolor("#0F172A")
        ax.tick_params(colors='#94A3B8')
        ax.xaxis.label.set_color('#E2E8F0')
        ax.yaxis.label.set_color('#E2E8F0')
        ax.title.set_color('#E2E8F0')

        plot_type = self._current_plot_type

        if plot_type == "line":
            df_pivot.plot(ax=ax, kind='line', marker='o', markersize=4, linewidth=2,
                          color=[COLORS[i % len(COLORS)] for i in range(len(df_pivot.columns))])
        elif plot_type == "bar":
            df_pivot.plot(ax=ax, kind='bar', stacked=False, width=0.8,
                          color=[COLORS[i % len(COLORS)] for i in range(len(df_pivot.columns))])
        elif plot_type == "area":
            df_pivot.plot(ax=ax, kind='area', stacked=True, alpha=0.6,
                          color=[COLORS[i % len(COLORS)] for i in range(len(df_pivot.columns))])
        elif plot_type == "scatter":
            for i, col in enumerate(df_pivot.columns):
                ax.scatter(df_pivot.index, df_pivot[col], label=col, s=30,
                           color=COLORS[i % len(COLORS)], alpha=0.7)
        elif plot_type == "hist":
            df_pivot.plot(ax=ax, kind='hist', bins=20, alpha=0.6, legend=True,
                          color=[COLORS[i % len(COLORS)] for i in range(len(df_pivot.columns))])
            ax.set_xlabel("Nombre de détections")
            ax.set_ylabel("Fréquence")
            ax.set_title("Distribution des détections par espèce")
        elif plot_type == "box":
            df_pivot.boxplot(ax=ax, patch_artist=True,
                             boxprops=dict(facecolor='#1E293B', color='#38BDF8'),
                             whiskerprops=dict(color='#38BDF8'),
                             capprops=dict(color='#38BDF8'),
                             medianprops=dict(color='#F97316'))
            ax.set_ylabel("Nombre de détections")
            ax.set_title("Distribution des détections par espèce (boxplot)")
            ax.tick_params(axis='x', rotation=45)
        elif plot_type == "pie":
            # Camembert : on utilise les totaux par espèce sur toute la période
            totals = df_pivot.sum(axis=0)
            if totals.sum() == 0:
                ax.text(0.5, 0.5, "Aucune détection pour le camembert.",
                        ha="center", va="center", color="#94A3B8", transform=ax.transAxes)
            else:
                ax.pie(totals, labels=totals.index, autopct='%1.1f%%',
                       colors=[COLORS[i % len(COLORS)] for i in range(len(totals))],
                       wedgeprops=dict(edgecolor='#0F172A', linewidth=1))
                ax.set_title("Répartition des détections par espèce")
        elif plot_type == "trend":
            for i, col in enumerate(df_pivot.columns):
                y = df_pivot[col].values
                x = df_pivot.index.values
                ax.plot(x, y, marker='o', label=col, color=COLORS[i % len(COLORS)])
                if len(y) > 2:
                    coeffs = np.polyfit(x, y, 2)
                    poly = np.poly1d(coeffs)
                    ax.plot(x, poly(x), '--', alpha=0.7,
                            color=COLORS[i % len(COLORS)], linewidth=2, label=f"{col} (tendance)")
            ax.set_ylabel("Abondance")
            ax.set_title("Tendances temporelles")

        # Légende
        if plot_type not in ["pie", "box", "hist"]:
            ax.legend(loc='upper left', fontsize=8, framealpha=0.6, facecolor='#1E293B', edgecolor='#2A3442')

        ax.grid(True, linestyle='--', alpha=0.3, color='#2A3442')
        ax.set_xlabel("Temps (s)")
        ax.set_ylabel("Nombre de détections")
        if plot_type not in ["pie", "box", "hist"]:
            ax.set_title("Évolution temporelle des détections")

        fig.tight_layout()
        self.canvas.draw()

        # Mettre à jour les statistiques
        self._update_stats(df_pivot)

    def _update_stats(self, df_pivot):
        """Calcule et affiche les statistiques dans la zone de texte."""
        if not self.btn_toggle_stats.isChecked():
            return
        stats_lines = []
        stats_lines.append("📊 Statistiques par espèce :")
        stats_lines.append("")
        for col in df_pivot.columns:
            series = df_pivot[col]
            stats_lines.append(f"  {col}:")
            stats_lines.append(f"    Total  : {int(series.sum())}")
            stats_lines.append(f"    Moyenne: {series.mean():.2f}")
            stats_lines.append(f"    Écart-type: {series.std():.2f}")
            stats_lines.append(f"    Min    : {int(series.min())}")
            stats_lines.append(f"    Max    : {int(series.max())}")
            stats_lines.append("")
        self.stats_text.setText("\n".join(stats_lines))
