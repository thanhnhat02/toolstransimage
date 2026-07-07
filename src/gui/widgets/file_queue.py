"""
File queue widget — lists selected images with status indicators.
"""
import logging
from enum import Enum
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class FileStatus(Enum):
    PENDING  = ("⏳", "#8B949E")
    RUNNING  = ("⚙️", "#58A6FF")
    DONE     = ("✓",  "#56D364")
    FAILED   = ("✗",  "#F85149")
    SKIPPED  = ("—",  "#8B949E")


class FileQueueWidget(QWidget):
    """
    Displays the list of images queued for processing with
    per-item status icons.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._paths: List[Path] = []
        self._items: List[QListWidgetItem] = []
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        # Header
        header = QHBoxLayout()
        self._title = QLabel("Image Queue")
        self._title.setStyleSheet("font-weight: 700; font-size: 13px; color: #C9D1D9;")
        self._count_lbl = QLabel("0 images")
        self._count_lbl.setStyleSheet("color: #8B949E; font-size: 12px;")
        header.addWidget(self._title)
        header.addStretch()
        header.addWidget(self._count_lbl)
        lay.addLayout(header)

        # List
        self._list = QListWidget()
        self._list.setSelectionMode(QAbstractItemView.SingleSelection)
        self._list.setAlternatingRowColors(True)
        self._list.setSortingEnabled(False)
        self._list.setDragEnabled(False)
        lay.addWidget(self._list)

    def set_images(self, paths: List[Path]):
        self._paths = paths
        self._items = []
        self._list.clear()

        for path in paths:
            item = QListWidgetItem()
            item.setText(f"  ⏳  {path.name}")
            item.setForeground(QColor("#C9D1D9"))
            item.setData(Qt.UserRole, str(path))
            item.setToolTip(str(path))
            self._list.addItem(item)
            self._items.append(item)

        self._count_lbl.setText(f"{len(paths)} image{'s' if len(paths) != 1 else ''}")

    def set_status(self, idx: int, status: FileStatus, detail: str = ""):
        if idx < 0 or idx >= len(self._items):
            return
        item = self._items[idx]
        icon, color = status.value
        name = self._paths[idx].name
        suffix = f"  ({detail})" if detail else ""
        item.setText(f"  {icon}  {name}{suffix}")
        item.setForeground(QColor(color))
        self._list.scrollToItem(item)

    def clear_queue(self):
        self._list.clear()
        self._paths = []
        self._items = []
        self._count_lbl.setText("0 images")

    @property
    def image_count(self) -> int:
        return len(self._paths)
