# fishid/core/image_stitcher.py
import cv2
import numpy as np
import os
from PySide6.QtCore import QThread, Signal


class StitcherWorker(QThread):
    progress = Signal(int)
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, image_paths, max_dim=1200):
        super().__init__()
        self.image_paths = image_paths
        self.max_dim = max_dim
        self._is_running = True

    def stop(self):
        self._is_running = False

    def _preprocess_image(self, img):
        """Redimensionne et améliore le contraste pour de meilleures correspondances."""
        h, w = img.shape[:2]
        if max(w, h) > self.max_dim:
            scale = self.max_dim / max(w, h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            img = cv2.resize(img, (new_w, new_h))
        # Améliorer le contraste
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        img = cv2.merge((l, a, b))
        img = cv2.cvtColor(img, cv2.COLOR_LAB2BGR)
        return img

    def run(self):
        try:
            images = []
            total = len(self.image_paths)
            
            for i, path in enumerate(self.image_paths):
                if not self._is_running:
                    return
                
                if not os.path.exists(path):
                    self.error.emit(f"Fichier introuvable : {path}")
                    return
                
                img = cv2.imread(path)
                if img is None:
                    self.error.emit(f"Impossible de lire l'image : {path}")
                    return
                
                img = self._preprocess_image(img)
                images.append(img)
                self.progress.emit(int((i + 1) / total * 50))
            
            if len(images) < 2:
                self.error.emit("Au moins 2 images sont nécessaires")
                return
            
            # Essayer d'abord avec SCANS, puis PANORAMA
            stitcher = cv2.Stitcher.create(cv2.Stitcher_SCANS)
            status, panorama = stitcher.stitch(images)
            
            if status != cv2.Stitcher_OK:
                # Essayer avec PANORAMA
                stitcher = cv2.Stitcher.create(cv2.Stitcher_PANORAMA)
                status, panorama = stitcher.stitch(images)
            
            if status == cv2.Stitcher_ERR_NEED_MORE_IMGS:
                self.error.emit("Chevauchement insuffisant entre les images (besoin de plus de 30%)")
                return
            elif status == cv2.Stitcher_ERR_HOMOGRAPHY_EST_FAIL:
                self.error.emit("Échec de l'alignement. Les images sont trop différentes ou déformées")
                return
            elif status == cv2.Stitcher_ERR_CAMERA_PARAMS_ADJUST_FAIL:
                self.error.emit("Échec de l'ajustement des paramètres caméra")
                return
            elif status != cv2.Stitcher_OK:
                self.error.emit(f"Échec du stitching (code {status})")
                return
            
            self.progress.emit(100)
            self.finished.emit(panorama)
            
        except Exception as e:
            self.error.emit(f"Erreur : {str(e)}")