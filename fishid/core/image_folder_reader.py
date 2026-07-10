# fishid/core/image_folder_reader.py
import os
import glob
import cv2
from PySide6.QtCore import QObject, QThread, Signal


class ImageFolderReader(QObject):
    frame_ready = Signal(object, int)  # frame, index
    finished = Signal()
    error_occurred = Signal(str)

    def __init__(self):
        super().__init__()
        self.image_files = []
        self.total_frames = 0
        self.fps = 1   # pour l'affichage, on peut défiler à la vitesse souhaitée
        self.is_playing = False
        self.thread = None
        self.current_idx = 0
        self.folder_path = ""

    def open_folder(self, folder_path: str) -> bool:
        self.folder_path = folder_path
        self.image_files = []
        for ext in ('*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tif', '*.tiff'):
            self.image_files.extend(glob.glob(os.path.join(folder_path, ext)))
        self.image_files.sort()
        if not self.image_files:
            self.error_occurred.emit(f"Aucune image trouvée dans {folder_path}")
            return False
        self.total_frames = len(self.image_files)
        return True

    def play(self):
        if not self.image_files or self.is_playing:
            return
        self.is_playing = True
        self.current_idx = 0
        self.thread = QThread()
        self.moveToThread(self.thread)
        self.thread.started.connect(self._run)
        self.thread.start()

    def stop(self):
        self.is_playing = False
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        self.thread = None

    def seek(self, index: int):
        if 0 <= index < self.total_frames:
            self.current_idx = index
            # On peut éventuellement émettre la frame immédiatement, mais cela dépend de l'utilisation

    def _run(self):
        while self.is_playing and self.current_idx < self.total_frames:
            img_path = self.image_files[self.current_idx]
            frame = cv2.imread(img_path)
            if frame is not None:
                self.frame_ready.emit(frame, self.current_idx)
            else:
                self.error_occurred.emit(f"Impossible de lire {img_path}")
            self.current_idx += 1
            # Attendre pour simuler un framerate (optionnel)
            QThread.msleep(int(1000 / self.fps))
        self.finished.emit()
        self.is_playing = False