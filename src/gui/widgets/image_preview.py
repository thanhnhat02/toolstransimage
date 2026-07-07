"""
Image preview widget with before/after split-view comparison.
"""
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QPoint, QRect, QRectF, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QImage,
    QMouseEvent,
    QPainter,
    QPen,
    QPixmap,
    QResizeEvent,
)
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

logger = logging.getLogger(__name__)


class ImagePreviewWidget(QWidget):
    """
    Interactive before/after image comparison widget.
    Drag the divider to compare original vs enhanced.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._before_pixmap: Optional[QPixmap] = None
        self._after_pixmap: Optional[QPixmap] = None
        self._divider_x: float = 0.5   # 0–1 relative position
        self._dragging = False
        self._placeholder_text = "Drop images here or use the buttons above"

        self.setMinimumSize(400, 300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)
        self.setCursor(Qt.ArrowCursor)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def set_before(self, path: Path):
        """Load the original image as the 'before' side."""
        try:
            self._before_pixmap = QPixmap(str(path))
            self._after_pixmap = None
            self._divider_x = 0.5
            self.update()
        except Exception as e:
            logger.warning(f"Cannot load preview: {e}")

    def set_after(self, path: Path):
        """Load the enhanced image as the 'after' side."""
        try:
            self._after_pixmap = QPixmap(str(path))
            self._divider_x = 0.5
            self.update()
        except Exception as e:
            logger.warning(f"Cannot load after preview: {e}")

    def set_placeholder(self, text: str):
        self._placeholder_text = text
        self.update()

    def clear(self):
        self._before_pixmap = None
        self._after_pixmap = None
        self.update()

    # ------------------------------------------------------------------ #
    # Rendering
    # ------------------------------------------------------------------ #

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        w, h = self.width(), self.height()

        # Background
        painter.fillRect(0, 0, w, h, QColor("#0D1117"))

        if self._before_pixmap is None:
            self._draw_placeholder(painter, w, h)
            return

        # Scale pixmap to fit while maintaining aspect ratio
        scaled_before = self._before_pixmap.scaled(
            w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        img_w, img_h = scaled_before.width(), scaled_before.height()
        x_off = (w - img_w) // 2
        y_off = (h - img_h) // 2

        divider_px = int(self._divider_x * img_w)

        # ── Before (left) ──────────────────────────────────────────── #
        if self._after_pixmap:
            painter.drawPixmap(
                x_off, y_off,
                scaled_before,
                0, 0, divider_px, img_h,
            )
        else:
            painter.drawPixmap(x_off, y_off, scaled_before)

        # ── After (right) ─────────────────────────────────────────── #
        if self._after_pixmap:
            scaled_after = self._after_pixmap.scaled(
                w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            painter.drawPixmap(
                x_off + divider_px, y_off,
                scaled_after,
                divider_px, 0, img_w - divider_px, img_h,
            )

            # ── Divider line ────────────────────────────────────────── #
            div_screen_x = x_off + divider_px
            pen = QPen(QColor("#58A6FF"), 2)
            painter.setPen(pen)
            painter.drawLine(div_screen_x, y_off, div_screen_x, y_off + img_h)

            # Divider handle circle
            cy = y_off + img_h // 2
            painter.setBrush(QColor("#58A6FF"))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPoint(div_screen_x, cy), 10, 10)

            # Labels
            self._draw_label(painter, "BEFORE", x_off + 8, y_off + 8, left=True)
            self._draw_label(painter, "AFTER",  x_off + img_w - 8, y_off + 8, left=False)

    def _draw_placeholder(self, painter: QPainter, w: int, h: int):
        painter.setPen(QColor("#21262D"))
        for x in range(0, w, 30):
            for y in range(0, h, 30):
                painter.drawPoint(x, y)

        painter.setPen(QColor("#30363D"))
        font = QFont("Ubuntu", 16)
        font.setWeight(QFont.Light)
        painter.setFont(font)
        painter.drawText(
            QRect(0, 0, w, h),
            Qt.AlignCenter,
            "🖼  " + self._placeholder_text,
        )

    def _draw_label(
        self, painter: QPainter, text: str, x: int, y: int, left: bool
    ):
        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 140))
        fm = painter.fontMetrics()
        tw = fm.horizontalAdvance(text) + 12
        th = fm.height() + 6
        lx = x if left else x - tw
        painter.drawRoundedRect(lx, y, tw, th, 4, 4)
        painter.setPen(QColor("#E8EAED"))
        font = QFont("Ubuntu", 10, QFont.Bold)
        painter.setFont(font)
        painter.drawText(QRect(lx, y, tw, th), Qt.AlignCenter, text)
        painter.restore()

    # ------------------------------------------------------------------ #
    # Mouse events for divider drag
    # ------------------------------------------------------------------ #

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and self._after_pixmap:
            self._dragging = True
            self._update_divider(event.x())

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging and self._after_pixmap:
            self._update_divider(event.x())
        elif self._after_pixmap:
            # Show resize cursor near divider
            img_w = self._get_img_width()
            x_off = (self.width() - img_w) // 2
            div_x = x_off + int(self._divider_x * img_w)
            if abs(event.x() - div_x) < 15:
                self.setCursor(Qt.SplitHCursor)
            else:
                self.setCursor(Qt.ArrowCursor)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._dragging = False

    def _update_divider(self, mouse_x: int):
        if self._before_pixmap is None:
            return
        img_w = self._get_img_width()
        x_off = (self.width() - img_w) // 2
        rel = (mouse_x - x_off) / img_w
        self._divider_x = max(0.02, min(0.98, rel))
        self.update()

    def _get_img_width(self) -> int:
        if self._before_pixmap is None:
            return self.width()
        scaled = self._before_pixmap.scaled(
            self.width(), self.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation,
        )
        return scaled.width()
