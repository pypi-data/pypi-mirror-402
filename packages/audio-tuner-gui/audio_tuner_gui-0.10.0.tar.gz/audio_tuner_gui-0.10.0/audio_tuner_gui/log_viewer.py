#!/usr/bin/env python3
#
# This file is part of Audio Tuner.
#
# Copyright 2025, 2026 Jessie Blue Cassell <bluesloth600@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


"""Message log for the GUI."""


__author__ = 'Jessie Blue Cassell'


__all__ = [
            'LOG_LEVEL_ERROR',
            'LOG_LEVEL_WARNING',
            'LOG_LEVEL_NORMAL',
            'LogViewer',
          ]


from PyQt6.QtCore import (
                          Qt,
                         )
from PyQt6.QtWidgets import (
                             QWidget,
                             QPushButton,
                             QMessageBox,
                             QVBoxLayout,
                             QTextEdit,
                            )
from PyQt6.QtGui import (
                         QIcon,
                         QAction,
                         QColor,
                         QFont,
                         QTextCursor,
                         QPalette,
                        )

import audio_tuner_gui.common as gcom


_CLEAR_CONFIRMATION_MESSAGE = ('This will clear the entire message log.'
                              '\nAre you sure?')

# Severity levels
LOG_LEVEL_ERROR = 3
LOG_LEVEL_WARNING = 2
LOG_LEVEL_NORMAL = 1


class _LogText(QTextEdit):
    def __init__(self, parent):
        super().__init__(parent)
        self.clear_act = QAction('Clear log', self)
        self.clear_act.setIcon(QIcon.fromTheme(gcom.ICON_CLEAR))
        self.clear_act.triggered.connect(self.clear)

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        if self.document().isEmpty():
            self.clear_act.setEnabled(False)
        else:
            self.clear_act.setEnabled(True)
        menu.addAction(self.clear_act)
        menu.exec(event.globalPos())

    def clear(self):
        reply = QMessageBox.question(
                                self,
                                'Clear message log',
                                _CLEAR_CONFIRMATION_MESSAGE,
                                QMessageBox.StandardButton.Yes
                                | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            super().clear()


class LogViewer(QWidget):
    """A window for storing and viewing log messages.  Inherits from
    QWidget.

    Parameters
    ----------
    parent
        The parent widget.
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowFlag(Qt.WindowType.Window)
        self.setWindowTitle('Message log')

        palette = QPalette()
        self.normal_color = palette.windowText().color()
        self.error_color = QColor(255, 0, 0)

        self.vbox = QVBoxLayout(self)

        self.text = _LogText(self)
        self.text.setReadOnly(True)
        self.text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.vbox.addWidget(self.text)

        self.button = QPushButton('Close')
        self.button.clicked.connect(self.close)
        self.vbox.addWidget(self.button)

        self.resize(600, 400)

    def add_message(self, message, level):
        """Add a message to the log.

        Parameters
        ----------
        message : str
            The message.
        level : int
            The severity level (LOG_LEVEL_ERROR, LOG_LEVEL_WARNING or
            LOG_LEVEL_NORMAL).
        """

        self.text.moveCursor(QTextCursor.MoveOperation.End)
        if level == LOG_LEVEL_ERROR:
            self.text.setTextColor(self.error_color)
        else:
            self.text.setTextColor(self.normal_color)
        if level >= LOG_LEVEL_WARNING:
            self.text.setFontWeight(QFont.Weight.Bold)
        else:
            self.text.setFontWeight(QFont.Weight.Normal)
        self.text.insertPlainText(message)

    def close(self):
        """Hide the window."""

        self.hide()
