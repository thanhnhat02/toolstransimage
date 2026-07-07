"""
Dark theme QSS stylesheet for AI Image Enhancer.
Modern dark UI with accent colors inspired by professional creative tools.
"""

DARK_THEME = """
/* ─── Global ─────────────────────────────────────────────────────── */
* {
    font-family: 'Segoe UI', 'Ubuntu', 'Inter', sans-serif;
    font-size: 13px;
    color: #E8EAED;
    outline: none;
}

QMainWindow, QWidget {
    background-color: #0F1117;
}

QDialog {
    background-color: #161B22;
    border: 1px solid #30363D;
    border-radius: 8px;
}

/* ─── Scrollbars ─────────────────────────────────────────────────── */
QScrollBar:vertical {
    background: #161B22;
    width: 8px;
    margin: 0;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #30363D;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #58A6FF; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal {
    background: #161B22;
    height: 8px;
    margin: 0;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #30363D;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background: #58A6FF; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ─── GroupBox ───────────────────────────────────────────────────── */
QGroupBox {
    background-color: #161B22;
    border: 1px solid #21262D;
    border-radius: 8px;
    margin-top: 14px;
    padding: 12px 8px 8px 8px;
    font-size: 12px;
    font-weight: 600;
    color: #8B949E;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    top: 0px;
    padding: 0 6px;
    color: #8B949E;
}

/* ─── Labels ─────────────────────────────────────────────────────── */
QLabel {
    color: #C9D1D9;
    background: transparent;
}
QLabel#title_label {
    font-size: 22px;
    font-weight: 700;
    color: #58A6FF;
    letter-spacing: -0.5px;
}
QLabel#subtitle_label {
    font-size: 12px;
    color: #8B949E;
}
QLabel#status_label {
    font-size: 12px;
    color: #56D364;
    font-weight: 500;
}
QLabel#error_label {
    font-size: 12px;
    color: #F85149;
}
QLabel#info_stat {
    font-size: 20px;
    font-weight: 700;
    color: #58A6FF;
}
QLabel#info_stat_sub {
    font-size: 11px;
    color: #8B949E;
}

/* ─── Push Buttons ───────────────────────────────────────────────── */
QPushButton {
    background-color: #21262D;
    color: #C9D1D9;
    border: 1px solid #30363D;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
    min-height: 32px;
}
QPushButton:hover {
    background-color: #30363D;
    border-color: #58A6FF;
    color: #E8EAED;
}
QPushButton:pressed {
    background-color: #161B22;
}
QPushButton:disabled {
    background-color: #161B22;
    color: #484F58;
    border-color: #21262D;
}

QPushButton#btn_primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1F6FEB, stop:1 #58A6FF);
    color: #FFFFFF;
    border: none;
    font-weight: 600;
    font-size: 14px;
    min-height: 42px;
    border-radius: 8px;
}
QPushButton#btn_primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #388BFD, stop:1 #79C0FF);
}
QPushButton#btn_primary:pressed {
    background: #1158C7;
}
QPushButton#btn_primary:disabled {
    background: #21262D;
    color: #484F58;
}

QPushButton#btn_danger {
    background-color: #DA3633;
    color: #FFFFFF;
    border: none;
    font-weight: 600;
}
QPushButton#btn_danger:hover { background-color: #F85149; }
QPushButton#btn_danger:pressed { background-color: #B91C1C; }

QPushButton#btn_success {
    background-color: #238636;
    color: #FFFFFF;
    border: none;
    font-weight: 600;
}
QPushButton#btn_success:hover { background-color: #2EA043; }

QPushButton#btn_warning {
    background-color: #9E6A03;
    color: #FFFFFF;
    border: none;
    font-weight: 600;
}
QPushButton#btn_warning:hover { background-color: #D4A017; }

QPushButton#btn_icon {
    background: transparent;
    border: 1px solid #30363D;
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 28px;
}
QPushButton#btn_icon:hover {
    background: #21262D;
    border-color: #58A6FF;
}

/* ─── ComboBox ───────────────────────────────────────────────────── */
QComboBox {
    background-color: #21262D;
    color: #C9D1D9;
    border: 1px solid #30363D;
    border-radius: 6px;
    padding: 6px 12px;
    min-height: 30px;
}
QComboBox:hover {
    border-color: #58A6FF;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #8B949E;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background-color: #161B22;
    border: 1px solid #30363D;
    border-radius: 6px;
    selection-background-color: #1F6FEB;
    color: #C9D1D9;
    padding: 4px;
}
QComboBox QAbstractItemView::item {
    padding: 6px 12px;
    min-height: 28px;
    border-radius: 4px;
}
QComboBox QAbstractItemView::item:hover {
    background-color: #21262D;
}

/* ─── Sliders ────────────────────────────────────────────────────── */
QSlider::groove:horizontal {
    background: #21262D;
    height: 4px;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #58A6FF;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}
QSlider::handle:horizontal:hover {
    background: #79C0FF;
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1F6FEB, stop:1 #58A6FF);
    border-radius: 2px;
}

/* ─── CheckBox ───────────────────────────────────────────────────── */
QCheckBox {
    color: #C9D1D9;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #30363D;
    border-radius: 4px;
    background: #21262D;
}
QCheckBox::indicator:hover { border-color: #58A6FF; }
QCheckBox::indicator:checked {
    background: #1F6FEB;
    border-color: #1F6FEB;
    image: url(none);
}

/* ─── ProgressBar ────────────────────────────────────────────────── */
QProgressBar {
    background-color: #21262D;
    border: none;
    border-radius: 6px;
    height: 12px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1F6FEB, stop:0.5 #58A6FF, stop:1 #A5D6FF);
    border-radius: 6px;
}

QProgressBar#pb_overall {
    height: 16px;
}
QProgressBar#pb_current {
    height: 8px;
}

/* ─── List / Table ───────────────────────────────────────────────── */
QListWidget, QTreeWidget, QTableWidget {
    background-color: #0D1117;
    border: 1px solid #21262D;
    border-radius: 6px;
    alternate-background-color: #161B22;
    color: #C9D1D9;
    gridline-color: #21262D;
}
QListWidget::item, QTreeWidget::item {
    padding: 6px 8px;
    border-radius: 4px;
    margin: 1px 2px;
}
QListWidget::item:selected, QTreeWidget::item:selected {
    background-color: #1F4A7E;
    color: #E8EAED;
}
QListWidget::item:hover:!selected, QTreeWidget::item:hover:!selected {
    background-color: #21262D;
}

QHeaderView::section {
    background-color: #161B22;
    border: none;
    border-bottom: 1px solid #21262D;
    padding: 6px 8px;
    color: #8B949E;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ─── TextEdit / Log ─────────────────────────────────────────────── */
QTextEdit, QPlainTextEdit {
    background-color: #0D1117;
    border: 1px solid #21262D;
    border-radius: 6px;
    color: #8B949E;
    font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
    font-size: 12px;
    padding: 6px;
    line-height: 1.4;
}

/* ─── LineEdit ───────────────────────────────────────────────────── */
QLineEdit {
    background-color: #21262D;
    border: 1px solid #30363D;
    border-radius: 6px;
    color: #C9D1D9;
    padding: 6px 10px;
    min-height: 30px;
}
QLineEdit:focus { border-color: #58A6FF; }
QLineEdit:read-only {
    background-color: #0D1117;
    color: #8B949E;
}

/* ─── Splitter ───────────────────────────────────────────────────── */
QSplitter::handle {
    background-color: #21262D;
}
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:vertical { height: 1px; }

/* ─── TabWidget ──────────────────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #21262D;
    background-color: #161B22;
    border-radius: 0 6px 6px 6px;
}
QTabBar::tab {
    background: #0F1117;
    color: #8B949E;
    border: 1px solid #21262D;
    border-bottom: none;
    padding: 8px 18px;
    border-radius: 6px 6px 0 0;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #161B22;
    color: #58A6FF;
    border-bottom: 2px solid #58A6FF;
}
QTabBar::tab:hover:!selected {
    background: #21262D;
    color: #C9D1D9;
}

/* ─── Tooltip ────────────────────────────────────────────────────── */
QToolTip {
    background-color: #161B22;
    color: #C9D1D9;
    border: 1px solid #30363D;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}

/* ─── StatusBar ──────────────────────────────────────────────────── */
QStatusBar {
    background-color: #161B22;
    border-top: 1px solid #21262D;
    color: #8B949E;
    font-size: 12px;
    padding: 2px 8px;
}
QStatusBar::item { border: none; }

/* ─── MenuBar / Menu ─────────────────────────────────────────────── */
QMenuBar {
    background-color: #161B22;
    border-bottom: 1px solid #21262D;
    color: #C9D1D9;
}
QMenuBar::item { padding: 6px 12px; background: transparent; }
QMenuBar::item:selected { background: #21262D; border-radius: 4px; }

QMenu {
    background-color: #161B22;
    border: 1px solid #30363D;
    border-radius: 6px;
    padding: 4px;
    color: #C9D1D9;
}
QMenu::item { padding: 6px 24px 6px 12px; border-radius: 4px; }
QMenu::item:selected { background: #1F6FEB; color: #FFFFFF; }
QMenu::separator {
    height: 1px;
    background: #21262D;
    margin: 4px 0;
}

/* ─── ToolBar ────────────────────────────────────────────────────── */
QToolBar {
    background-color: #161B22;
    border-bottom: 1px solid #21262D;
    spacing: 4px;
    padding: 4px;
}
QToolButton {
    background: transparent;
    border: none;
    border-radius: 4px;
    padding: 4px;
    color: #8B949E;
}
QToolButton:hover { background: #21262D; color: #C9D1D9; }
QToolButton:pressed { background: #161B22; }
"""
