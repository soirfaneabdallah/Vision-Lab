# fishid/controllers/history_handler.py
import json
from PySide6.QtWidgets import QMessageBox
from fishid.ui.history_dialog import HistoryDialog


class HistoryHandler:
    def __init__(self, session_history):
        self.session_history = session_history

    def show_history(self, parent):
        history = self.session_history.load()
        if not history:
            QMessageBox.information(parent, "Historique vide", "Aucune session enregistrée.")
            return
        def delete_callback(session_id):
            all_sessions = self.session_history.load()
            new_sessions = [s for s in all_sessions if s.get('session_id') != session_id]
            with open(self.session_history.history_path, 'w', encoding='utf-8') as f:
                json.dump(new_sessions, f, indent=2, ensure_ascii=False)
        dialog = HistoryDialog(parent, history, delete_callback)
        dialog.exec()