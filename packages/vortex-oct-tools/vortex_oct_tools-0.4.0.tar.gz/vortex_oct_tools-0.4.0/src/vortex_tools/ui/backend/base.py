from typing import List, Iterable, Optional, Tuple
from functools import reduce
from time import time
from enum import Enum

from matplotlib import cm

import numpy as np

from qtpy.QtCore import QPointF
from qtpy.QtGui import QPainter, QFontMetricsF, QPen, QColor, QFont

__all__ = ['BaseImageWidget']

class BaseImageWidget:
    class Anchor(Enum):
        TopLeft = 0
        TopRight = 1
        BottomRight = 2
        BottomLeft = 3

    def __init__(self, *args, **kwargs):
        '''
        cmap `Callable`: `cm.inferno`
            Callable object that maps [0, 1] to a [0, 255] grayscale, grayscale-alpha, RGB, or RGBA value
        range `Iterable[float]`: [0, 1]
            Two-element list of minimum and maximum color map values.
        aspect `float`: 1
            Target ratio of width to height.
        data `numpy.ndarray`: `None`
            Initial Numpy array to display.
        debug `bool`: `False`
            Show sizes and frame rates on the display.
        '''

        self._colormap: np.ndarray[float] = kwargs.pop('cmap', cm.inferno)
        self._range: Iterable[int] = kwargs.pop('range', [0, 1])
        self._aspect: float = kwargs.pop('aspect', 1)

        self.__data: np.ndarray = kwargs.pop('data', None)

        self._overlay_font = kwargs.pop('overlay_font', None)
        if self._overlay_font is None:
            self._overlay_font = QFont("Consolas")
            self._overlay_font.setStyleHint(QFont.Monospace)

        self._debug = kwargs.pop('debug', False)
        self.__frame_times = []

        super().__init__(*args, **kwargs)

    @property
    def data(self) -> np.ndarray:
        return self.__data
    @data.setter
    def data(self, value: np.ndarray):
        self.__data = value
        self.invalidate()

    @property
    def colormap(self) -> np.ndarray:
        return self._colormap
    @colormap.setter
    def colormap(self, value: np.ndarray):
        self._colormap = value
        self.invalidate()

    @property
    def range(self) -> np.ndarray:
        return self._range
    @range.setter
    def range(self, value: np.ndarray):
        self._range = value
        self.invalidate()

    def invalidate(self):
        raise NotImplementedError

    def _draw_stats(self, painter: QPainter) -> None:
        # calculate frame rate
        self.__frame_times.append(time())

        if len(self.__frame_times) < 2:
            fps = 0
        else:
            divisor = self.__frame_times[-1] - self.__frame_times[0]
            if divisor == 0:
                fps = 0
            else:
                fps = (len(self.__frame_times) - 1) / divisor
        while self.__frame_times[-1] - self.__frame_times[0] > 1:
            del self.__frame_times[0]

        pixel_scale = self.devicePixelRatio()

        lines = [f'{fps:.1f} fps']
        if self.data is None:
            lines += ['Data: None']
        else:
            lines += ['Data: ' + ' x '.join([str(x) for x in self.data.shape])]
        lines += [f'Window: {pixel_scale*self.width():.0f} x {pixel_scale*self.height():.0f}']
        lines += self._make_additional_stats()

        self._draw_multiline_text_overlay(painter, QPointF(0, 0), lines)

    def _draw_multiline_text_overlay(self, painter: QPainter, position: QPointF, lines: List[str], padding: Optional[Tuple[int, int, int, int]]=None, anchor: Anchor=Anchor.TopLeft) -> None:
        if padding is None:
            padding = [3, 4, 0, 2]

        # layout options
        painter.setFont(self._overlay_font)
        metrics = QFontMetricsF(self._overlay_font)

        offsets = [QPointF(padding[0], padding[2] + (i + 1) * metrics.height()) for i in range(len(lines))]
        bounds =  [metrics.boundingRect(line).translated(offset) for (offset, line) in zip(offsets, lines)]

        max_bounds = reduce(lambda a, b: a.united(b), bounds).adjusted(0, 0, padding[1], padding[3])
        max_bounds.setTopLeft(QPointF(0, 0))

        if anchor == BaseImageWidget.Anchor.TopLeft:
            max_bounds.moveTopLeft(position)
        elif anchor == BaseImageWidget.Anchor.TopRight:
            max_bounds.moveTopRight(position)
        elif anchor == BaseImageWidget.Anchor.BottomLeft:
            max_bounds.moveBottomLeft(position)
        elif anchor == BaseImageWidget.Anchor.BottomRight:
            max_bounds.moveBottomRight(position)

        # draw the context
        painter.setPen(QPen(QColor(255, 255, 255)))

        painter.fillRect(max_bounds, QColor(0, 0, 0, 128))
        for (offset, line) in zip(offsets, lines):
            painter.drawText(max_bounds.topLeft() + offset, line)

    def _make_additional_stats(self) -> List[str]:
        return []
