import sys
import signal

from qtpy.QtCore import Qt, QCoreApplication, QTimer
from qtpy.QtGui import QGuiApplication
from qtpy.QtWidgets import QApplication

import numpy as np

from .qt import NumpyImageWidget, NumpyImageViewer
from .mpl import MatplotlibImageWidget

def run() -> None:
    try:
        QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
        QGuiApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    except AttributeError:
        pass

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    # cause KeyboardInterrupt to exit the Qt application
    signal.signal(signal.SIGINT, lambda sig, frame: app.exit())

    # regularly re-enter Python so the signal handler runs
    def keepalive(msec):
        QTimer.singleShot(msec, lambda: keepalive(msec))
    keepalive(10)

    (x, y) = np.meshgrid(*[np.linspace(0, 1, n) for n in [10, 20]])
    data = x + y

    mplw = MatplotlibImageWidget(data=data, debug=True)
    npw = NumpyImageWidget(data=data, debug=True)
    npv = NumpyImageViewer(data=data, debug=True)

    for w in [mplw, npw, npv]:
        w.setWindowTitle(type(w).__name__)
        w.setStyleSheet('background: magenta;')
        w.show()

    app.exec()

if __name__ == '__main__':
    run()
