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


"""File selector for the GUI."""


__author__ = 'Jessie Blue Cassell'


__all__ = [
            'FileSelector',
          ]


import os
import errno
from collections import deque

from PyQt6.QtCore import (
                          Qt,
                          QDir,
                          pyqtSignal,
                          QModelIndex,
                         )
from PyQt6.QtWidgets import (
                             QWidget,
                             QVBoxLayout,
                             QHBoxLayout,
                             QLineEdit,
                             QTreeView,
                             QAbstractItemView,
                             QCompleter,
                             QToolButton,
                            )
from PyQt6.QtGui import (
                         QIcon,
                         QFileSystemModel,
                         QKeySequence,
                        )

import audio_tuner_gui.common as gcom


class _PathHistory(deque):
    def __init__(self, path):
        super().__init__()
        self.n = 0
        self.append(self._norm(path))

    def _norm(self, path):
        return QDir.fromNativeSeparators(path).rstrip('/') + '/'

    def cd(self, path):
        path = self._norm(path)
        while not self.at_end():
            self.pop()
        if path != self[-1]:
            self.append(path)
            self.n += 1
        return path

    def at_end(self):
        return len(self) == self.n + 1

    def at_beginning(self):
        return self.n == 0

    def current(self):
        return self[self.n]

    def next(self, native=False):
        ret = self[self.n+1]
        if native:
            ret = QDir.toNativeSeparators(ret)
        return ret

    def previous(self, native=False):
        ret = self[self.n-1]
        if native:
            ret = QDir.toNativeSeparators(ret)
        return ret

    def forward(self):
        if not self.at_end():
            self.n += 1
        else:
            raise IndexError

    def back(self):
        if not self.at_beginning():
            self.n -= 1
        else:
            raise IndexError


class _PathEdit(QLineEdit):
    def setText(self, text):
        if QDir(text).exists():
            text = text.rstrip('/\\') + '/'
        text = QDir.toNativeSeparators(text)
        super().setText(text)


class _FileView(QTreeView):
    EnterKeyPress = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.setExpandsOnDoubleClick(False)
        self.setAllColumnsShowFocus(True)
        self.setItemsExpandable(False)
        self.setRootIsDecorated(False)
        self.setSelectionMode(
                        QAbstractItemView.SelectionMode.ExtendedSelection)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return:
            self.EnterKeyPress.emit()
        else:
            super().keyPressEvent(event)


class FileSelector(QWidget):
    """A widget for selecting files to analyze.  Inherits from QWidget.

    Parameters
    ----------
    option_panel : audio_tuner_gui.option_panel.OptionPanel
        The option panel widget to get analysis options from.
    """

    SelectForAnalysis = pyqtSignal(str, gcom.Options)
    """Signal emitted when a file is selected.

    Parameters
    ----------
    audio_tuner_gui.common.Options
        The options to use when the file is analyzed.
    """

    UpdateStatusbar = pyqtSignal(str)
    """Signal emitted to request a string be displayed on the status bar.

    Parameters
    ----------
    str
        The string.
    """


    def __init__(self, option_panel):
        super().__init__()

        self.option_panel = option_panel

        vbox = QVBoxLayout(self)
        vbox.setSpacing(5)
        vbox.setContentsMargins(3, 3, 3, 3)

        self.path_history = _PathHistory(QDir.currentPath())

        self._init_file_view()
        self._init_control_panel()
        self._cd(self.path_history.current())

        vbox.addWidget(self.panel)
        vbox.addWidget(self.view)

    def _init_file_view(self):
        model = QFileSystemModel(self)

        self.original_filter = model.filter()
        self.showhidden_filter = self.original_filter | QDir.Filter.Hidden

        view = _FileView()
        view.setModel(model)
        view.setColumnWidth(0, 250)
        view.header().moveSection(2, 1)
        view.setSortingEnabled(True)
        view.sortByColumn(0, Qt.SortOrder.AscendingOrder)

        view.doubleClicked.connect(self._file_selector_doubleclick)
        view.EnterKeyPress.connect(self._file_selector_enter)

        self.model = model
        self.view = view

    def _set_show_hidden(self, checked):
        if checked:
            self.model.setFilter(self.showhidden_filter)
        else:
            self.model.setFilter(self.original_filter)

    def _init_control_panel(self):
        panel = QWidget()
        hbox = QHBoxLayout(panel)
        hbox.setContentsMargins(0, 0, 0, 0)

        back_act = gcom.SplitAction('&Back', self)
        back_act.setIcon(QIcon.fromTheme(gcom.ICON_BACK))
        back_act.setShortcut(QKeySequence('Alt+Left'))
        back_act.triggered_connect(self._go_back)

        back_button = QToolButton()
        back_button.setDefaultAction(back_act.button())
        hbox.addWidget(back_button)

        forward_act = gcom.SplitAction('&Forward', self)
        forward_act.setIcon(QIcon.fromTheme(gcom.ICON_FORWARD))
        forward_act.setShortcut(QKeySequence('Alt+Right'))
        forward_act.triggered_connect(self._go_forward)

        forward_button = QToolButton()
        forward_button.setDefaultAction(forward_act.button())
        hbox.addWidget(forward_button)

        up_act = gcom.SplitAction('&Up', self)
        up_act.setIcon(QIcon.fromTheme(gcom.ICON_UP))
        up_act.setShortcut(QKeySequence('Alt+Up'))
        up_act.triggered_connect(self._updir)

        up_button = QToolButton()
        up_button.setDefaultAction(up_act.button())
        hbox.addWidget(up_button)

        home_act = gcom.SplitAction('&Home', self)
        home_act.setIcon(QIcon.fromTheme(gcom.ICON_HOME))
        home_act.setShortcut(QKeySequence('Alt+Home'))
        home_act.setStatusTip('Go to home directory')
        home_act.triggered_connect(self._go_home)

        home_button = QToolButton()
        home_button.setDefaultAction(home_act.button())
        hbox.addWidget(home_button)

        completer = QCompleter(self.model, self)

        pathedit = _PathEdit()
        pathedit.setCompleter(completer)
        hbox.addWidget(pathedit)
        pathedit.returnPressed.connect(self._pathedit_enter,
                                       Qt.ConnectionType.QueuedConnection)

        self.pathedit = pathedit
        self.panel = panel
        self.back_button = back_button
        self.forward_button = forward_button
        self.up_button = up_button
        self.back_act = back_act
        self.forward_act = forward_act
        self.up_act = up_act
        self.home_act = home_act

    def _pathedit_enter(self):
        try:
            self._cd(QDir.fromNativeSeparators(self.pathedit.text()))
        except NotADirectoryError:
            path = self.pathedit.text()
            options = self.option_panel.get_options()
            if options is None:
                self.option_panel.ensure_visible()
            else:
                self.SelectForAnalysis.emit(path, options)
            self._select_filename()

    def handle_command_line_arg(self, arg):
        """If `arg` is a file, act like it's been selected and send it
        out for analysis.  If `arg` is a directory, change to that
        directory.

        Note that this does the same thing as the `handle_drop` method.
        They're separate methods to leave open the possibility of
        different behavior for command line arguments and drops in the
        future.

        Parameters
        ----------
        arg : str
            File or directory path.
        """

        try:
            self._cd(QDir.fromNativeSeparators(arg))
        except NotADirectoryError:
            options = self.option_panel.get_options()
            if options is None:
                self.option_panel.ensure_visible()
            else:
                self.SelectForAnalysis.emit(arg, options)

    def handle_drop(self, path):
        """If `path` is a file, act like it's been selected and send it
        out for analysis.  If `path` is a directory, change to that
        directory.

        Note that this does the same thing as the
        `handle_command_line_arg` method.  They're separate methods to
        leave open the possibility of different behavior for command
        line arguments and drops in the future.

        Parameters
        ----------
        path : str
            File or directory path.
        """
        self.handle_command_line_arg(path)

    def _select_filename(self):
        path = self.pathedit.text()
        if not QDir(path).exists():
            length = len(os.path.basename(path))
            pos = len(os.path.dirname(path)) + 1
            self.pathedit.setSelection(pos, length)


    def _cd(self, dest=None, hist='cd'):
        if hist == 'previous':
            dest = self.path_history.previous()
        elif hist == 'next':
            dest = self.path_history.next()
        if isinstance(dest, QModelIndex):
            path = self.model.filePath(dest)
            index = dest
        elif isinstance(dest, str):
            if not QDir(dest).exists():
                raise NotADirectoryError(errno.ENOTDIR,
                                         os.strerror(errno.ENOTDIR),
                                         dest)
            path = dest
            index = self.model.index(dest)
        self.model.setRootPath(path)
        self.view.setRootIndex(index)
        self.pathedit.setText(QDir(path).absolutePath())
        if hist == 'previous':
            self.path_history.back()
        elif hist == 'next':
            self.path_history.forward()
        elif hist == 'cd':
            self.path_history.cd(path)
        if self.path_history.at_beginning():
            self.back_act.setEnabled(False)
            self.back_button.setAutoRaise(True)
            status = 'No previous directory'
            self.back_act.setStatusTip(status)
            if self.back_button.underMouse():
                self.UpdateStatusbar.emit(status)
        else:
            self.back_act.setEnabled(True)
            self.back_button.setAutoRaise(False)
            status = ('Go to previous directory: '
                      + self.path_history.previous(native=True))
            self.back_act.setStatusTip(status)
            if self.back_button.underMouse():
                self.UpdateStatusbar.emit(status)
        if self.path_history.at_end():
            self.forward_act.setEnabled(False)
            self.forward_button.setAutoRaise(True)
            status = 'No next directory'
            self.forward_act.setStatusTip(status)
            if self.forward_button.underMouse():
                self.UpdateStatusbar.emit(status)
        else:
            self.forward_act.setEnabled(True)
            self.forward_button.setAutoRaise(False)
            status = ('Go to next directory: '
                      + self.path_history.next(native=True))
            self.forward_act.setStatusTip(status)
            if self.forward_button.underMouse():
                self.UpdateStatusbar.emit(status)
        if QDir(path).isRoot():
            self.up_act.setEnabled(False)
            self.up_button.setAutoRaise(True)
            status = 'No parent directory'
            self.up_act.setStatusTip(status)
            if self.up_button.underMouse():
                self.UpdateStatusbar.emit(status)
        else:
            self.up_act.setEnabled(True)
            self.up_button.setAutoRaise(False)
            status = 'Go to parent directory'
            self.up_act.setStatusTip(status)
            if self.up_button.underMouse():
                self.UpdateStatusbar.emit(status)

    def _file_selector_doubleclick(self, index):
        if self.model.isDir(index):
            self._cd(index)
        else:
            self._file_selector_enter()

    def _file_selector_enter(self):
        selected = [x for x in self.view.selectedIndexes() if x.column() == 0]
        if len(selected) == 1 and self.model.isDir(selected[0]):
            self._cd(selected[0])
        else:
            options = self.option_panel.get_options()
            if options is None:
                self.option_panel.ensure_visible()
            else:
                for index in selected:
                    self.SelectForAnalysis.emit(self.model.filePath(index),
                                                options)

    def _updir(self):
        directory = self.model.rootDirectory()
        if directory.cdUp():
            newpath = directory.absolutePath()
            self._cd(newpath)

    def _go_home(self):
        self._cd(QDir.homePath())

    def _go_back(self):
        self._cd(hist='previous')

    def _go_forward(self):
        self._cd(hist='next')
