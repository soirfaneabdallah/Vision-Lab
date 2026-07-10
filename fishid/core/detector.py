"""
fishid/core/detector.py
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import onnxruntime as ort
from PySide6.QtCore import QObject, Signal


# ── Logger dédié ──────────────────────────────────────────────────────────────
logger = logging.getLogger("VisionLab.Detector")


# ─────────────────────────────────────────────────────────────────────────────
# DATACLASSES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Detection:
    """
    Résultat d'une détection individuelle.

    Attributs :
        bbox         : [x1, y1, x2, y2] dans l'espace de l'image originale (pixels)
        confidence   : score de confiance final  [0, 1]
        class_id     : indice de classe
        class_name   : nom de la classe
        bbox_norm    : [x1, y1, x2, y2] normalisé [0, 1]  (calculé automatiquement)
        area         : surface de la boîte en pixels carrés
        center       : (cx, cy) centre de la boîte
    """
    bbox:       List[int]
    confidence: float
    class_id:   int
    class_name: str
    bbox_norm:  List[float] = field(default_factory=list)
    area:       int         = 0
    center:     Tuple[int, int] = (0, 0)

    def __post_init__(self):
        x1, y1, x2, y2 = self.bbox
        self.area   = max(0, (x2 - x1) * (y2 - y1))
        self.center = ((x1 + x2) // 2, (y1 + y2) // 2)

    def to_dict(self) -> Dict:
        return {
            "bbox":       self.bbox,
            "confidence": round(self.confidence, 4),
            "class_id":   self.class_id,
            "class_name": self.class_name,
            "bbox_norm":  [round(v, 4) for v in self.bbox_norm],
            "area":       self.area,
            "center":     list(self.center),
        }

    def __repr__(self) -> str:
        x1, y1, x2, y2 = self.bbox
        return (f"Detection({self.class_name!r} "
                f"conf={self.confidence:.3f} "
                f"box=[{x1},{y1},{x2},{y2}] "
                f"area={self.area}px²)")


@dataclass
class DetectorMetrics:
    """Métriques de performance du détecteur."""
    total_frames:      int   = 0
    total_detections:  int   = 0
    inference_times_ms: deque = field(default_factory=lambda: deque(maxlen=100))

    @property
    def avg_inference_ms(self) -> float:
        return float(np.mean(self.inference_times_ms)) if self.inference_times_ms else 0.0

    @property
    def min_inference_ms(self) -> float:
        return float(np.min(self.inference_times_ms)) if self.inference_times_ms else 0.0

    @property
    def max_inference_ms(self) -> float:
        return float(np.max(self.inference_times_ms)) if self.inference_times_ms else 0.0

    @property
    def fps(self) -> float:
        return 1000.0 / self.avg_inference_ms if self.avg_inference_ms > 0 else 0.0

    @property
    def avg_detections_per_frame(self) -> float:
        return self.total_detections / self.total_frames if self.total_frames > 0 else 0.0

    def record(self, elapsed_ms: float, n_detections: int):
        self.inference_times_ms.append(elapsed_ms)
        self.total_frames    += 1
        self.total_detections += n_detections

    def summary(self) -> Dict:
        return {
            "frames":            self.total_frames,
            "detections":        self.total_detections,
            "fps":               round(self.fps, 1),
            "avg_ms":            round(self.avg_inference_ms, 2),
            "min_ms":            round(self.min_inference_ms, 2),
            "max_ms":            round(self.max_inference_ms, 2),
            "avg_dets_per_frame": round(self.avg_detections_per_frame, 2),
        }

    def reset(self):
        self.__init__()


@dataclass
class ExclusionZone:
    """Zone rectangulaire à ignorer lors de la détection (coordonnées normalisées [0,1])."""
    x1_norm: float
    y1_norm: float
    x2_norm: float
    y2_norm: float
    label:   str = "exclusion"

    def contains_center(self, cx_norm: float, cy_norm: float) -> bool:
        return (self.x1_norm <= cx_norm <= self.x2_norm and
                self.y1_norm <= cy_norm <= self.y2_norm)


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES VISUELLES
# ─────────────────────────────────────────────────────────────────────────────

# Couleurs BGR par plage de confiance
_CONF_COLORS = [
    (0.85, (0,   230, 100)),   # > 0.85  → vert vif
    (0.70, (0,   200, 255)),   # > 0.70  → cyan/jaune
    (0.55, (0,   140, 255)),   # > 0.55  → orange
    (0.00, (0,    80, 220)),   # reste   → rouge/bordeaux
]

# Palette de 80 couleurs distinctes (BGR) pour les classes
_CLASS_PALETTE: List[Tuple[int,int,int]] = []
for _i in range(80):
    _h = int(_i * 179 / 80)          # OpenCV HSV : H ∈ [0, 179]
    _hsv = np.array([[[_h, 220, 200]]], dtype=np.uint8)
    _rgb = cv2.cvtColor(_hsv, cv2.COLOR_HSV2BGR)[0][0]
    _CLASS_PALETTE.append((int(_rgb[0]), int(_rgb[1]), int(_rgb[2])))


def _conf_color(conf: float) -> Tuple[int, int, int]:
    for threshold, color in _CONF_COLORS:
        if conf >= threshold:
            return color
    return _CONF_COLORS[-1][1]


def _class_color(class_id: int) -> Tuple[int, int, int]:
    return _CLASS_PALETTE[class_id % len(_CLASS_PALETTE)]


# ─────────────────────────────────────────────────────────────────────────────
# DÉTECTEUR PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

class FishDetector(QObject):
    """
    Détecteur haute performance pour espèces marines et déchets.

    Signaux Qt :
        detection_complete(list[dict])  : détections de la frame courante
        model_loaded(str)               : provider utilisé au chargement
        error_occurred(str)             : message d'erreur
        status_message(str)             : message d'information
        metrics_updated(dict)           : métriques toutes les N frames

    Utilisation minimale :
        detector = FishDetector("models/detect.onnx")
        detector.load_model(use_gpu=True)
        detections = detector.detect(frame)   # list[Detection]

    Utilisation avancée :
        detector.set_class_thresholds({"Mérou brun": 0.65, "Plastique": 0.5})
        detector.add_exclusion_zone(ExclusionZone(0.0, 0.0, 0.2, 1.0, "bord gauche"))
        annotated, dets = detector.detect_and_draw(frame, show_metrics=True)
    """

    # ── Signaux ───────────────────────────────────────────────────────────────
    detection_complete = Signal(list)   # list[dict]
    model_loaded       = Signal(str)    # provider
    error_occurred     = Signal(str)
    status_message     = Signal(str)
    metrics_updated    = Signal(dict)

    # ── Constantes ────────────────────────────────────────────────────────────
    WARMUP_FRAMES        = 3
    METRICS_EMIT_EVERY   = 30   # frames
    MIN_BOX_PIXEL        = 8    # pixels — boîtes plus petites ignorées
    LETTERBOX_COLOR      = (114, 114, 114)  # gris standard YOLO

    def __init__(
        self,
        model_path: str = "models/detect.onnx",
        conf_threshold: float = 0.45,
        iou_threshold:  float = 0.45,
        input_size:     int   = 640,
        class_names:    Optional[List[str]] = None,
    ):
        super().__init__()

        self.model_path     = Path(model_path)
        self.conf_threshold = float(np.clip(conf_threshold, 0.01, 0.99))
        self.iou_threshold  = float(np.clip(iou_threshold,  0.01, 0.99))
        self.input_size     = input_size   # forcé carré si int, sinon (w,h)
        self.class_names    = class_names or ["fish"]

        # Seuils par classe (écrase conf_threshold pour une classe donnée)
        self._class_thresholds: Dict[str, float] = {}

        # Zones d'exclusion
        self._exclusion_zones: List[ExclusionZone] = []

        # État interne
        self.session:      Optional[ort.InferenceSession] = None
        self._input_name:  str  = ""
        self._input_w:     int  = input_size
        self._input_h:     int  = input_size
        self._output_fmt:  str  = "yolov8"   # "yolov8" | "yolov5"
        self._n_classes:   int  = len(self.class_names)
        self._is_loaded:   bool = False
        self._provider:    str  = "CPUExecutionProvider"

        # Métriques
        self.metrics = DetectorMetrics()
        self._frame_counter = 0

        logger.debug("FishDetector initialisé — modèle : %s", self.model_path)

    # ═════════════════════════════════════════════════════════════════════════
    # CHARGEMENT
    # ═════════════════════════════════════════════════════════════════════════

    def load_model(self, use_gpu: bool = False) -> bool:
        """
        Charge le modèle ONNX avec le meilleur provider disponible.

        Ordre de priorité : CUDA → DirectML → CoreML → CPU
        Retourne True si le chargement réussit.
        """
        if not self.model_path.exists():
            msg = f"Modèle introuvable : {self.model_path}"
            logger.error(msg)
            self.error_occurred.emit(msg)
            return False

        providers = self._resolve_providers(use_gpu)

        for provider in providers:
            try:
                opts = ort.SessionOptions()
                opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
                opts.enable_mem_pattern       = True
                opts.enable_cpu_mem_arena     = True
                opts.intra_op_num_threads     = 0   # 0 = auto

                self.session = ort.InferenceSession(
                    str(self.model_path),
                    sess_options=opts,
                    providers=[provider],
                )
                self._provider = provider
                break
            except Exception as exc:
                logger.warning("Provider %s indisponible : %s", provider, exc)
                continue

        if self.session is None:
            msg = "Aucun provider ONNX disponible."
            logger.error(msg)
            self.error_occurred.emit(msg)
            return False

        # Récupérer les métadonnées du modèle
        inp  = self.session.get_inputs()[0]
        self._input_name = inp.name
        shape = inp.shape   # [batch, C, H, W] ou [batch, C, W, H]

        if len(shape) == 4:
            # Dimensions dynamiques (-1 ou None) → garder input_size
            self._input_h = shape[2] if isinstance(shape[2], int) and shape[2] > 0 else self.input_size
            self._input_w = shape[3] if isinstance(shape[3], int) and shape[3] > 0 else self.input_size

        # Détecter le format de sortie
        self._detect_output_format()

        # Warm-up (3 frames noires)
        self._warmup()

        self._is_loaded = True
        msg = f"✅ Détecteur chargé — {self._provider} | {self._input_w}×{self._input_h} | fmt={self._output_fmt}"
        logger.info(msg)
        self.status_message.emit(msg)
        self.model_loaded.emit(self._provider)
        return True

    def _resolve_providers(self, use_gpu: bool) -> List[str]:
        available = ort.get_available_providers()
        candidates = (
            ["CUDAExecutionProvider",
             "DmlExecutionProvider",
             "CoreMLExecutionProvider",
             "CPUExecutionProvider"]
            if use_gpu else
            ["CPUExecutionProvider"]
        )
        return [p for p in candidates if p in available] or ["CPUExecutionProvider"]

    def _detect_output_format(self):
        """Détermine automatiquement le format de sortie du modèle."""
        out = self.session.get_outputs()[0]
        shape = out.shape   # ex. [1, 84, 8400] ou [1, 25200, 85]
        if len(shape) == 3:
            if isinstance(shape[1], int) and shape[1] < 10:
                # [batch, 4+nc, n_anchors]
                self._output_fmt = "yolov8"
                self._n_classes  = shape[1] - 4
            elif isinstance(shape[2], int):
                # [batch, n_anchors, 5+nc]
                self._output_fmt = "yolov5"
                self._n_classes  = shape[2] - 5
        logger.debug("Format sortie : %s — %d classes", self._output_fmt, self._n_classes)

    def _warmup(self):
        """3 inférences à vide pour initialiser les allocations CUDA/ONNX."""
        dummy = np.zeros((1, 3, self._input_h, self._input_w), dtype=np.float32)
        for i in range(self.WARMUP_FRAMES):
            try:
                self.session.run(None, {self._input_name: dummy})
            except Exception:
                break
        logger.debug("Warm-up terminé (%d frames)", self.WARMUP_FRAMES)

    # ═════════════════════════════════════════════════════════════════════════
    # API PUBLIQUE — DÉTECTION
    # ═════════════════════════════════════════════════════════════════════════

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Détecte les objets dans `frame` (BGR, uint8).
        Retourne une liste de Detection, ordonnée par confiance décroissante.
        Émet detection_complete(list[dict]).
        """
        if not self._is_loaded or self.session is None:
            self.error_occurred.emit("Modèle non chargé. Appelez load_model() d'abord.")
            return []

        t0 = time.perf_counter()

        original_h, original_w = frame.shape[:2]

        # 1. Prétraitement letterbox
        blob, pad_info = self._letterbox_preprocess(frame)

        # 2. Inférence
        try:
            raw_output = self.session.run(None, {self._input_name: blob})[0]
        except Exception as exc:
            logger.error("Erreur inférence : %s", exc)
            self.error_occurred.emit(f"Erreur inférence : {exc}")
            return []

        # 3. Post-traitement
        detections = self._postprocess(
            raw_output, original_w, original_h, pad_info)

        # 4. Filtrage zones d'exclusion
        if self._exclusion_zones:
            detections = self._filter_exclusion_zones(
                detections, original_w, original_h)

        # 5. Tri final par confiance
        detections.sort(key=lambda d: d.confidence, reverse=True)

        # 6. Métriques
        elapsed_ms = (time.perf_counter() - t0) * 1000
        self.metrics.record(elapsed_ms, len(detections))
        self._frame_counter += 1

        if self._frame_counter % self.METRICS_EMIT_EVERY == 0:
            self.metrics_updated.emit(self.metrics.summary())

        # 7. Signal Qt
        self.detection_complete.emit([d.to_dict() for d in detections])

        logger.debug(
            "Frame %d : %d détections en %.1f ms",
            self._frame_counter, len(detections), elapsed_ms)

        return detections

    def detect_and_draw(
        self,
        frame: np.ndarray,
        use_class_colors: bool = True,
        show_conf: bool = True,
        show_label: bool = True,
        show_metrics: bool = False,
        thickness: int = 2,
        font_scale: float = 0.52,
    ) -> Tuple[np.ndarray, List[Detection]]:
        """
        Détecte et annote la frame.
        Retourne (frame_annotée, list[Detection]).
        """
        detections = self.detect(frame)
        annotated  = self._draw_boxes(
            frame.copy(), detections,
            use_class_colors=use_class_colors,
            show_conf=show_conf,
            show_label=show_label,
            thickness=thickness,
            font_scale=font_scale,
        )
        if show_metrics and self.metrics.total_frames > 0:
            annotated = self._draw_metrics_overlay(annotated)

        return annotated, detections

    def detect_objects(self, frame: np.ndarray) -> List[Dict]:
        """
        Alias compatible avec l'ancienne API (retourne list[dict]).
        Utilisé par VideoHandler._process_frame().
        """
        return [d.to_dict() for d in self.detect(frame)]

    # ═════════════════════════════════════════════════════════════════════════
    # CONFIGURATION AVANCÉE
    # ═════════════════════════════════════════════════════════════════════════

    def set_class_names(self, names: List[str]) -> None:
        self.class_names = names
        self._n_classes  = len(names)

    def set_conf_threshold(self, threshold: float) -> None:
        self.conf_threshold = float(np.clip(threshold, 0.01, 0.99))

    def set_iou_threshold(self, threshold: float) -> None:
        self.iou_threshold = float(np.clip(threshold, 0.01, 0.99))

    def set_class_thresholds(self, thresholds: Dict[str, float]) -> None:
        """
        Définit des seuils de confiance par classe.
        Ex. : detector.set_class_thresholds({"Mérou brun": 0.65, "Plastique": 0.5})
        """
        self._class_thresholds = {
            k: float(np.clip(v, 0.01, 0.99))
            for k, v in thresholds.items()
        }

    def add_exclusion_zone(self, zone: ExclusionZone) -> None:
        """Ajoute une zone à ignorer (coordonnées normalisées [0,1])."""
        self._exclusion_zones.append(zone)
        logger.info("Zone d'exclusion ajoutée : %s", zone.label)

    def clear_exclusion_zones(self) -> None:
        self._exclusion_zones.clear()

    def reset_metrics(self) -> None:
        self.metrics.reset()
        self._frame_counter = 0

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @property
    def provider(self) -> str:
        return self._provider

    # ═════════════════════════════════════════════════════════════════════════
    # PRÉTRAITEMENT
    # ═════════════════════════════════════════════════════════════════════════

    def _letterbox_preprocess(
        self, frame: np.ndarray
    ) -> Tuple[np.ndarray, Dict]:
        """
        Resize avec letterbox (conserve le ratio d'aspect).
        Retourne (blob [1,3,H,W], pad_info).

        pad_info :
            scale   : facteur de redimensionnement appliqué
            pad_top : pixels de padding ajoutés en haut
            pad_left: pixels de padding ajoutés à gauche
        """
        target_h, target_w = self._input_h, self._input_w
        src_h, src_w = frame.shape[:2]

        scale = min(target_w / src_w, target_h / src_h)
        new_w = int(round(src_w * scale))
        new_h = int(round(src_h * scale))

        resized = cv2.resize(frame, (new_w, new_h),
                             interpolation=cv2.INTER_LINEAR)

        # Centrer dans un canvas gris
        canvas = np.full((target_h, target_w, 3),
                         self.LETTERBOX_COLOR, dtype=np.uint8)
        pad_top  = (target_h - new_h) // 2
        pad_left = (target_w - new_w) // 2
        canvas[pad_top:pad_top + new_h, pad_left:pad_left + new_w] = resized

        # BGR → RGB, HWC → CHW, normalisation [0,1]
        blob = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        blob = np.transpose(blob, (2, 0, 1))[np.newaxis]   # (1, 3, H, W)

        pad_info = {"scale": scale, "pad_top": pad_top, "pad_left": pad_left}
        return blob, pad_info

    # ═════════════════════════════════════════════════════════════════════════
    # POST-TRAITEMENT
    # ═════════════════════════════════════════════════════════════════════════

    def _postprocess(
        self,
        output:     np.ndarray,
        orig_w:     int,
        orig_h:     int,
        pad_info:   Dict,
    ) -> List[Detection]:
        """
        Décode les sorties brutes ONNX selon le format détecté,
        applique le filtrage par confiance et la NMS vectorisée.
        """
        if self._output_fmt == "yolov8":
            return self._decode_yolov8(output, orig_w, orig_h, pad_info)
        else:
            return self._decode_yolov5(output, orig_w, orig_h, pad_info)

    # ── Décodeur YOLOv8 / YOLOv11 ─────────────────────────────────────────────

    def _decode_yolov8(
        self, output: np.ndarray,
        orig_w: int, orig_h: int, pad_info: Dict,
    ) -> List[Detection]:
        """
        Format : [1, 4 + num_classes, num_anchors]
        coords = cx, cy, w, h  (espace letterbox)
        """
        pred = output[0]               # (4+nc, n_anchors)
        if pred.shape[0] > pred.shape[1]:
            pred = pred.T              # → (n_anchors, 4+nc)

        n_anchors = pred.shape[0]
        if n_anchors == 0:
            return []

        boxes_cxcywh = pred[:, :4]    # (N, 4)
        scores_all   = pred[:, 4:]    # (N, nc)

        class_ids  = np.argmax(scores_all, axis=1)     # (N,)
        class_conf = scores_all[np.arange(n_anchors), class_ids]  # (N,)

        # Filtrage initial
        mask = class_conf >= self.conf_threshold
        if not np.any(mask):
            return []

        boxes_cxcywh = boxes_cxcywh[mask]
        class_ids    = class_ids[mask]
        class_conf   = class_conf[mask]

        # Conversion cx,cy,w,h → x1,y1,x2,y2
        boxes_xyxy = self._cxcywh_to_xyxy(boxes_cxcywh)

        # Remise à l'échelle (annuler letterbox)
        boxes_xyxy = self._unpad_boxes(boxes_xyxy, pad_info, orig_w, orig_h)

        return self._build_detections_nms(
            boxes_xyxy, class_ids, class_conf, orig_w, orig_h)

    # ── Décodeur YOLOv5 / v7 ──────────────────────────────────────────────────

    def _decode_yolov5(
        self, output: np.ndarray,
        orig_w: int, orig_h: int, pad_info: Dict,
    ) -> List[Detection]:
        """
        Format : [1, num_anchors, 5 + num_classes]
        colonnes : cx, cy, w, h, obj_conf, class_scores…
        """
        pred = output[0]               # (n_anchors, 5+nc)

        obj_conf   = pred[:, 4]
        scores_all = pred[:, 5:] * obj_conf[:, np.newaxis]

        class_ids  = np.argmax(scores_all, axis=1)
        class_conf = scores_all[np.arange(len(pred)), class_ids]

        mask = class_conf >= self.conf_threshold
        if not np.any(mask):
            return []

        boxes_cxcywh = pred[mask, :4]
        class_ids    = class_ids[mask]
        class_conf   = class_conf[mask]

        boxes_xyxy = self._cxcywh_to_xyxy(boxes_cxcywh)
        boxes_xyxy = self._unpad_boxes(boxes_xyxy, pad_info, orig_w, orig_h)

        return self._build_detections_nms(
            boxes_xyxy, class_ids, class_conf, orig_w, orig_h)

    # ── Helpers décodage ──────────────────────────────────────────────────────

    @staticmethod
    def _cxcywh_to_xyxy(boxes: np.ndarray) -> np.ndarray:
        """Convertit [cx, cy, w, h] → [x1, y1, x2, y2] vectorisé."""
        out = np.empty_like(boxes)
        out[:, 0] = boxes[:, 0] - boxes[:, 2] / 2  # x1
        out[:, 1] = boxes[:, 1] - boxes[:, 3] / 2  # y1
        out[:, 2] = boxes[:, 0] + boxes[:, 2] / 2  # x2
        out[:, 3] = boxes[:, 1] + boxes[:, 3] / 2  # y2
        return out

    @staticmethod
    def _unpad_boxes(
        boxes: np.ndarray, pad_info: Dict,
        orig_w: int, orig_h: int,
    ) -> np.ndarray:
        """Annule le letterbox et remet les coordonnées à l'échelle originale."""
        scale    = pad_info["scale"]
        pad_top  = pad_info["pad_top"]
        pad_left = pad_info["pad_left"]

        boxes[:, 0] = (boxes[:, 0] - pad_left) / scale
        boxes[:, 1] = (boxes[:, 1] - pad_top)  / scale
        boxes[:, 2] = (boxes[:, 2] - pad_left) / scale
        boxes[:, 3] = (boxes[:, 3] - pad_top)  / scale

        # Clamp
        boxes[:, 0] = np.clip(boxes[:, 0], 0, orig_w)
        boxes[:, 1] = np.clip(boxes[:, 1], 0, orig_h)
        boxes[:, 2] = np.clip(boxes[:, 2], 0, orig_w)
        boxes[:, 3] = np.clip(boxes[:, 3], 0, orig_h)
        return boxes

    def _build_detections_nms(
        self,
        boxes:      np.ndarray,   # (N, 4) float
        class_ids:  np.ndarray,   # (N,)   int
        confidences: np.ndarray,  # (N,)   float
        orig_w:     int,
        orig_h:     int,
    ) -> List[Detection]:
        """
        Applique la NMS vectorisée par classe et construit les objets Detection.
        Applique aussi les seuils par classe individuels.
        """
        # Filtrage seuil par classe
        per_class_mask = np.ones(len(boxes), dtype=bool)
        for idx in range(len(boxes)):
            cname = (self.class_names[class_ids[idx]]
                     if class_ids[idx] < len(self.class_names)
                     else f"class_{class_ids[idx]}")
            thr = self._class_thresholds.get(cname, self.conf_threshold)
            if confidences[idx] < thr:
                per_class_mask[idx] = False

        boxes       = boxes[per_class_mask]
        class_ids   = class_ids[per_class_mask]
        confidences = confidences[per_class_mask]

        if len(boxes) == 0:
            return []

        # NMS vectorisée (OpenCV pour performance, fallback NumPy)
        kept_indices = self._nms_vectorized(boxes, confidences, class_ids)

        detections: List[Detection] = []
        for i in kept_indices:
            x1, y1, x2, y2 = boxes[i]
            ix1, iy1 = int(x1), int(y1)
            ix2, iy2 = int(x2), int(y2)

            # Taille minimale
            if (ix2 - ix1) < self.MIN_BOX_PIXEL or (iy2 - iy1) < self.MIN_BOX_PIXEL:
                continue

            cid   = int(class_ids[i])
            cname = (self.class_names[cid]
                     if cid < len(self.class_names) else f"class_{cid}")
            conf  = float(confidences[i])

            det = Detection(
                bbox=[ix1, iy1, ix2, iy2],
                confidence=conf,
                class_id=cid,
                class_name=cname,
                bbox_norm=[
                    round(ix1 / orig_w, 4), round(iy1 / orig_h, 4),
                    round(ix2 / orig_w, 4), round(iy2 / orig_h, 4),
                ],
            )
            detections.append(det)

        return detections

    def _nms_vectorized(
        self,
        boxes:       np.ndarray,   # (N, 4)  x1 y1 x2 y2
        scores:      np.ndarray,   # (N,)
        class_ids:   np.ndarray,   # (N,)
    ) -> List[int]:
        """
        NMS par classe, 100 % NumPy (rapide, sans boucle sur les boîtes).
        Retourne les indices à conserver.
        """
        kept: List[int] = []
        unique_classes = np.unique(class_ids)

        for cls in unique_classes:
            cls_mask = class_ids == cls
            cls_idx  = np.where(cls_mask)[0]

            cls_boxes  = boxes[cls_idx]
            cls_scores = scores[cls_idx]

            order = np.argsort(cls_scores)[::-1]
            cls_boxes  = cls_boxes[order]
            cls_scores = cls_scores[order]
            cls_idx    = cls_idx[order]

            suppressed = np.zeros(len(cls_idx), dtype=bool)
            for i in range(len(cls_idx)):
                if suppressed[i]:
                    continue
                kept.append(int(cls_idx[i]))
                if i == len(cls_idx) - 1:
                    break
                iou = self._iou_vectorized(cls_boxes[i], cls_boxes[i+1:])
                suppressed[i+1:] |= iou >= self.iou_threshold

        return kept

    @staticmethod
    def _iou_vectorized(box: np.ndarray, others: np.ndarray) -> np.ndarray:
        """
        IoU entre `box` (4,) et `others` (N, 4).
        Retourne un vecteur (N,) d'IoU.
        """
        xi1 = np.maximum(box[0], others[:, 0])
        yi1 = np.maximum(box[1], others[:, 1])
        xi2 = np.minimum(box[2], others[:, 2])
        yi2 = np.minimum(box[3], others[:, 3])

        inter = np.maximum(0.0, xi2 - xi1) * np.maximum(0.0, yi2 - yi1)

        area_box    = (box[2] - box[0]) * (box[3] - box[1])
        area_others = (others[:, 2] - others[:, 0]) * (others[:, 3] - others[:, 1])
        union = area_box + area_others - inter

        return np.where(union > 0, inter / union, 0.0)

    # ═════════════════════════════════════════════════════════════════════════
    # FILTRES POST-NMS
    # ═════════════════════════════════════════════════════════════════════════

    def _filter_exclusion_zones(
        self,
        detections: List[Detection],
        orig_w:     int,
        orig_h:     int,
    ) -> List[Detection]:
        """Retire les détections dont le centre tombe dans une zone exclue."""
        filtered = []
        for det in detections:
            cx_norm = det.center[0] / orig_w
            cy_norm = det.center[1] / orig_h
            excluded = any(
                z.contains_center(cx_norm, cy_norm)
                for z in self._exclusion_zones
            )
            if not excluded:
                filtered.append(det)
        return filtered

    # ═════════════════════════════════════════════════════════════════════════
    # RENDU VISUEL
    # ═════════════════════════════════════════════════════════════════════════

    def _draw_boxes(
        self,
        frame:            np.ndarray,
        detections:       List[Detection],
        use_class_colors: bool  = True,
        show_conf:        bool  = True,
        show_label:       bool  = True,
        thickness:        int   = 2,
        font_scale:       float = 0.52,
    ) -> np.ndarray:
        """Dessine les boîtes avec label, fond semi-transparent et coins arrondis."""
        overlay = frame.copy()

        for det in detections:
            x1, y1, x2, y2 = det.bbox
            color = (_class_color(det.class_id)
                     if use_class_colors else _conf_color(det.confidence))

            # Rectangle principal
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, thickness)

            # Coins décoratifs (effet "tracking box")
            corner_len = max(8, min(20, (x2 - x1) // 6))
            cth = thickness + 1
            # top-left
            cv2.line(overlay, (x1, y1), (x1 + corner_len, y1), color, cth)
            cv2.line(overlay, (x1, y1), (x1, y1 + corner_len), color, cth)
            # top-right
            cv2.line(overlay, (x2, y1), (x2 - corner_len, y1), color, cth)
            cv2.line(overlay, (x2, y1), (x2, y1 + corner_len), color, cth)
            # bottom-left
            cv2.line(overlay, (x1, y2), (x1 + corner_len, y2), color, cth)
            cv2.line(overlay, (x1, y2), (x1, y2 - corner_len), color, cth)
            # bottom-right
            cv2.line(overlay, (x2, y2), (x2 - corner_len, y2), color, cth)
            cv2.line(overlay, (x2, y2), (x2, y2 - corner_len), color, cth)

            if not show_label:
                continue

            # Construction du label
            label_parts = [det.class_name]
            if show_conf:
                label_parts.append(f"{det.confidence:.0%}")
            label = "  ".join(label_parts)

            (lw, lh), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_DUPLEX, font_scale, 1)

            # Position du label (au-dessus si place, sinon en dessous)
            ly = y1 - 6 if y1 - lh - 12 >= 0 else y2 + lh + 8

            # Fond semi-transparent
            pad = 4
            cv2.rectangle(overlay,
                          (x1 - 1, ly - lh - pad),
                          (x1 + lw + pad * 2, ly + pad),
                          color, -1)

            # Transparence du fond
            frame = cv2.addWeighted(overlay, 0.75, frame, 0.25, 0)
            overlay = frame.copy()

            # Texte blanc
            cv2.putText(frame, label,
                        (x1 + pad, ly),
                        cv2.FONT_HERSHEY_DUPLEX, font_scale,
                        (255, 255, 255), 1, cv2.LINE_AA)
            overlay = frame.copy()

        return frame

    def _draw_metrics_overlay(self, frame: np.ndarray) -> np.ndarray:
        """Overlay FPS + latence en coin supérieur gauche."""
        h, w = frame.shape[:2]
        m = self.metrics

        lines = [
            f"FPS : {m.fps:.1f}",
            f"Latence : {m.avg_inference_ms:.1f} ms",
            f"Dets/frame : {m.avg_detections_per_frame:.1f}",
            f"Total : {m.total_frames} frames",
        ]

        box_w, box_h = 180, len(lines) * 20 + 12
        overlay = frame.copy()
        cv2.rectangle(overlay, (8, 8), (8 + box_w, 8 + box_h),
                      (20, 20, 20), -1)
        frame = cv2.addWeighted(overlay, 0.65, frame, 0.35, 0)

        for i, line in enumerate(lines):
            cv2.putText(frame, line, (14, 26 + i * 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.46,
                        (0, 230, 160), 1, cv2.LINE_AA)
        return frame

    # ═════════════════════════════════════════════════════════════════════════
    # UTILITAIRES
    # ═════════════════════════════════════════════════════════════════════════

    def crop_detection(
        self,
        frame:  np.ndarray,
        det:    Detection,
        margin: int = 10,
    ) -> Optional[np.ndarray]:
        """
        Extrait la région d'une détection avec marge.
        Accepte un objet Detection ou un dict avec clé 'bbox'.
        Retourne None si la région est invalide.
        """
        if isinstance(det, dict):
            bbox = det["bbox"]
        else:
            bbox = det.bbox

        x1, y1, x2, y2 = bbox
        h, w = frame.shape[:2]

        x1 = max(0, x1 - margin)
        y1 = max(0, y1 - margin)
        x2 = min(w, x2 + margin)
        y2 = min(h, y2 + margin)

        if x2 <= x1 or y2 <= y1:
            return None

        return frame[y1:y2, x1:x2].copy()

    def crop_all(
        self,
        frame:      np.ndarray,
        detections: List[Detection],
        margin:     int = 10,
    ) -> List[Tuple[Detection, np.ndarray]]:
        """
        Retourne [(Detection, crop)] pour toutes les détections valides.
        Pratique pour la classification différée (InferenceWorker).
        """
        result = []
        for det in detections:
            crop = self.crop_detection(frame, det, margin)
            if crop is not None:
                result.append((det, crop))
        return result

    def release(self) -> None:
        """Libère les ressources ONNX."""
        self.session = None
        self._is_loaded = False
        logger.info("FishDetector libéré.")

    def __repr__(self) -> str:
        status = (f"loaded on {self._provider}"
                  if self._is_loaded else "not loaded")
        return (f"FishDetector(model={self.model_path.name!r}, "
                f"conf={self.conf_threshold}, iou={self.iou_threshold}, "
                f"classes={len(self.class_names)}, {status})")