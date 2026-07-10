# fishid/ui/styles.py


DARK_THEME = """
/* ================================================================ */
/*          THÈME SOMBRE PROFESSIONNEL MODERNE (2026)               */
/*          Couleurs: Slate Dark + Bleu Vibrant + Rose Accent       */
/* ================================================================ */



/* --- CONTEXTE GÉNÉRAL --- */
QMainWindow {
    background-color: #0B0E14;
    color: #E0E6F0;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}



QWidget {
    background-color: #0B0E14;
    color: #E0E6F0;
}



/* --- HEADER PROF (Dégradé Bleu) --- */
QFrame#headerProf {
    background: linear-gradient(135deg, #89B4FA 0%, #A6C3FC 100%);
    border-radius: 12px;
    padding: 16px;
}



QLabel#headerTitle {
    color: #FFFFFF;
    font-size: 24px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
}



QLabel#headerSubtitle {
    color: #E8F0F8;
    font-size: 14px;
    font-weight: 500;
}



/* --- CARTES DE RÉSUMÉ --- */
QFrame#summaryCard {
    background-color: #1E2433;
    border: 1px solid #3A4254;
    border-radius: 12px;
}



QLabel#summaryTitle {
    color: #89B4FA;
    font-size: 16px;
    font-weight: 700;
    letter-spacing: 0.5px;
}



QFrame#statCard {
    background-color: #2A3244;
    border-radius: 8px;
    padding: 12px;
}



QLabel#statValue {
    color: #89B4FA;
    font-size: 20px;
    font-weight: 700;
}



QLabel#summaryText {
    color: #A0A8B8;
    font-size: 13px;
    line-height: 1.6;
}



/* --- ARBRE MODERNE --- */
QFrame#treeContainer {
    background-color: #1E2433;
    border: 1px solid #3A4254;
    border-radius: 12px;
}



QLabel#treeTitle {
    color: #89B4FA;
    font-size: 16px;
    font-weight: 700;
}



QTreeWidget#detectionTreeModern {
    background-color: #0B0E14;
    border: none;
    border-radius: 8px;
    font-size: 13px;
}



QTreeWidget#detectionTreeModern::item {
    height: 38px;
    padding: 8px;
    border-radius: 6px;
    color: #E0E6F0;
}



QTreeWidget#detectionTreeModern::item:selected {
    background-color: #3A4254;
    color: #89B4FA;
}



QTreeWidget#detectionTreeModern::item:hover {
    background-color: #2A3244;
}



QTreeWidget#detectionTreeModern::header {
    background-color: #3A4254;
    color: #89B4FA;
    font-weight: 700;
    font-size: 12px;
    height: 32px;
}



/* --- BARRE D'ACTIONS --- */
QFrame#actionsBar {
    background-color: #1E2433;
    border: 1px solid #3A4254;
    border-radius: 12px;
}



QPushButton#btnClearProf {
    background-color: #FFB3BA;
    color: #FFFFFF;
    font-size: 13px;
    font-weight: 700;
    border-radius: 8px;
    padding: 12px 20px;
    border: none;
    text-transform: uppercase;
}



QPushButton#btnClearProf:hover {
    background-color: #FF9BA5;
}



QPushButton#btnExportProf {
    background-color: #89B4FA;
    color: #FFFFFF;
    font-size: 13px;
    font-weight: 700;
    border-radius: 8px;
    padding: 12px 20px;
    border: none;
    text-transform: uppercase;
}



QPushButton#btnExportProf:hover {
    background-color: #6FA3F0;
}



/* --- BANDEAU DE TITRE --- */
#titleBar {
    background-color: #0B0E14;
    border-bottom: 1px solid #1E2433;
    min-height: 48px;
    max-height: 48px;
}



#titleLabel {
    color: #E0E6F0;
    font-size: 16px;
    font-weight: 700;
    padding-left: 16px;
}



#titleSubLabel {
    color: #89B4FA;
    font-size: 12px;
    padding-left: 8px;
    font-weight: 500;
}



‹!-- Boutons fenêtre -->
#windowMinButton, #windowMaxButton, #windowCloseButton {
    background: transparent;
    color: #A0A8B8;
    border: none;
    font-size: 14px;
    padding: 0 8px;
}



#windowMinButton:hover, #windowMaxButton:hover {
    background: #1E2433;
    color: #E0E6F0;
}



#windowCloseButton:hover {
    background: #F38BA8;
    color: #0B0E14;
}



/* --- BARRE DE MENU --- */
QMenuBar {
    background-color: #0B0E14;
    color: #A0A8B8;
    border-bottom: 1px solid #1E2433;
    padding: 4px 0;
}



QMenuBar::item:selected {
    background-color: #1E2433;
    color: #E0E6F0;
    border-radius: 6px;
}



QMenu {
    background-color: #12161F;
    color: #E0E6F0;
    border: 1px solid #1E2433;
    border-radius: 10px;
    padding: 6px;
}



QMenu::item:selected {
    background-color: #1E2433;
    color: #89B4FA;
    border-radius: 6px;
}



QMenu::separator {
    height: 1px;
    background: #1E2433;
    margin: 4px 8px;
}



/* --- PANNEAUX --- */
#leftPanel, #rightPanel {
    background-color: #11151C;
    border: 1px solid #1E2433;
    border-radius: 12px;
    padding: 16px;
}



/* --- TEXTES --- */
#videoPanelTitle {
    color: #E0E6F0;
    font-weight: 700;
    font-size: 14px;
}



#videoListLabel, #timeLabel, #threshLabel, #frameLabel, #speedLabel {
    color: #A0A8B8;
    font-size: 11px;
}



#lblThreshold, #lblSpeed {
    color: #89B4FA;
    font-weight: 700;
}



#lblFrameInfo {
    color: #6C7086;
    font-size: 10px;
}



/* --- BOUTONS PRINCIPAUX --- */
QPushButton {
    background-color: #89B4FA;
    color: #0B0E14;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 700;
    font-size: 13px;
}



QPushButton:hover {
    background-color: #74A8F9;
}



QPushButton:pressed {
    background-color: #5D9BF7;
}



QPushButton:disabled {
    background-color: #1E2433;
    color: #585B70;
}



/* --- BOUTON STOP --- */
QPushButton#stopButton {
    background-color: #F38BA8;
    color: #0B0E14;
    border-radius: 8px;
}



QPushButton#stopButton:hover {
    background-color: #F06292;
}



/* --- BOUTONS SPEED PRESET --- */
QPushButton.speedPreset {
    background-color: #1E2433;
    color: #A0A8B8;
    border: 1px solid #313855;
    border-radius: 4px;
    font-size: 11px;
    padding: 4px 8px;
}



QPushButton.speedPreset:hover {
    background-color: #89B4FA;
    color: #0B0E14;
}



/* --- LISTE --- */
QListWidget {
    background-color: #0B0E14;
    color: #E0E6F0;
    border: 1px solid #1E2433;
    border-radius: 8px;
    padding: 6px;
    outline: none;
}



QListWidget::item:selected {
    background-color: #1E2433;
    color: #89B4FA;
    border-radius: 4px;
}



/* --- VIEWER --- */
#viewerWidget {
    background-color: #11151C;
    border-radius: 8px;
}



#viewerLabel {
    color: #585B70;
    font-size: 18px;
    border: none;
    background: transparent;
}



/* --- ARBRE DÉTECTIONS (style plus polished) --- */
#detectionTree {
    background-color: #0B0E14;
    color: #E0E6F0;
    border: 1px solid #1E2433;
    border-radius: 8px;
    font-size: 13px;
    alternate-background-color: #11151C;
}



#detectionTree::item {
    height: 35px;
    padding: 8px;
    border-bottom: 1px solid #1E2433;
}



#detectionTree::item:selected {
    background-color: #1E2433;
    color: #89B4FA;
}



QHeaderView::section {
    background-color: #3A4254;
    color: #89B4FA;
    border: none;
    padding: 10px 8px;
    font-weight: 700;
    font-size: 12px;
    border-bottom: 2px solid #89B4FA;
}



#detectionTitle {
    color: #E0E6F0;
    font-weight: 700;
    font-size: 14px;
}



#detectionStats {
    color: #89B4FA;
    font-size: 12px;
}



#clearButton {
    background-color: #1E2433;
    color: #A0A8B8;
    border: none;
    border-radius: 6px;
    font-size: 12px;
    padding: 8px 16px;
}



#clearButton:hover {
    background-color: #F38BA8;
    color: #0B0E14;
}



/* --- SLIDERS --- */
QSlider::groove:horizontal {
    background: #1E2433;
    height: 6px;
    border-radius: 3px;
}



QSlider::handle:horizontal {
    background: #89B4FA;
    width: 20px;
    margin: -7px 0;
    border-radius: 10px;
}



QSlider::handle:horizontal:hover {
    background: #74A8F9;
}



/* --- INPUTS --- */
QDoubleSpinBox, QSpinBox, QLineEdit {
    background-color: #0B0E14;
    color: #E0E6F0;
    border: 1px solid #1E2433;
    border-radius: 6px;
    padding: 8px;
    font-size: 13px;
}



QDoubleSpinBox:focus, QSpinBox:focus, QLineEdit:focus {
    border: 1px solid #89B4FA;
}



/* --- PROGRESS BAR --- */
QProgressBar {
    background-color: #0B0E14;
    border: 1px solid #1E2433;
    border-radius: 8px;
    text-align: center;
    color: #E0E6F0;
    height: 22px;
    font-weight: 700;
    font-size: 11px;
}



QProgressBar::chunk {
    background-color: #89B4FA;
    border-radius: 6px;
}



/* --- GROUP BOX --- */
QGroupBox {
    color: #E0E6F0;
    border: 1px solid #1E2433;
    border-radius: 10px;
    margin-top: 16px;
    padding-top: 20px;
    font-weight: 700;
    font-size: 13px;
}



QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: #89B4FA;
    font-weight: 700;
}



/* --- STATUS BAR --- */
QStatusBar {
    background-color: #0B0E14;
    color: #89B4FA;
    border-top: 1px solid #1E2433;
    font-size: 12px;
}



#statusMessage {
    color: #89B4FA;
    padding-left: 10px;
}



#statusVersion {
    color: #6C7086;
    padding-right: 10px;
}



/* --- SCROLLBAR --- */
QScrollBar:vertical, QScrollBar:horizontal {
    background: #11151C;
    border-radius: 4px;
    padding: 2px;
}



QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #3A4254;
    border-radius: 4px;
    min-height: 24px;
}



QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
    background: #89B4FA;
}



QScrollBar::add-line, QScrollBar::sub-line {
    height: 0px;
    width: 0px;
}



/* --- TOOLTIP --- */
QToolTip {
    background-color: #1E2433;
    color: #E0E6F0;
    border: 1px solid #3A4254;
    border-radius: 6px;
    padding: 8px;
    font-size: 12px;
}



/* --- BARRE DE CONTRÔLE --- */
#controlBar {
    background-color: #11151C;
    border-top: 1px solid #1E2433;
    border-radius: 0;
    padding: 8px 16px;
}



#timeLabel {
    color: #E0E6F0;
    font-size: 13px;
    font-weight: 500;
}



QPushButton.controlButton {
    background-color: #3A4254;
    color: #FFFFFF;
    border: 1px solid #5A6079;
    border-radius: 8px;
    font-size: 18px;
    font-weight: 700;
    padding: 8px 16px;
}



QPushButton.controlButton:hover {
    background-color: #89B4FA;
    border-color: #89B4FA;
    color: #FFFFFF;
}



QPushButton.controlButton:pressed {
    background-color: #2A3144;
}



QPushButton.controlButton:disabled {
    background-color: #1E2433;
    color: #585B70;
    border-color: #313855;
}



/* --- DIALOG / PARAMÈTRES --- */
QDialog {
    background-color: #0B0E14;
    color: #E0E6F0;
}



QLabel {
    color: #E0E6F0;
    background: transparent;
    border: none;
}



QCheckBox {
    color: #E0E6F0;
    background: transparent;
    spacing: 8px;
}



QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #89B4FA;
    border-radius: 4px;
    background-color: #0B0E14;
}



QCheckBox::indicator:checked {
    background-color: #89B4FA;
    border-color: #89B4FA;
}



QComboBox {
    background-color: #0B0E14;
    color: #E0E6F0;
    border: 1px solid #1E2433;
    border-radius: 6px;
    padding: 8px;
    font-size: 13px;
}



QComboBox::drop-down {
    border: none;
}



QComboBox::down-arrow {
    width: 12px;
    height: 12px;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid #89B4FA;
    margin-right: 8px;
}



QComboBox QAbstractItemView {
    background-color: #12161F;
    color: #E0E6F0;
    selection-background-color: #1E2433;
    border: 1px solid #1E2433;
    border-radius: 6px;
    padding: 4px;
}



/* --- BOUTON EXPORT --- */
QPushButton#exportButton {
    background-color: #00BFA6;
    color: #0B0E14;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 700;
    font-size: 13px;
}



QPushButton#exportButton:hover {
    background-color: #00D4B8;
}



QPushButton#exportButton:pressed {
    background-color: #00A48E;
}



/* --- CARTES INDICATEURS --- */
#indicatorTile, #diversityCard {
    background-color: #1E2433;
    border: 1px solid #3A4254;
    border-radius: 8px;
    padding: 12px;
}



/* --- PANNEAU DÉTECTIONS (style plus polished) --- */
#detectionTree {
    background-color: #1B1E2A;
    color: #E0E6F0;
    border: 1px solid #2E3440;
    border-radius: 8px;
    font-size: 13px;
    alternate-background-color: #222634;
}



#detectionTree::item {
    padding: 8px 4px;
    border-bottom: 1px solid #2E3440;
}



#detectionTree::item:selected {
    background-color: #2E3A4D;
    color: #FFFFFF;
}



QHeaderView::section {
    background-color: #2A2E3C;
    color: #89B4FA;
    font-weight: 700;
    padding: 10px 8px;
    border: none;
    border-bottom: 2px solid #89B4FA;
}
"""


LIGHT_THEME = """
/* ================================================================ */
/*          THÈME JOUR PROFESSIONNEL MODERNE (2026)                 */
/*          Couleurs: Slate Light + Bleu Vibrant + Rose Accent      */
/*          Structure identique au DARK_THEME                       */
/* ================================================================ */



/* --- CONTEXTE GÉNÉRAL --- */
QMainWindow {
    background-color: #F4F6F9;
    color: #1E293B;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}



QWidget {
    background-color: #F4F6F9;
    color: #1E293B;
}



/* --- HEADER PROF (Dégradé Bleu) --- */
QFrame#headerProf {
    background: linear-gradient(135deg, #2563EB 0%, #3B82F6 100%);
    border-radius: 12px;
    padding: 16px;
}



QLabel#headerTitle {
    color: #FFFFFF;
    font-size: 24px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
}



QLabel#headerSubtitle {
    color: #E8F0F8;
    font-size: 14px;
    font-weight: 500;
}



/* --- CARTES DE RÉSUMÉ --- */
QFrame#summaryCard {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
}



QLabel#summaryTitle {
    color: #2563EB;
    font-size: 16px;
    font-weight: 700;
    letter-spacing: 0.5px;
}



QFrame#statCard {
    background-color: #F8FAFC;
    border-radius: 8px;
    padding: 12px;
}



QLabel#statValue {
    color: #2563EB;
    font-size: 20px;
    font-weight: 700;
}



QLabel#summaryText {
    color: #64748B;
    font-size: 13px;
    line-height: 1.6;
}



/* --- ARBRE MODERNE --- */
QFrame#treeContainer {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
}



QLabel#treeTitle {
    color: #2563EB;
    font-size: 16px;
    font-weight: 700;
}



QTreeWidget#detectionTreeModern {
    background-color: #F4F6F9;
    border: none;
    border-radius: 8px;
    font-size: 13px;
}



QTreeWidget#detectionTreeModern::item {
    height: 38px;
    padding: 8px;
    border-radius: 6px;
    color: #1E293B;
}



QTreeWidget#detectionTreeModern::item:selected {
    background-color: #E2E8F0;
    color: #2563EB;
}



QTreeWidget#detectionTreeModern::item:hover {
    background-color: #F1F5F9;
}



QTreeWidget#detectionTreeModern::header {
    background-color: #E2E8F0;
    color: #2563EB;
    font-weight: 700;
    font-size: 12px;
    height: 32px;
}



/* --- BARRE D'ACTIONS --- */
QFrame#actionsBar {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
}



QPushButton#btnClearProf {
    background-color: #DC3545;
    color: #FFFFFF;
    font-size: 13px;
    font-weight: 700;
    border-radius: 8px;
    padding: 12px 20px;
    border: none;
    text-transform: uppercase;
}



QPushButton#btnClearProf:hover {
    background-color: #B02A37;
}



QPushButton#btnExportProf {
    background-color: #2563EB;
    color: #FFFFFF;
    font-size: 13px;
    font-weight: 700;
    border-radius: 8px;
    padding: 12px 20px;
    border: none;
    text-transform: uppercase;
}



QPushButton#btnExportProf:hover {
    background-color: #1D4ED8;
}



/* --- BANDEAU DE TITRE --- */
#titleBar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E2E8F0;
    min-height: 48px;
    max-height: 48px;
}



#titleLabel {
    color: #1E293B;
    font-size: 16px;
    font-weight: 700;
    padding-left: 16px;
}



#titleSubLabel {
    color: #2563EB;
    font-size: 12px;
    padding-left: 8px;
    font-weight: 500;
}



‹!-- Boutons fenêtre -->
#windowMinButton, #windowMaxButton, #windowCloseButton {
    background: transparent;
    color: #64748B;
    border: none;
    font-size: 14px;
    padding: 0 8px;
}



#windowMinButton:hover, #windowMaxButton:hover {
    background: #E2E8F0;
    color: #1E293B;
}



#windowCloseButton:hover {
    background: #DC3545;
    color: #FFFFFF;
}



/* --- BARRE DE MENU --- */
QMenuBar {
    background-color: #FFFFFF;
    color: #64748B;
    border-bottom: 1px solid #E2E8F0;
    padding: 4px 0;
}



QMenuBar::item:selected {
    background-color: #E2E8F0;
    color: #1E293B;
    border-radius: 6px;
}



QMenu {
    background-color: #FFFFFF;
    color: #1E293B;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 6px;
}



QMenu::item:selected {
    background-color: #F1F5F9;
    color: #2563EB;
    border-radius: 6px;
}



QMenu::separator {
    height: 1px;
    background: #E2E8F0;
    margin: 4px 8px;
}



/* --- PANNEAUX --- */
#leftPanel, #rightPanel {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 16px;
}



/* --- TEXTES --- */
#videoPanelTitle {
    color: #1E293B;
    font-weight: 700;
    font-size: 14px;
}



#videoListLabel, #timeLabel, #threshLabel, #frameLabel, #speedLabel {
    color: #64748B;
    font-size: 11px;
}



#lblThreshold, #lblSpeed {
    color: #2563EB;
    font-weight: 700;
}



#lblFrameInfo {
    color: #94A3B8;
    font-size: 10px;
}



/* --- BOUTONS PRINCIPAUX --- */
QPushButton {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 700;
    font-size: 13px;
}



QPushButton:hover {
    background-color: #1D4ED8;
}



QPushButton:pressed {
    background-color: #173EA6;
}



QPushButton:disabled {
    background-color: #E2E8F0;
    color: #94A3B8;
}



/* --- BOUTON STOP --- */
QPushButton#stopButton {
    background-color: #DC3545;
    color: #FFFFFF;
    border-radius: 8px;
}



QPushButton#stopButton:hover {
    background-color: #B02A37;
}



/* --- BOUTONS SPEED PRESET --- */
QPushButton.speedPreset {
    background-color: #E2E8F0;
    color: #64748B;
    border: 1px solid #CBD5E1;
    border-radius: 4px;
    font-size: 11px;
    padding: 4px 8px;
}



QPushButton.speedPreset:hover {
    background-color: #2563EB;
    color: #FFFFFF;
}



/* --- LISTE --- */
QListWidget {
    background-color: #FFFFFF;
    color: #1E293B;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 6px;
    outline: none;
}



QListWidget::item:selected {
    background-color: #F1F5F9;
    color: #2563EB;
    border-radius: 4px;
}



/* --- VIEWER --- */
#viewerWidget {
    background-color: #F8FAFC;
    border-radius: 8px;
}



#viewerLabel {
    color: #94A3B8;
    font-size: 18px;
    border: none;
    background: transparent;
}



/* --- ARBRE DÉTECTIONS --- */
#detectionTree {
    background-color: #FFFFFF;
    color: #1E293B;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    font-size: 13px;
    alternate-background-color: #F8FAFC;
}



#detectionTree::item {
    height: 35px;
    padding: 8px;
    border-bottom: 1px solid #E2E8F0;
}



#detectionTree::item:selected {
    background-color: #F1F5F9;
    color: #2563EB;
}



QHeaderView::section {
    background-color: #F4F6F9;
    color: #2563EB;
    border: none;
    padding: 10px 8px;
    font-weight: 700;
    font-size: 12px;
    border-bottom: 2px solid #2563EB;
}



#detectionTitle {
    color: #1E293B;
    font-weight: 700;
    font-size: 14px;
}



#detectionStats {
    color: #2563EB;
    font-size: 12px;
}



#clearButton {
    background-color: #E2E8F0;
    color: #64748B;
    border: none;
    border-radius: 6px;
    font-size: 12px;
    padding: 8px 16px;
}



#clearButton:hover {
    background-color: #DC3545;
    color: #FFFFFF;
}



/* --- SLIDERS --- */
QSlider::groove:horizontal {
    background: #E2E8F0;
    height: 6px;
    border-radius: 3px;
}



QSlider::handle:horizontal {
    background: #2563EB;
    width: 20px;
    margin: -7px 0;
    border-radius: 10px;
}



QSlider::handle:horizontal:hover {
    background: #1D4ED8;
}



/* --- INPUTS --- */
QDoubleSpinBox, QSpinBox, QLineEdit {
    background-color: #FFFFFF;
    color: #1E293B;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 8px;
    font-size: 13px;
}



QDoubleSpinBox:focus, QSpinBox:focus, QLineEdit:focus {
    border: 1px solid #2563EB;
}



/* --- PROGRESS BAR --- */
QProgressBar {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    text-align: center;
    color: #1E293B;
    height: 22px;
    font-weight: 700;
    font-size: 11px;
}



QProgressBar::chunk {
    background-color: #2563EB;
    border-radius: 6px;
}



/* --- GROUP BOX --- */
QGroupBox {
    color: #1E293B;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    margin-top: 16px;
    padding-top: 20px;
    font-weight: 700;
    font-size: 13px;
}



QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: #2563EB;
    font-weight: 700;
}



/* --- STATUS BAR --- */
QStatusBar {
    background-color: #FFFFFF;
    color: #2563EB;
    border-top: 1px solid #E2E8F0;
    font-size: 12px;
}



#statusMessage {
    color: #2563EB;
    padding-left: 10px;
}



#statusVersion {
    color: #94A3B8;
    padding-right: 10px;
}



/* --- SCROLLBAR --- */
QScrollBar:vertical, QScrollBar:horizontal {
    background: #F8FAFC;
    border-radius: 4px;
    padding: 2px;
}



QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #CBD5E1;
    border-radius: 4px;
    min-height: 24px;
}



QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
    background: #2563EB;
}



QScrollBar::add-line, QScrollBar::sub-line {
    height: 0px;
    width: 0px;
}



/* --- TOOLTIP --- */
QToolTip {
    background-color: #FFFFFF;
    color: #1E293B;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 8px;
    font-size: 12px;
}



/* --- BARRE DE CONTRÔLE --- */
#controlBar {
    background-color: #FFFFFF;
    border-top: 1px solid #E2E8F0;
    border-radius: 0;
    padding: 8px 16px;
}



#timeLabel {
    color: #1E293B;
    font-size: 13px;
    font-weight: 500;
}



QPushButton.controlButton {
    background-color: #FFFFFF;
    color: #1E293B;
    border: 1px solid #C5D3E8;
    border-radius: 8px;
    font-size: 18px;
    font-weight: 700;
    padding: 8px 16px;
}



QPushButton.controlButton:hover {
    background-color: #EAF0FA;
    border-color: #2563EB;
    color: #2563EB;
}



QPushButton.controlButton:pressed {
    background-color: #D0DFF5;
}



QPushButton.controlButton:disabled {
    background-color: #F0F2F5;
    color: #A0B0C0;
    border-color: #E2E8F0;
}



/* --- DIALOG / PARAMÈTRES --- */
QDialog {
    background-color: #F4F6F9;
    color: #1E293B;
}
"""