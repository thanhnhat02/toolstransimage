"""
Progress tracking panel — batch statistics, ETA, live log output.
"""
import logging
import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class StatCard(QWidget):
    """Small stat display card (number + subtitle)."""

    def __init__(self, title: str, value: str = "—", parent=None):
        super().__init__(parent)
        self.setObjectName("stat_card")
        self.setStyleSheet("""
            #stat_card {
                background: #161B22;
                border: 1px solid #21262D;
                border-radius: 8px;
            }
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(2)
        lay.setAlignment(Qt.AlignCenter)

        self._value_lbl = QLabel(value)
        self._value_lbl.setObjectName("info_stat")
        self._value_lbl.setAlignment(Qt.AlignCenter)
        self._value_lbl.setStyleSheet(
            "font-size: 22px; font-weight: 700; color: #58A6FF;"
        )

        self._title_lbl = QLabel(title)
        self._title_lbl.setObjectName("info_stat_sub")
        self._title_lbl.setAlignment(Qt.AlignCenter)
        self._title_lbl.setStyleSheet("font-size: 11px; color: #8B949E;")

        lay.addWidget(self._value_lbl)
        lay.addWidget(self._title_lbl)

    def set_value(self, v: str):
        self._value_lbl.setText(v)


class ProgressPanel(QWidget):
    """Bottom panel showing progress bars, stats, controls and log."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._total = 0
        self._done = 0
        self._failed = 0
        self._start_time: float = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_elapsed)
        self._build_ui()

    # ------------------------------------------------------------------ #
    # Build UI
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(12, 8, 12, 8)
        main.setSpacing(8)

        # ── Stat cards ───────────────────────────────────────────────── #
        stats_row = QHBoxLayout()
        stats_row.setSpacing(8)

        self._card_total    = StatCard("Total",     "0")
        self._card_done     = StatCard("Completed", "0")
        self._card_failed   = StatCard("Failed",    "0")
        self._card_remain   = StatCard("Remaining", "0")
        self._card_elapsed  = StatCard("Elapsed",   "0:00")
        self._card_eta      = StatCard("ETA",       "—")
        self._card_speed    = StatCard("Img/Min",   "—")

        for card in (
            self._card_total, self._card_done, self._card_failed,
            self._card_remain, self._card_elapsed, self._card_eta, self._card_speed
        ):
            stats_row.addWidget(card)

        main.addLayout(stats_row)

        # ── Progress bars ─────────────────────────────────────────────── #
        prog_widget = QWidget()
        prog_widget.setStyleSheet("""
            background: #161B22;
            border: 1px solid #21262D;
            border-radius: 8px;
        """)
        prog_lay = QVBoxLayout(prog_widget)
        prog_lay.setContentsMargins(12, 10, 12, 10)
        prog_lay.setSpacing(6)

        # Overall batch progress
        overall_row = QHBoxLayout()
        overall_row.addWidget(QLabel("Overall"))
        self._pb_overall = QProgressBar()
        self._pb_overall.setObjectName("pb_overall")
        self._pb_overall.setRange(0, 100)
        self._pb_overall.setValue(0)
        overall_row.addWidget(self._pb_overall, 1)
        self._lbl_pct = QLabel("0%")
        self._lbl_pct.setFixedWidth(40)
        self._lbl_pct.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._lbl_pct.setStyleSheet("color: #58A6FF; font-weight: 700;")
        overall_row.addWidget(self._lbl_pct)
        prog_lay.addLayout(overall_row)

        # Current image
        curr_row = QHBoxLayout()
        self._lbl_current = QLabel("Ready")
        self._lbl_current.setStyleSheet("color: #8B949E; font-size: 12px;")
        curr_row.addWidget(self._lbl_current)
        prog_lay.addLayout(curr_row)

        main.addWidget(prog_widget)

        # ── Control buttons ───────────────────────────────────────────── #
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(8)

        self.btn_pause  = QPushButton("⏸  Pause")
        self.btn_resume = QPushButton("▶  Resume")
        self.btn_stop   = QPushButton("⏹  Stop")
        self.btn_clear  = QPushButton("🗑  Clear Log")

        self.btn_pause.setObjectName("btn_warning")
        self.btn_resume.setObjectName("btn_success")
        self.btn_stop.setObjectName("btn_danger")
        self.btn_clear.setObjectName("btn_icon")

        self.btn_pause.setEnabled(False)
        self.btn_resume.setEnabled(False)
        self.btn_stop.setEnabled(False)

        self.btn_clear.clicked.connect(self._clear_log)

        ctrl_row.addWidget(self.btn_pause)
        ctrl_row.addWidget(self.btn_resume)
        ctrl_row.addWidget(self.btn_stop)
        ctrl_row.addStretch()
        ctrl_row.addWidget(self.btn_clear)

        main.addLayout(ctrl_row)

        # ── Log output ────────────────────────────────────────────────── #
        log_grp = QGroupBox("Processing Log")
        log_lay = QVBoxLayout(log_grp)
        log_lay.setContentsMargins(8, 8, 8, 8)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumHeight(200)
        self._log.setPlaceholderText("Processing log will appear here …")
        log_lay.addWidget(self._log)

        main.addWidget(log_grp)

    # ------------------------------------------------------------------ #
    # Public API (called from main window via signals)
    # ------------------------------------------------------------------ #

    def reset(self, total: int):
        self._total = total
        self._done = 0
        self._failed = 0
        self._start_time = time.perf_counter()

        self._card_total.set_value(str(total))
        self._card_done.set_value("0")
        self._card_failed.set_value("0")
        self._card_remain.set_value(str(total))
        self._card_elapsed.set_value("0:00")
        self._card_eta.set_value("—")
        self._card_speed.set_value("—")

        self._pb_overall.setValue(0)
        self._lbl_pct.setText("0%")
        self._lbl_current.setText("Processing …")

        self.btn_pause.setEnabled(True)
        self.btn_stop.setEnabled(True)
        self.btn_resume.setEnabled(False)

        self._timer.start(1000)

    def mark_started(self, idx: int, filename: str):
        self._lbl_current.setText(f"Processing: {filename}")
        self._lbl_current.setStyleSheet("color: #58A6FF; font-size: 12px;")

    @Slot(int, int)
    def on_progress(self, done: int, total: int):
        self._done = done
        pct = int(done / total * 100) if total else 0
        self._pb_overall.setValue(pct)
        self._lbl_pct.setText(f"{pct}%")
        self._card_done.set_value(str(done))
        self._card_remain.set_value(str(total - done))

    @Slot(float, float)
    def on_eta(self, elapsed: float, eta: float):
        self._card_eta.set_value(self._fmt_secs(eta))
        # Speed
        done = self._done
        if elapsed > 0 and done > 0:
            speed = done / elapsed * 60
            self._card_speed.set_value(f"{speed:.1f}")

    @Slot(str)
    def append_log(self, msg: str):
        self._log.moveCursor(QTextCursor.End)
        self._log.insertPlainText(msg + "\n")
        self._log.moveCursor(QTextCursor.End)

    def mark_done(self):
        elapsed = time.perf_counter() - self._start_time
        self._timer.stop()
        self._lbl_current.setText(f"✓ Completed in {self._fmt_secs(elapsed)}")
        self._lbl_current.setStyleSheet("color: #56D364; font-size: 12px; font-weight: 600;")
        self._card_elapsed.set_value(self._fmt_secs(elapsed))
        self._card_eta.set_value("Done")

        self.btn_pause.setEnabled(False)
        self.btn_resume.setEnabled(False)
        self.btn_stop.setEnabled(False)

    def mark_paused(self):
        self._timer.stop()
        self.btn_pause.setEnabled(False)
        self.btn_resume.setEnabled(True)
        self._lbl_current.setText("⏸ Paused")
        self._lbl_current.setStyleSheet("color: #F0883E; font-size: 12px;")

    def mark_resumed(self):
        self._timer.start(1000)
        self.btn_pause.setEnabled(True)
        self.btn_resume.setEnabled(False)

    def mark_stopped(self):
        self._timer.stop()
        self.btn_pause.setEnabled(False)
        self.btn_resume.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self._lbl_current.setText("⏹ Stopped")
        self._lbl_current.setStyleSheet("color: #F85149; font-size: 12px;")

    # ------------------------------------------------------------------ #
    # Internal
    # ------------------------------------------------------------------ #

    def _update_elapsed(self):
        elapsed = time.perf_counter() - self._start_time
        self._card_elapsed.set_value(self._fmt_secs(elapsed))

    def _clear_log(self):
        self._log.clear()

    @staticmethod
    def _fmt_secs(secs: float) -> str:
        secs = int(secs)
        m, s = divmod(secs, 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"
