# Copyright (c) 2026 Jifeng Wu
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
import sys
import traceback

from detect_qt_binding import detect_qt_binding, QtBindings

QT_BINDING = detect_qt_binding()
if QT_BINDING == QtBindings.PyQt6:
    from PyQt6.QtWidgets import QMessageBox

    Critical = QMessageBox.Icon.Critical


    def exec_(msg_box):
        # type: (QMessageBox) -> int
        return getattr(msg_box, 'exec')()
elif QT_BINDING == QtBindings.PySide6:
    from PySide6.QtWidgets import QMessageBox

    Critical = QMessageBox.Icon.Critical


    def exec_(msg_box):
        # type: (QMessageBox) -> int
        return getattr(msg_box, 'exec')()
elif QT_BINDING == QtBindings.PyQt5:
    from PyQt5.QtWidgets import QMessageBox

    Critical = QMessageBox.Critical


    def exec_(msg_box):
        # type: (QMessageBox) -> int
        return msg_box.exec_()
elif QT_BINDING == QtBindings.PySide2:
    from PySide2.QtWidgets import QMessageBox

    Critical = QMessageBox.Icon.Critical


    def exec_(msg_box):
        # type: (QMessageBox) -> int
        return msg_box.exec_()
elif QT_BINDING == QtBindings.PyQt4:
    from PyQt4.QtGui import QMessageBox

    Critical = QMessageBox.Critical


    def exec_(msg_box):
        # type: (QMessageBox) -> int
        return msg_box.exec_()
elif QT_BINDING == QtBindings.PySide:
    from PySide.QtGui import QMessageBox

    Critical = QMessageBox.Icon.Critical


    def exec_(msg_box):
        # type: (QMessageBox) -> int
        return msg_box.exec_()
else:
    raise ImportError(
        'We require one of PyQt6, PySide6, PyQt5, PySide2, PyQt4, or PySide. '
        'None of these packages were detected in your Python environment.'
    )


def pyqt_current_exception_message_box(parent):
    # type: (...) -> int
    # Get the exception type, value, and traceback object
    exc_type, exc_value, exc_traceback = sys.exc_info()
    tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))

    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle(exc_type.__name__)
    msg_box.setText(str(exc_value))
    msg_box.setDetailedText(tb_str)

    return exec_(msg_box)
