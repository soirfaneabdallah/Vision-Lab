# fishid/controllers/app_controller.py
from PySide6.QtCore import QSettings

DEFAULT_SETTINGS = {
    "mode": "fish",
    "frame_interval": 10,
    "conf_threshold": 0.4,
    "anomaly_threshold": 0.9,
    "save_predictions": False,
    "save_mode": "best",
    "output_dir": "",
    "report_author": "Vision Lab",
    "use_gpu": False,
    "theme": "dark",
    "buffer_enabled": True,
    "buffer_frames": 60,
}

def load_settings():
    settings = QSettings("VisionLab", "Settings")
    values = {}
    for key, default in DEFAULT_SETTINGS.items():
        v = settings.value(key, default)
        if isinstance(default, bool):
            v = v == "true" or v is True
        elif isinstance(default, int):
            v = int(v)
        elif isinstance(default, float):
            v = float(v)
        values[key] = v
    return values

def save_settings(settings_dict):
    settings = QSettings("VisionLab", "Settings")
    for key, value in settings_dict.items():
        settings.setValue(key, value)