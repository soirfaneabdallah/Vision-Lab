# fishid/core/duplicate_checker.py
import imagehash
from PIL import Image
import numpy as np
import cv2
import os
import json
from datetime import datetime
from PySide6.QtCore import QObject, Signal


class DuplicateChecker(QObject):
    """
    Vérifie les doublons d'images avec hash perceptuel (pHash).
    Organise la sauvegarde par classe.
    Supporte deux modes :
    - "best" : ne garde que la meilleure image par individu (anti‑doublon)
    - "all"  : enregistre toutes les occurrences sans vérification
    """

    status_message = Signal(str)
    image_saved = Signal(str, str)  # class_name, filename

    def __init__(self, output_dir: str = "output", hash_threshold: int = 8):
        super().__init__()
        self.output_dir = output_dir
        self.hash_threshold = hash_threshold
        self.seen_hashes = {}
        self.session_prefix = ""
        self.stats = {
            'total_detections': 0,
            'saved_images': 0,
            'duplicates_skipped': 0,
            'by_class': {}
        }
        self.save_all_occurrences = False
        os.makedirs(self.output_dir, exist_ok=True)

    def set_save_mode(self, mode: str):
        self.save_all_occurrences = (mode == "all")

    def set_output_dir(self, path: str):
        self.output_dir = path
        os.makedirs(self.output_dir, exist_ok=True)

    def set_session_prefix(self, prefix: str):
        self.session_prefix = prefix

    def is_duplicate(self, image: np.ndarray, class_name: str) -> bool:
        if image is None or image.size == 0:
            return True
        img_hash = self._compute_hash(image)
        if img_hash is None:
            return True
        if class_name not in self.seen_hashes:
            self.seen_hashes[class_name] = set()
        for existing_hash in self.seen_hashes[class_name]:
            distance = img_hash - existing_hash
            if distance <= self.hash_threshold:
                return True
        self.seen_hashes[class_name].add(img_hash)
        return False

    def save_image(self, image: np.ndarray, class_name: str,
                   video_name: str = "", frame_idx: int = 0,
                   confidence: float = 0.0) -> str:
        self.stats['total_detections'] += 1

        # Préfixe du fichier (session ou vidéo)
        video_prefix = self.session_prefix if self.session_prefix else self.sanitize_filename(video_name).replace('.mp4', '').replace('.avi', '')[:20]

        # Dossier de la classe
        class_dir = os.path.join(self.output_dir, self.sanitize_filename(class_name))
        os.makedirs(class_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{video_prefix}_f{frame_idx:06d}_{timestamp}.jpg"
        filepath = os.path.join(class_dir, filename)

        if self.save_all_occurrences:
            # Mode "toutes les occurrences" – pas d'anti‑doublon
            cv2.imwrite(filepath, image, [cv2.IMWRITE_JPEG_QUALITY, 95])
            self.stats['saved_images'] += 1
            if class_name not in self.stats['by_class']:
                self.stats['by_class'][class_name] = 0
            self.stats['by_class'][class_name] += 1
            self.image_saved.emit(class_name, filename)
            return filepath
        else:
            # Mode "meilleure image" – anti‑doublon
            if self.is_duplicate(image, class_name):
                self.stats['duplicates_skipped'] += 1
                return None
            cv2.imwrite(filepath, image, [cv2.IMWRITE_JPEG_QUALITY, 95])
            self.stats['saved_images'] += 1
            if class_name not in self.stats['by_class']:
                self.stats['by_class'][class_name] = 0
            self.stats['by_class'][class_name] += 1
            self.image_saved.emit(class_name, filename)
            return filepath

    def save_detection_info(self, detections: list, video_name: str,
                            frame_idx: int, csv_path: str = None):
        if csv_path is None:
            csv_path = os.path.join(self.output_dir, "detections_log.csv")
        file_exists = os.path.exists(csv_path)
        with open(csv_path, 'a', encoding='utf-8') as f:
            if not file_exists:
                f.write("video_name,frame,class_name,confidence,x1,y1,x2,y2,timestamp\n")
            timestamp = datetime.now().isoformat()
            for det in detections:
                bbox = det.get('bbox', [0, 0, 0, 0])
                line = (f"{video_name},{frame_idx},"
                        f"{det.get('class_name', 'inconnu')},"
                        f"{det.get('confidence', 0):.4f},"
                        f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]},"
                        f"{timestamp}\n")
                f.write(line)

    def save_session_info(self, video_name: str):
        session_file = os.path.join(self.output_dir, "session_info.json")
        session_data = {
            'video_name': video_name,
            'date': datetime.now().isoformat(),
            'output_directory': self.output_dir,
            'statistics': self.stats,
            'hash_threshold': self.hash_threshold
        }
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)

    def get_stats(self) -> dict:
        return self.stats.copy()

    def reset(self):
        self.seen_hashes.clear()
        self.stats = {
            'total_detections': 0,
            'saved_images': 0,
            'duplicates_skipped': 0,
            'by_class': {}
        }

    def _compute_hash(self, image: np.ndarray):
        try:
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb)
            return imagehash.phash(pil_image)
        except Exception:
            return None

    @staticmethod
    def sanitize_filename(name: str) -> str:
        import re
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        return name[:100].strip()