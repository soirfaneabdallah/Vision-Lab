# fishid/core/analysis_manager.py
import pandas as pd
import numpy as np
from collections import defaultdict
from fishid.core.detection import Detection


class AnalysisDataManager:
    def __init__(self):
        self.detections_history: list[list[Detection]] = []
        # Initialiser avec des DataFrames vides
        self.df_detections = pd.DataFrame()
        self.df_temporal_agg = pd.DataFrame()
        self.all_class_names = set()
        self.current_interval = 1

    def load_detections(self, history: list[list[Detection]]):
        """Charge l'historique des détections et prépare les DataFrames."""
        self.detections_history = history
        self.all_class_names = set()

        data = []
        for frame_detections in history:
            for detection in frame_detections:
                data.append({
                    'frame_idx': detection.frame_idx,
                    'timestamp_ms': detection.timestamp_ms,
                    'class_id': detection.class_id,
                    'class_name': detection.class_name,
                    'confidence': detection.confidence,
                    'bbox': detection.bbox,
                    'x_min': detection.bbox[0],
                    'y_min': detection.bbox[1],
                    'x_max': detection.bbox[2],
                    'y_max': detection.bbox[3]
                })
                self.all_class_names.add(detection.class_name)

        if not data:
            self.df_detections = pd.DataFrame()
            self.df_temporal_agg = pd.DataFrame()
            return

        self.df_detections = pd.DataFrame(data)
        self.df_detections['timestamp_sec'] = self.df_detections['timestamp_ms'] / 1000.0
        self.df_detections.sort_values(by='timestamp_sec', inplace=True)

        self._calculate_temporal_aggregation(interval_sec=self.current_interval)

    def _calculate_temporal_aggregation(self, interval_sec: int = 1):
        """Agrège les détections par intervalles de temps."""
        self.current_interval = interval_sec

        if self.df_detections is None or self.df_detections.empty:
            self.df_temporal_agg = pd.DataFrame()
            return

        min_time = self.df_detections['timestamp_sec'].min()
        max_time = self.df_detections['timestamp_sec'].max()

        if min_time == max_time:
            bins = [min_time, max_time + 0.1]
        else:
            bins = np.arange(min_time, max_time + interval_sec, interval_sec)

        if len(bins) < 2:
            bins = [min_time, max_time + 0.1]

        self.df_detections['time_bin'] = pd.cut(
            self.df_detections['timestamp_sec'],
            bins=bins,
            labels=bins[:-1],
            right=False,
            include_lowest=True
        )

        temporal_counts = self.df_detections.groupby(['time_bin', 'class_name']).size()
        self.df_temporal_agg = temporal_counts.reset_index(name='count')

        # Remplir les valeurs manquantes
        all_time_bins = pd.Index(bins[:-1], name='time_bin')
        all_class_names_index = pd.Index(sorted(list(self.all_class_names)), name='class_name')
        multi_index = pd.MultiIndex.from_product(
            [all_time_bins, all_class_names_index],
            names=['time_bin', 'class_name']
        )

        self.df_temporal_agg = (
            self.df_temporal_agg
            .set_index(['time_bin', 'class_name'])
            .reindex(multi_index, fill_value=0)
            .reset_index()
        )

        self.df_temporal_agg['time_bin'] = pd.to_numeric(self.df_temporal_agg['time_bin'])

    def get_temporal_data(self, interval_sec: int = 1) -> pd.DataFrame:
        """Retourne les données agrégées temporelles."""
        if self.df_temporal_agg is None or self.df_temporal_agg.empty or self.current_interval != interval_sec:
            self._calculate_temporal_aggregation(interval_sec=interval_sec)
        return self.df_temporal_agg if self.df_temporal_agg is not None else pd.DataFrame()

    def get_class_names(self) -> list:
        """Retourne la liste des noms de classes."""
        return sorted(list(self.all_class_names))

    @property
    def species_list(self):
        """Alias de get_class_names pour compatibilité avec le widget."""
        return self.get_class_names()

    @property
    def has_data(self) -> bool:
        """Indique si des données de détection sont disponibles."""
        return not self.df_detections.empty