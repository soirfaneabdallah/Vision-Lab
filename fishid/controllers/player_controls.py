# fishid/controllers/player_controls.py
from PySide6.QtCore import Qt
from fishid.utils import load_svg_icon


class PlayerControls:
    def __init__(self, parent, video_handler, theme_getter):
        self.parent = parent
        self.video_handler = video_handler
        self.theme_getter = theme_getter
        self.btn_play_pause = parent.btn_play_pause
        self.btn_stop = parent.btn_stop
        self.position_slider = parent.position_slider
        self.lbl_time = parent.lbl_time
        self._is_seeking = False  # Flag pour éviter les conflits pendant le seek

    def update_play_pause_icon(self):
        color = Qt.white if self.theme_getter() == "dark" else Qt.black
        icon_name = "pause.svg" if self.video_handler.is_playing else "play.svg"
        self.btn_play_pause.setIcon(load_svg_icon(icon_name, color, 24))

    def on_play_pause_clicked(self):
        self.video_handler.toggle_play_pause()
        self.update_play_pause_icon()

    def on_stop_clicked(self):
        self.video_handler.stop_processing()
        self.update_play_pause_icon()

    def on_slider_moved(self, pos):
        """Appelé quand l'utilisateur glisse le curseur."""
        self._is_seeking = True
        self.video_handler.seek(pos)

    def on_slider_pressed(self):
        """Appelé quand l'utilisateur clique sur la barre."""
        self._is_seeking = True

    def on_slider_released(self):
        """Appelé quand l'utilisateur relâche le curseur."""
        if self._is_seeking:
            pos = self.position_slider.value()
            self.video_handler.seek(pos)
            self._is_seeking = False

    def update_progress(self, current, total, fps):
        """Met à jour la barre de progression et le temps."""
        if current > total:
            current = total
        if current < 0:
            current = 0
        
        # Mettre à jour le slider sans bloquer les signaux
        self.position_slider.blockSignals(False)  #  NE PAS BLOQUER
        self.position_slider.setMaximum(total)
        self.position_slider.setValue(current)
        self.position_slider.blockSignals(False)
        
        if fps > 0:
            curr_sec = int(current / fps) if current > 0 else 0
            total_sec = int(total / fps) if total > 0 else 0
            remain_sec = total_sec - curr_sec
            if remain_sec < 0:
                remain_sec = 0
            
            current_str = self._format_time(curr_sec)
            total_str = self._format_time(total_sec)
            remain_str = self._format_time(remain_sec)
            self.lbl_time.setText(f"{current_str} / {total_str} (-{remain_str})")

    def on_slider_moved(self, pos):
        self._is_seeking = True
        self.video_handler.seek(pos)

    def on_slider_released(self):
        if self._is_seeking:
            pos = self.position_slider.value()
            self.video_handler.seek(pos)
            self._is_seeking = False

    def _format_time(self, seconds):
        """Formate un temps en secondes au format HH:MM:SS."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"