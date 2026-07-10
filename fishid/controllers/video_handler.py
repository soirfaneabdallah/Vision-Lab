import os
import datetime
import cv2
import ffmpeg
import ctypes
import platform

from PySide6.QtCore import QObject, Signal, QTimer

from fishid.helpers import get_color_for_class
from fishid.core.video_reader import VideoReader
from fishid.core.qt_video_reader import QtVideoReader
from fishid.core.tracker_wrapper import BoTSORTWrapper
from fishid.core.inference_worker import InferenceWorker
from fishid.core.detection import Detection

def windows_short_path(path):
    if platform.system().lower() != "windows":
        return path
    buf = ctypes.create_unicode_buffer(260)
    r = ctypes.windll.kernel32.GetShortPathNameW(path, buf, 260)
    return buf.value if r else path


class VideoHandler(QObject):
    frame_ready = Signal(object)
    progress_updated = Signal(int, int, float)
    video_opened = Signal(str, int, float)
    playback_finished = Signal()
    error_occurred = Signal(str)
    detection_added = Signal(str, float, str)
    image_saved = Signal(str, str)
    processing_started = Signal()
    processing_stopped = Signal()
    buffering_started = Signal()
    buffering_finished = Signal()
    detections_updated = Signal(object)

    def __init__(self, model_manager, duplicate_checker, session_history, spinner=None, video_viewer=None):
        super().__init__()
        self.model_manager = model_manager
        self.duplicate_checker = duplicate_checker
        self.session_history = session_history
        self.spinner = spinner
        self.video_viewer = video_viewer

        self.video_reader_file = QtVideoReader()
        self.video_reader_cam = VideoReader()
        self.current_reader = None
        self.current_source_name = ""

        self.tracker = None
        self.track_labels = {}
        self.inference_worker = None
        self.current_mode = "fish"
        self.frame_interval = 10
        self.conf_threshold = 0.4
        self.anomaly_threshold = 0.2
        self.save_predictions = False
        self.direct_classifier = None
        self.use_gpu = False
        self.session_prefix = ""
        self.last_annotated_frame = None
        self.tracking_enabled = True
        self.annotations_enabled = True
        self.is_playing = False
        self.position_slider_max = 0
        self.fps = 0

        self.buffer_enabled = True
        self.buffer_target_size = 60
        self.frame_buffer = []
        self.buffering = True
        self.display_timer = None
        self.sound_paused = False
        self.current_frame_idx = 0

        self._fallback_attempted = False
        self._load_timeout = None
        self._opencv_cap = None
        self._loading_from_fallback = False

        self.detections_history = []

        self.buffering_started.connect(self._on_buffering_started)
        self.buffering_finished.connect(self._on_buffering_finished)
        self.direct_classifier = self.model_manager.get_waste_direct_classifier()

    def set_buffer_settings(self, enabled, frames):
        self.buffer_enabled = enabled
        self.buffer_target_size = frames if enabled else 0
        if not enabled:
            self.buffering = False

    def _on_buffering_started(self):
        if self.spinner:
            self.spinner.set_text("Pré-traitement vidéo...")
            self.spinner.start()

    def _on_buffering_finished(self):
        self.buffering = False
        if self.spinner:
            self.spinner.stop()
        self._stop_display_timer()
        self._start_display_timer()
        if self.current_reader:
            self.current_reader.play()
        self.error_occurred.emit("✅ Buffer prêt, lecture avec annotations")

    def _disconnect_signals(self, reader):
        if reader is None:
            return
        try:
            reader.frame_ready.disconnect(self._on_new_frame)
            reader.progress_updated.disconnect(self._on_progress_updated)
            reader.video_opened.disconnect(self._on_video_opened)
            reader.error_occurred.disconnect(self.error_occurred.emit)
            reader.playback_finished.disconnect(self._on_playback_finished)
        except (TypeError, RuntimeError):
            pass

    def _connect_signals(self, reader):
        if reader is None:
            return
        reader.frame_ready.connect(self._on_new_frame)
        reader.progress_updated.connect(self._on_progress_updated)
        reader.video_opened.connect(self._on_video_opened)
        reader.error_occurred.connect(self.error_occurred.emit)
        reader.playback_finished.connect(self._on_playback_finished)

    def _release_all_readers(self):
        try:
            if self.video_reader_file:
                self.video_reader_file.close()
        except Exception:
            pass
        try:
            if self.video_reader_cam and hasattr(self.video_reader_cam, "cap") and self.video_reader_cam.cap is not None:
                self.video_reader_cam.cap.release()
                self.video_reader_cam.cap = None
        except Exception:
            pass
        try:
            if self._opencv_cap is not None:
                self._opencv_cap.release()
                self._opencv_cap = None
        except Exception:
            pass

    def _stop_display_timer(self):
        if self.display_timer and self.display_timer.isActive():
            self.display_timer.stop()
        self.display_timer = None

    def _start_display_timer(self):
        if self.display_timer is None:
            self.display_timer = QTimer()
            self.display_timer.timeout.connect(self._display_next_frame)
        if not self.display_timer.isActive():
            self.display_timer.start(int(1000 / 30))

    def _stop_completely(self):
        if self.current_reader:
            self._disconnect_signals(self.current_reader)
            try:
                self.current_reader.stop()
            except Exception:
                pass

        self.stop_processing()
        self._stop_display_timer()

        self.tracker = None
        self.track_labels.clear()
        self.is_playing = False
        self.frame_buffer.clear()
        self.buffering = True
        self.sound_paused = False
        self.detections_history = []

        self._release_all_readers()

    def load_video(self, path):
        self._stop_completely()
        self._fallback_attempted = False
        self._loading_from_fallback = False

        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            self.error_occurred.emit(f"❌ Fichier introuvable: {abs_path}")
            return False

        print("RAW PATH:", repr(path))
        print("ABS PATH:", repr(abs_path))

        cap = cv2.VideoCapture(abs_path)
        if not cap.isOpened():
            self.error_occurred.emit("❌ OpenCV ne peut pas ouvrir cette vidéo.")
            return False

        fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
        print("FOURCC:", codec, fourcc)
        print("FPS:", fps, "FRAMES:", total, "SIZE:", width, "x", height)

        cap.release()
        return self._try_fallback(abs_path)

    def load_webcam(self, index=0):
        self._stop_completely()
        self.current_reader = self.video_reader_cam
        self.current_source_name = f"webcam_{index}"
        self._connect_signals(self.current_reader)
        self.current_reader.video_path = self.current_source_name
        return self.current_reader.open_webcam(index)

    def load_ip_camera(self, url):
        self._stop_completely()
        self.current_reader = self.video_reader_cam
        self.current_source_name = url
        self._connect_signals(self.current_reader)
        self.current_reader.video_path = url
        return self.current_reader.open_ip_camera(url)

    def get_current_source_name(self):
        return self.current_source_name

    def get_video_widget(self):
        if hasattr(self.video_reader_file, "get_widget"):
            return self.video_reader_file.get_widget()
        return None

    def start_processing(self):
        if self.current_reader is None:
            self.error_occurred.emit("⚠️ Aucune source chargée.")
            return

        if isinstance(self.current_reader, QtVideoReader):
            if not getattr(self.current_reader, "video_path", None):
                self.error_occurred.emit("⚠️ Aucune vidéo chargée.")
                return
        else:
            if getattr(self.current_reader, "cap", None) is None and getattr(self.current_reader, "remote_server", None) is None:
                self.error_occurred.emit("⚠️ Aucune source chargée.")
                return

        self.stop_processing()
        try:
            self.current_reader.stop()
        except Exception:
            pass

        self.duplicate_checker.reset()
        self.track_labels.clear()
        self.frame_buffer.clear()
        self.sound_paused = False
        self.current_frame_idx = 0
        self.detections_history = []

        if self.buffer_enabled and self.buffer_target_size > 0:
            self.buffering = True
            self.buffering_started.emit()
        else:
            self.buffering = False

        classifier = self.model_manager.get_classifier(self.current_mode)
        if classifier.session is None:
            classifier.load_model(use_gpu=self.use_gpu)

        fps = getattr(self.current_reader, "fps", 30) or 30
        self.tracker = BoTSORTWrapper(
            lost_track_buffer=30,
            frame_rate=fps,
            track_activation_threshold=0.6,
            minimum_consecutive_frames=2,
            high_conf_det_threshold=0.5,
            enable_cmc=False,
            cmc_method="sparseOptFlow",
            cmc_downscale=2,
        )

        source_name = self.current_source_name or "source"
        clean_name = source_name.replace(".mp4", "").replace(".avi", "").replace(".mkv", "")[:20]
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_prefix = f"{clean_name}_{timestamp}_"
        self.duplicate_checker.set_session_prefix(self.session_prefix)

        self.current_reader.play()
        self.is_playing = True
        self.processing_started.emit()

    def stop_processing(self):
        if self.inference_worker and self.inference_worker.isRunning():
            self.inference_worker.quit()
            self.inference_worker.wait(2000)
            self.inference_worker = None

        self._stop_display_timer()

        if self.current_reader:
            try:
                self.current_reader.pause()
            except Exception:
                pass
            if self.sound_paused and hasattr(self.current_reader, "set_muted"):
                try:
                    self.current_reader.set_muted(False)
                except Exception:
                    pass

        self.tracker = None
        self.track_labels.clear()
        self.is_playing = False
        self.processing_stopped.emit()

    def toggle_play_pause(self):
        if self.tracker is None:
            self.start_processing()
            return

        if self.current_reader:
            if self.is_playing:
                self.current_reader.pause()
                self.is_playing = False
                self._stop_display_timer()
            else:
                self.current_reader.play()
                self.is_playing = True
                if not self.buffering and self.frame_buffer:
                    self._start_display_timer()

    def seek(self, frame_idx: int):
        if self.current_reader is None:
            return

        if self.display_timer and self.display_timer.isActive():
            self.display_timer.stop()

        self.frame_buffer.clear()
        self.current_frame_idx = frame_idx

        if isinstance(self.current_reader, QtVideoReader):
            if self.fps > 0:
                ms = int(frame_idx / self.fps * 1000)
                self.current_reader.seek(ms)
        else:
            self.current_reader.seek(frame_idx)

        self.progress_updated.emit(frame_idx, self.position_slider_max, self.fps)

        if not self.buffering:
            self._start_display_timer()

    def set_settings(self, mode, frame_interval, conf_threshold, anomaly_threshold,
                     save_predictions, save_mode, use_gpu):
        self.current_mode = mode
        self.frame_interval = frame_interval
        self.conf_threshold = conf_threshold
        self.anomaly_threshold = anomaly_threshold
        self.save_predictions = save_predictions
        self.use_gpu = use_gpu
        self.duplicate_checker.set_save_mode(save_mode)

    def _on_video_opened(self, name, total_frames, fps):
        self.fps = fps or 30
        self.position_slider_max = total_frames
        self.video_opened.emit(name, total_frames, self.fps)
        self.progress_updated.emit(0, total_frames, self.fps)

    def _on_progress_updated(self, current, total, fps):
        self.fps = fps or self.fps or 30
        self.position_slider_max = total
        self.progress_updated.emit(current, total, self.fps)

    def _on_new_frame(self, frame, frame_idx):
        self.current_frame_idx = frame_idx

        if self.buffering and self.buffer_enabled:
            self.frame_ready.emit(frame)
            self._process_frame(frame, frame_idx, store_in_buffer=True)
            if len(self.frame_buffer) >= self.buffer_target_size:
                self.buffering_finished.emit()
        else:
            self._process_frame(frame, frame_idx, store_in_buffer=False)
            if self.last_annotated_frame is not None:
                self.frame_ready.emit(self.last_annotated_frame)

    def _process_frame(self, frame, frame_idx, store_in_buffer=False):
        if self.tracker is None:
            if store_in_buffer:
                self.frame_buffer.append(frame)
            return

        detections = self.model_manager.object_detector.detect_objects(frame)
        tracks = self.tracker.update(detections, frame)

        annotated = frame.copy()
        if self.tracking_enabled:
            for trk in tracks:
                bbox = trk["bbox"]
                tid = trk["track_id"]
                label = self.track_labels.get(tid, "?")
                color = get_color_for_class(label)
                cv2.rectangle(annotated, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
                if self.annotations_enabled:
                    cv2.putText(annotated, f"ID:{tid} {label}", (bbox[0], bbox[1] - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        self.last_annotated_frame = annotated

        if store_in_buffer:
            self.frame_buffer.append(annotated)

        tracks_to_classify = []
        if frame_idx % self.frame_interval == 0:
            if self.inference_worker is None or not self.inference_worker.isRunning():
                tracks_to_classify = [
                    trk for trk in tracks
                    if self.track_labels.get(trk["track_id"], "?") in ("?", "Incertain")
                ]

        if tracks_to_classify:
            classifier = self.model_manager.get_classifier(self.current_mode)
            use_direct = (self.current_mode == "waste" and self.direct_classifier is not None)

            worker = InferenceWorker(
                frame,
                tracks_to_classify,
                self.model_manager.dinov2,
                self.model_manager.anomaly_detector,
                classifier,
                self.conf_threshold,
                self.anomaly_threshold,
                self.current_mode,
                video_name=self.current_source_name,
                frame_idx=frame_idx,
                use_direct_classifier=use_direct
            )
            if use_direct:
                worker.direct_classifier = self.direct_classifier
            worker.result_ready.connect(self._on_inference_result)
            worker.start()
            self.inference_worker = worker

    def _on_inference_result(self, track_id, class_name, confidence, cropped_image, frame_idx, bbox=None):
        self.track_labels[track_id] = class_name
        self.detection_added.emit(class_name, confidence, "")

        if bbox is None:
            bbox = [0, 0, 0, 0]

        detection = Detection(
            frame_idx=frame_idx,
            timestamp_ms=int(datetime.datetime.now().timestamp() * 1000),
            class_id=track_id,
            class_name=class_name,
            confidence=confidence,
            bbox=bbox
        )
        self.detections_history.append(detection)

        if self.save_predictions and cropped_image is not None and class_name not in ("Incertain",):
            self.duplicate_checker.save_image(
                image=cropped_image,
                class_name=class_name,
                video_name=self.current_source_name,
                frame_idx=frame_idx,
                confidence=confidence
            )
            self.image_saved.emit(class_name, "")

    def _on_playback_finished(self):
        if self.position_slider_max > 0:
            QTimer.singleShot(100, self._force_progress_to_end)

        if self.detections_history:
            frames_dict = {}
            for det in self.detections_history:
                frames_dict.setdefault(det.frame_idx, []).append(det)

            detections_by_frame = [frames_dict[idx] for idx in sorted(frames_dict.keys())]
            self.detections_updated.emit(detections_by_frame)
            self.error_occurred.emit(f"✅ {len(self.detections_history)} détections transmises")

        if self.frame_buffer:
            self.error_occurred.emit("🎵 Son terminé, fin du traitement en cours...")
        else:
            self.stop_processing()
            self.playback_finished.emit()

    def _force_progress_to_end(self):
        if self.position_slider_max > 0:
            self.progress_updated.emit(self.position_slider_max, self.position_slider_max, self.fps)

    def capture_current_frame(self):
        if self.last_annotated_frame is not None:
            capture_dir = os.path.join(self.duplicate_checker.output_dir, "captures")
            os.makedirs(capture_dir, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"capture_{timestamp}.png"
            path = os.path.join(capture_dir, filename)
            cv2.imwrite(path, self.last_annotated_frame)
            return filename
        return None

    def toggle_tracking(self):
        self.tracking_enabled = not self.tracking_enabled
        return self.tracking_enabled

    def toggle_annotations(self):
        self.annotations_enabled = not self.annotations_enabled
        return self.annotations_enabled

    def process_single_image(self, image, source_name):
        self.stop_processing()
        self.current_source_name = source_name
        self.track_labels.clear()
        self.duplicate_checker.reset()
        self.frame_buffer.clear()
        self.detections_history = []

        classifier = self.model_manager.get_classifier(self.current_mode)
        if classifier.session is None:
            classifier.load_model(use_gpu=self.use_gpu)

        self.tracker = BoTSORTWrapper(
            lost_track_buffer=30,
            frame_rate=30,
            track_activation_threshold=0.6,
            minimum_consecutive_frames=2,
            high_conf_det_threshold=0.5,
            enable_cmc=False,
        )

        self.model_manager.object_detector.conf_threshold = self.conf_threshold
        detections = self.model_manager.object_detector.detect_objects(image)
        tracks = self.tracker.update(detections, image)

        annotated = image.copy()
        for trk in tracks:
            bbox = trk["bbox"]
            tid = trk["track_id"]
            label = self.track_labels.get(tid, "?")
            color = get_color_for_class(label)
            cv2.rectangle(annotated, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
            cv2.putText(annotated, f"ID:{tid} {label}", (bbox[0], bbox[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        self.frame_ready.emit(annotated)
        self.last_annotated_frame = annotated

        tracks_to_classify = [
            trk for trk in tracks
            if self.track_labels.get(trk["track_id"], "?") in ("?", "Incertain")
        ]

        if tracks_to_classify:
            worker = InferenceWorker(
                image,
                tracks_to_classify,
                self.model_manager.dinov2,
                self.model_manager.anomaly_detector,
                classifier,
                self.conf_threshold,
                self.anomaly_threshold,
                self.current_mode,
                video_name=source_name,
                frame_idx=0
            )
            worker.result_ready.connect(self._on_inference_result_single)
            worker.start()
            worker.wait()

        if self.track_labels:
            annotated2 = image.copy()
            for trk in tracks:
                bbox = trk["bbox"]
                tid = trk["track_id"]
                label = self.track_labels.get(tid, "?")
                color = get_color_for_class(label)
                cv2.rectangle(annotated2, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
                cv2.putText(annotated2, f"ID:{tid} {label}", (bbox[0], bbox[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            self.frame_ready.emit(annotated2)

        if self.detections_history:
            self.detections_updated.emit(self.detections_history)

        self.tracker = None
        self.inference_worker = None

    def _on_inference_result_single(self, track_id, class_name, confidence, cropped_image, frame_idx, bbox=None):
        self.track_labels[track_id] = class_name
        self.detection_added.emit(class_name, confidence, "")

        if bbox is None:
            bbox = [0, 0, 0, 0]

        detection = Detection(
            frame_idx=frame_idx,
            timestamp_ms=int(datetime.datetime.now().timestamp() * 1000),
            class_id=track_id,
            class_name=class_name,
            confidence=confidence,
            bbox=bbox
        )
        self.detections_history.append(detection)

        if self.save_predictions and cropped_image is not None and class_name not in ("Incertain",):
            self.duplicate_checker.save_image(
                image=cropped_image,
                class_name=class_name,
                video_name=self.current_source_name,
                frame_idx=frame_idx,
                confidence=confidence
            )
            self.image_saved.emit(class_name, "")

    def _on_qt_reader_error(self, error_string):
        if "Unsupported media" in error_string or "codec" in error_string.lower():
            if not self._loading_from_fallback:
                if self._load_timeout is not None:
                    self._load_timeout.stop()
                self._try_fallback(self.current_source_name)

    def _check_media_loaded(self, path):
        if not hasattr(self.current_reader, "_media_loaded") or not self.current_reader._media_loaded:
            self._try_fallback(path)

    def _try_fallback(self, path):
        if self._loading_from_fallback:
            return False

        self._loading_from_fallback = True
        self._release_all_readers()

        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            self.error_occurred.emit(f"❌ Fichier introuvable : {abs_path}")
            self._loading_from_fallback = False
            return False

        if self._open_with_cv2_reader(abs_path):
            self._loading_from_fallback = False
            return True

        converted = self._convert_video_to_h264(abs_path)
        if converted and os.path.exists(converted):
            self._loading_from_fallback = False
            return self.load_video(converted)

        self.error_occurred.emit(
            f"❌ Échec chargement vidéo : {abs_path}\n"
            f"Causes possibles :\n"
            f"- codec non supporté\n"
            f"- OpenCV sans FFMPEG\n"
            f"- fichier corrompu\n"
            f"- format exotique"
        )
        self._loading_from_fallback = False
        return False

    def _open_with_cv2_reader(self, abs_path):
        cap = cv2.VideoCapture(abs_path)
        if not cap.isOpened():
            cap.release()
            return False

        self._opencv_cap = cap
        self.current_reader = VideoReader()
        self.current_reader.cap = cap
        self.current_reader.video_path = abs_path
        self.current_reader.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.current_reader.fps = cap.get(cv2.CAP_PROP_FPS) or 30
        self.current_reader.frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.current_reader.frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.current_reader.is_playing = False

        self.current_source_name = os.path.basename(abs_path)
        self._connect_signals(self.current_reader)

        self.video_opened.emit(
            self.current_source_name,
            self.current_reader.total_frames,
            self.current_reader.fps
        )
        self.progress_updated.emit(0, self.current_reader.total_frames, self.current_reader.fps)
        self.error_occurred.emit("ℹ️ Vidéo lue avec fallback OpenCV")
        return True

    def _convert_video_to_h264(self, input_path, output_path=None):
        try:
            if output_path is None:
                base, _ = os.path.splitext(input_path)
                output_path = base + "_h264.mp4"

            (
                ffmpeg
                .input(input_path)
                .output(
                    output_path,
                    vcodec="libx264",
                    acodec="aac",
                    pix_fmt="yuv420p",
                    movflags="+faststart"
                )
                .overwrite_output()
                .run(quiet=True)
            )
            return output_path
        except Exception as e:
            self.error_occurred.emit(f"❌ Échec conversion vidéo: {e}")
            return None
    def _start_display_timer(self):
        if self.display_timer is None:
            self.display_timer = QTimer()
            self.display_timer.timeout.connect(self._display_next_frame)
        if not self.display_timer.isActive():
            self.display_timer.start(int(1000 / 30))

    def _stop_display_timer(self):
        if self.display_timer and self.display_timer.isActive():
            self.display_timer.stop()
        self.display_timer = None

    def _display_next_frame(self):
        if self.frame_buffer:
            frame = self.frame_buffer.pop(0)
            self.frame_ready.emit(frame)
            self.progress_updated.emit(self.current_frame_idx, self.position_slider_max, self.fps)
        else:
            if not self.sound_paused and self.current_reader and hasattr(self.current_reader, "set_muted"):
                self.current_reader.set_muted(True)
                self.sound_paused = True
                self.error_occurred.emit("⚠️ Traitement trop lent, mise en pause du son...")