# core/tracker_wrapper.py
import numpy as np
import supervision as sv
from trackers.core.botsort.tracker import BoTSORTTracker


class BoTSORTWrapper:
    """
    Enveloppe autour de BoT‑SORT pour l’intégrer facilement au pipeline FishID.

    - Convertit les détections FishID en objets `sv.Detections`.
    - Renvoie une liste de dictionnaires avec `track_id` ajouté.
    - Gère proprement les cas où il n’y a aucune détection.
    - Propose une réinitialisation et un accès aux paramètres de suivi.
    """

    def __init__(
        self,
        lost_track_buffer: int = 30,
        frame_rate: float = 30.0,
        track_activation_threshold: float = 0.7,
        minimum_consecutive_frames: int = 2,
        minimum_iou_threshold_first_assoc: float = 0.2,
        minimum_iou_threshold_second_assoc: float = 0.5,
        minimum_iou_threshold_unconfirmed_assoc: float = 0.3,
        high_conf_det_threshold: float = 0.6,
        enable_cmc: bool = True,
        cmc_method: str = "sparseOptFlow",
        cmc_downscale: int = 2,
        instant_first_frame_activation: bool = True,
    ):
        # Stocker les paramètres pour référence future
        self._params = {k: v for k, v in locals().items() if k != 'self'}

        self.tracker = BoTSORTTracker(
            lost_track_buffer=lost_track_buffer,
            frame_rate=frame_rate,
            track_activation_threshold=track_activation_threshold,
            minimum_consecutive_frames=minimum_consecutive_frames,
            minimum_iou_threshold_first_assoc=minimum_iou_threshold_first_assoc,
            minimum_iou_threshold_second_assoc=minimum_iou_threshold_second_assoc,
            minimum_iou_threshold_unconfirmed_assoc=minimum_iou_threshold_unconfirmed_assoc,
            high_conf_det_threshold=high_conf_det_threshold,
            enable_cmc=enable_cmc,
            cmc_method=cmc_method,
            cmc_downscale=cmc_downscale,
            instant_first_frame_activation=instant_first_frame_activation,
        )

    def update(self, detections: list, frame: np.ndarray) -> list:
        """
        Args:
            detections: liste de dicts FishID (bbox, confidence, class_id, class_name)
            frame: image BGR (utilisée pour la compensation de mouvement de caméra)

        Returns:
            liste de dicts contenant en plus 'track_id'
        """
        # --- Cas sans détection ---
        if not detections:
            self.tracker.update(sv.Detections.empty(), frame)
            return []

        # --- Conversion vers sv.Detections ---
        xyxy = np.array([d['bbox'] for d in detections], dtype=np.float32)
        conf = np.array([d.get('confidence', 1.0) for d in detections], dtype=np.float32)
        class_id = np.array([d.get('class_id', 0) for d in detections], dtype=int)

        sv_dets = sv.Detections(
            xyxy=xyxy,
            confidence=conf,
            class_id=class_id,
        )

        # --- Mise à jour du tracker ---
        tracked_dets = self.tracker.update(sv_dets, frame)

        if len(tracked_dets) == 0:
            return []

        # --- Reconstruction de la sortie ---
        out_dets = []
        for i in range(len(tracked_dets)):
            bbox = tracked_dets.xyxy[i].tolist()
            confidence = float(tracked_dets.confidence[i]) if tracked_dets.confidence is not None else 0.0
            class_id = int(tracked_dets.class_id[i]) if tracked_dets.class_id is not None else -1
            track_id = int(tracked_dets.tracker_id[i])

            out_dets.append({
                'bbox': [int(v) for v in bbox],
                'confidence': confidence,
                'class_id': class_id,
                'class_name': '',   # sera rempli plus tard par la classification fine
                'track_id': track_id,
            })
        return out_dets

    def reset(self):
        """Réinitialise l'état du tracker (pour une nouvelle vidéo)."""
        self.tracker.reset()

    @property
    def params(self) -> dict:
        """Retourne les paramètres de suivi actuels."""
        return self._params