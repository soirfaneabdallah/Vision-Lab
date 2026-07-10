# core/session_history.py
import os
import json
import datetime
import shutil

HISTORY_DIR = "history"
HISTORY_FILE = "session_history.json"

class SessionHistory:
    """Gère l'historique des sessions d'analyse."""

    def __init__(self, base_path="."):
        self.base_path = base_path
        self.history_path = os.path.join(base_path, HISTORY_DIR, HISTORY_FILE)
        os.makedirs(os.path.dirname(self.history_path), exist_ok=True)

    def load(self) -> list:
        if not os.path.exists(self.history_path):
            return []
        with open(self.history_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save(self, entry: dict):
        history = self.load()
        history.append(entry)
        with open(self.history_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

    def add_session(self, video_name, stats, best_images: dict):
        """Enregistre une session avec les données de l'analyse.
        best_images : dictionnaire {class_name: chemin_image}
        """
        session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        images_dir = os.path.join(self.base_path, HISTORY_DIR, "images", session_id)
        os.makedirs(images_dir, exist_ok=True)

        # Copier les meilleures images dans l'historique
        for class_name, img_path in best_images.items():
            if os.path.exists(img_path):
                ext = os.path.splitext(img_path)[1]
                dest = os.path.join(images_dir, f"{class_name}{ext}")
                shutil.copy2(img_path, dest)

        entry = {
            'session_id': session_id,
            'date': datetime.datetime.now().isoformat(),
            'video_name': video_name,
            'mode': getattr(self, 'mode', 'fish'),
            'stats': {
                'total_detections': stats.get('total', 0),
                'species_count': stats.get('species', 0),
                'anomalies': stats.get('anomalies', 0),
                'duration': stats.get('duration', ''),
                'shannon': stats.get('shannon', 0.0),
                'simpson': stats.get('simpson', 0.0),
                'pielou': stats.get('pielou', 0.0),
                'species_list': stats.get('species_list', [])
            },
            'images_dir': images_dir
        }
        self.save(entry)
        return entry