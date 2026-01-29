""" Utility module """

from pqthreads.qt import PySide
from pqthreads.qt import QtCore


def compat_exec(obj):
    """ Compatibility exec function """
    if PySide.__version_info__[0] < 6:
        obj.exec_()
    else:
        obj.exec()


class SignalWaiter(QtCore.QObject):
    """ Context manager that blocks loop until signal emitted, or timeout (ms)
    elapses. """
    def __init__(self, signal, error_signal=None, timeout=1000, parent=None):
        super().__init__(parent=parent)
        self.signal = signal
        self.error_signal = error_signal
        self.timeout = timeout
        self.loop = None

    def __enter__(self):
        self.loop = QtCore.QEventLoop(parent=self)
        self.signal.connect(self.loop.quit)
        if self.error_signal is not None:
            self.error_signal.connect(self.loop.quit)

    def __exit__(self, exc_type, exc_value, exc_tb):
        if self.timeout is not None:
            QtCore.QTimer.singleShot(self.timeout, self.loop.quit)
        compat_exec(self.loop)
