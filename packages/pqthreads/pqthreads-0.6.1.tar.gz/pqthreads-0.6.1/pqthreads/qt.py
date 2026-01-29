""" Backwards compatible PySide imports """

# pylint: disable=unused-import
try:
    import PySide6 as PySide
    from PySide6 import QtCore, QtWidgets
except ImportError:
    import PySide2 as PySide
    from PySide2 import QtCore, QtWidgets
# pylint: enable=unused-import
