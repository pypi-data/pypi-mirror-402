from matplotlib.axes import Axes
from matplotlib.image import AxesImage
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvas

from qtpy.QtGui import QPainter, QPaintEvent

from .base import BaseImageWidget

__all__ = ['NumpyImageWidget']

class MatplotlibImageWidget(BaseImageWidget, FigureCanvas):
    def __init__(self, *args, **kwargs):
        '''
        Display a Numpy array using Matplotlib.

        Set the displayed array using the `data` property.
        The array may be edited in-place as long as `invalidate()` is called afterwards.

        figsize `Tuple[float]`: (6, 4)
            Size of figure for standalone windows.
        '''

        figsize = kwargs.pop('figsize', (6.5, 5))

        self._axes: Axes = None
        self.__axes_image: AxesImage = None
        self.__invalidated: bool = True

        super().__init__(Figure(figsize=figsize), *args, **kwargs)

    def paintEvent(self, e: QPaintEvent) -> None:
        # NOTE: redraw only when invalidated to avoid continuous drawing
        if self.axes_image and self.__invalidated:
            self.draw()
            self.__invalidated = False

        super().paintEvent(e)

        if self._debug:
            painter = QPainter(self)
            self._draw_stats(painter)
            painter.end()

    def invalidate(self) -> None:
        '''
        Request a redraw to update the image.
        '''
        if self.axes_image:
            self.axes_image.set_array(self.data)
            # NOTE: do not draw here because this is likely called from a Vortex thread
            self.__invalidated = True
            self.update()

    @property
    def axes_image(self) -> AxesImage:
        if not self.__axes_image or (self.data is not None and self.data.shape != self.__axes_image.get_array().shape):
            self._make_and_cache_axes()

        # get from cache
        return self.__axes_image

    @property
    def axes(self) -> Axes:
        return self._axes

    def _make_and_cache_axes(self) -> None:
        if self.data is None:
            return

        if self.__axes_image is not None:
            # destroy the old axes
            self.figure.clear()

        # generate the plot
        self._axes = self.figure.subplots()
        self.__axes_image = self._axes.imshow(
            self.data,
            interpolation='nearest',
            vmin=self._range[0], vmax=self._range[1],
            aspect=self._aspect,
            cmap=self._colormap
        )

        self.figure.tight_layout()
