""" Figure window module """

import sys
from pqthreads.qt import QtCore, QtWidgets


class FigureWindowException(Exception):
    """ Exception for FigureWindow """


class FigureWindow(QtWidgets.QMainWindow):
    """ Figure window """

    def __init__(self, index, **kwargs):
        super().__init__(parent=kwargs.pop('parent', None))
        self.index = index
        self.resize(kwargs.get('width', 600), kwargs.get('height', 500))
        self.change_title(title=kwargs.get('title', 'Untitled'))
        self.show()

    def change_title(self, title='Untitled'):
        """ Change the window title """
        title = f'Figure {self.index+1}: {title}'
        self.setWindowTitle(title)
        return title

    @property
    def title(self):
        """ Returns the window title """
        return self.windowTitle()

    @title.setter
    def title(self, title):
        """ Sets the window title """
        self.change_title(title)

    def raise_window(self):
        """ Raises the current window to top """
        if sys.platform == 'win32':
            state = self.windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive
            self.setWindowState(state)
            self.activateWindow()
        else:
            self.raise_()

    def raise_exception(self):
        """ Method to raise custom exception for testing purposes """
        raise FigureWindowException('Custom exception')

    def delete(self):
        """ Closes the window """
        self.close()


class GraphWindow(QtWidgets.QMainWindow):
    """ Graph window """
    def __init__(self, index, **kwargs):
        super().__init__(parent=kwargs.pop('parent', None))
        self.index = index
        self.show()

    def test_method(self):
        """ Method solely for testing purposes """
        return 'Test successful'

    def delete(self):
        """ Closes the window """
        self.close()
