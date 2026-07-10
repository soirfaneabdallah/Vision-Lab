# fishid/controllers/camera_handler.py
import sys
import io
import cv2
import requests
import re
import os
from PySide6.QtWidgets import QMessageBox, QInputDialog, QDialog, QVBoxLayout, QListWidget, QDialogButtonBox, QListWidgetItem
from PySide6.QtCore import QThread, Qt
from PySide6.QtGui import QImage, QPixmap
from fishid.core.remote_camera import RemoteCameraServer
from fishid.ui.camera_dialog import CameraDialog


class CameraHandler:
    def __init__(self, video_reader, app_status, processing_callback, stop_callback):
        self.video_reader = video_reader
        self.app_status = app_status
        self.processing_callback = processing_callback
        self.stop_callback = stop_callback
        self.remote_server = RemoteCameraServer()
        self.remote_server_active = False

    def _get_available_cameras(self, max_index=5):
        """Détecte les caméras disponibles (index 0 à max_index-1)."""
        available = []
        for i in range(max_index):
            old_stderr = sys.stderr
            sys.stderr = open(os.devnull, 'w')
            cap = cv2.VideoCapture(i)
            sys.stderr = old_stderr
            if cap.isOpened():
                # Test de lecture d'un frame pour valider
                ret, frame = cap.read()
                name = f"Caméra {i}" + (" (active)" if ret else "")
                available.append((i, name))
                cap.release()
        return available

    def start_webcam(self, parent_widget):
        self.stop_callback()
        self.stop_remote_camera()
        cameras = self._get_available_cameras()
        if not cameras:
            QMessageBox.warning(parent_widget, "Aucune caméra", "Aucune webcam détectée.")
            return
        if len(cameras) == 1:
            idx, _ = cameras[0]
        else:
            dlg = QDialog(parent_widget)
            dlg.setWindowTitle("Choisir une webcam")
            layout = QVBoxLayout(dlg)
            list_widget = QListWidget()
            for idx, name in cameras:
                list_widget.addItem(QListWidgetItem(f"{name} (index {idx})"))
            layout.addWidget(list_widget)
            btnbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            btnbox.accepted.connect(dlg.accept)
            btnbox.rejected.connect(dlg.reject)
            layout.addWidget(btnbox)
            if dlg.exec() != QDialog.Accepted:
                return
            selected = list_widget.currentRow()
            if selected < 0:
                return
            idx, _ = cameras[selected]
        success = self.video_reader.open_webcam(idx)
        if success:
            self.app_status(f"📷 Webcam {idx} activée")
            self.processing_callback()
        else:
            self.app_status("🔴 Impossible d'ouvrir la webcam")

    def start_browser_camera(self, parent_widget):
        if self.remote_server_active:
            self.stop_remote_camera()
            return
        self.stop_callback()
        self.stop_remote_camera()
        try:
            self.remote_server.start()
        except Exception as e:
            QMessageBox.critical(parent_widget, "Erreur", f"Impossible de démarrer le serveur local : {e}")
            return
        self.remote_server_active = True
        for _ in range(30):
            if self.remote_server.is_running:
                break
            QThread.msleep(100)
        else:
            QMessageBox.critical(parent_widget, "Erreur", "Le serveur caméra n'a pas démarré (port occupé ?)")
            self.remote_server_active = False
            self.remote_server.stop()
            return
        # Configuration du lecteur vidéo pour la source distante
        self.video_reader.set_remote_source(self.remote_server)
        self.video_reader.video_path = "Smartphone"
        self.video_reader.total_frames = 1000000
        self.video_reader.fps = 30.0
        self.video_reader.is_playing = False

        internet_available = self._check_internet()
        public_url = ""
        qr_pixmap = None
        if internet_available:
            try:
                from pyngrok import ngrok, conf
                conf.get_default().log_level = "CRITICAL"
                ngrok.kill()
                tunnel = ngrok.connect(5001, "http")
                public_url = tunnel.public_url.replace("http://", "https://")
                import qrcode
                qr = qrcode.make(public_url)
                buf = io.BytesIO()
                qr.save(buf, format='PNG')
                buf.seek(0)
                qr_image = QImage()
                qr_image.loadFromData(buf.read(), 'PNG')
                qr_pixmap = QPixmap.fromImage(qr_image).scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            except:
                internet_available = False
                public_url = ""
                qr_pixmap = None
        local_ip = self.remote_server._get_local_ip()
        local_url = f"http://{local_ip}:5001"
        if internet_available and public_url:
            info_text = ("Scannez le QR code avec votre téléphone pour vous connecter via Internet.\n"
                         "Aucun réseau local requis.")
            prefill_url = public_url
        else:
            info_text = ("⚠️ Aucune connexion Internet détectée.\n"
                         "Le QR code n'est pas disponible.\n\n"
                         "Votre téléphone doit être sur le même réseau Wi‑Fi que cet ordinateur.\n"
                         "Ouvrez l'URL ci‑dessous dans le navigateur du téléphone :")
            prefill_url = local_url
        dialog = CameraDialog(parent_widget, prefill_url, qr_pixmap, info_text)
        if dialog.exec() != QDialog.Accepted:
            self.stop_remote_camera()
            return
        url = dialog.get_url().strip()
        if not url:
            QMessageBox.warning(parent_widget, "Erreur", "Aucune URL saisie.")
            self.stop_remote_camera()
            return
        if url != prefill_url:
            if not self._is_valid_url(url):
                QMessageBox.critical(parent_widget, "URL invalide",
                                     "L'URL doit être de la forme http://adresse:port (ex. http://192.168.1.45:8080/video).")
                self.stop_remote_camera()
                return
            self.stop_remote_camera()
            cv2.setLogLevel(0)
            test_cap = cv2.VideoCapture(url)
            if test_cap.isOpened():
                test_cap.release()
                success = self.video_reader.open_ip_camera(url)
                if success:
                    self.app_status(f"📷 Connecté à : {url}")
                    self.processing_callback()
                else:
                    self.app_status("🔴 Échec de connexion à l'URL")
                    QMessageBox.critical(parent_widget, "Erreur de connexion",
                                         "Impossible d'ouvrir le flux vidéo.\n"
                                         "Vérifiez l'URL et que les appareils sont sur le même réseau.")
            else:
                test_cap.release()
                QMessageBox.critical(parent_widget, "Erreur de connexion",
                                     "Impossible d'ouvrir le flux vidéo.\n"
                                     "Vérifiez l'URL et que les appareils sont sur le même réseau.")
        else:
            self.app_status("📱 En attente du flux smartphone...")
            self.processing_callback()

    def stop_remote_camera(self):
        if self.remote_server_active:
            try:
                from pyngrok import ngrok
                ngrok.kill()
            except:
                pass
            self.remote_server.stop()
            self.remote_server_active = False
            self.video_reader.set_remote_source(None)
            QThread.msleep(800)
            self.app_status("📱 Caméra smartphone arrêtée")

    def _check_internet(self):
        try:
            requests.get("https://www.google.com", timeout=3)
            return True
        except:
            return False

    def _is_valid_url(self, url):
        pattern = r'^https?://[^/]+:\d+'
        return re.match(pattern, url) is not None