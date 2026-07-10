# fishid/ui/history_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget,
    QTreeWidgetItem, QPushButton
)
from fishid.utils import resource_path
from PySide6.QtGui import QPixmap, QIcon
class HistoryDialog(QDialog):
    def __init__(self, parent, history_data, on_delete):
        super().__init__(parent)
        from fishid.utils import add_logo_to_dialog
        # dans __init__ :
        add_logo_to_dialog(self)

        self.setWindowTitle("Historique des sessions")
        self.setMinimumSize(700, 500)
        layout = QVBoxLayout(self)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Date", "Vidéo", "Espèces", "Shannon", "Durée"])
        self.tree.setColumnWidth(0, 160)
        self.tree.setColumnWidth(1, 200)
        self.tree.setColumnWidth(2, 80)
        self.tree.setColumnWidth(3, 80)
        self.tree.setColumnWidth(4, 100)

        for session in history_data:
            item = QTreeWidgetItem(self.tree)
            item.setText(0, session.get('date', '')[:19])
            item.setText(1, session.get('video_name', ''))
            item.setText(2, str(session.get('stats', {}).get('species_count', 0)))
            item.setText(3, f"{session.get('stats', {}).get('shannon', 0):.2f}")
            item.setText(4, session.get('stats', {}).get('duration', ''))
            item.setToolTip(0, session.get('session_id', ''))

        layout.addWidget(self.tree)

        btn_layout = QHBoxLayout()
        delete_btn = QPushButton("Supprimer la session sélectionnée")
        delete_btn.clicked.connect(self._on_delete)
        btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self._on_delete_callback = on_delete

    def _on_delete(self):
        item = self.tree.currentItem()
        if item:
            session_id = item.toolTip(0)
            self._on_delete_callback(session_id)
            self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(item))