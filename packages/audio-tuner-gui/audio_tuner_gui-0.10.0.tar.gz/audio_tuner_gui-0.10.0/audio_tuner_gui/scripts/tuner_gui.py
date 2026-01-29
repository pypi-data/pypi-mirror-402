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


"""The GUI frontend for Audio Tuner."""


__author__ = 'Jessie Blue Cassell'


import sys
import os
from collections import deque

from PyQt6.QtCore import (
                          Qt,
                          pyqtSignal,
                         )
from PyQt6.QtWidgets import (
                             QApplication,
                             QWidget,
                             QPushButton,
                             QMessageBox,
                             QMainWindow,
                             QVBoxLayout,
                             QHBoxLayout,
                             QSplitter,
                             QToolButton,
                             QSizePolicy,
                             QProgressBar,
                             QLabel,
                             QStackedWidget,
                             QLCDNumber,
                             QSlider,
                            )
from PyQt6.QtGui import (
                         QIcon,
                         QAction,
                         QKeySequence,
                         QFont,
                         QPalette,
                        )
from PyQt6.QtSvgWidgets import QSvgWidget

import audio_tuner.error_handling as eh
import audio_tuner.common as com
import audio_tuner.argument_parser as ap

import audio_tuner_gui.common as gcom
import audio_tuner_gui.file_selector as fs
import audio_tuner_gui.option_panel as op
import audio_tuner_gui.analysis as ga
import audio_tuner_gui.log_viewer as lv
import audio_tuner_gui.display as disp
import audio_tuner_gui.player as pl
import audio_tuner_gui.export as ex

from audio_tuner_gui import VERSION


APP_TITLE = 'Audio Tuner'
QUIT_CONFIRMATION_MESSAGE = f'Quit {APP_TITLE}?'
INIT_STATUS_MESSAGE = f'Welcome to {APP_TITLE}'

DESCRIPTION = (f'This is the GUI for {APP_TITLE}.  Command line arguments'
                ' can be used to run with different default settings.'
                '  Arguments not listed here will be passed to the'
                ' Qt GUI toolkit.')

ABOUT_TEXT = """
Copyright \N{COPYRIGHT SIGN} 2025, 2026 Jessie Blue Cassell.
License GPLv3+: GNU GPL version 3 or later <https://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.

Folder, Options, and Process Stop icons from the
Adwaita icon theme, by the GNOME Project.
<https://download.gnome.org/sources/adwaita-icon-theme/>
Copyright \N{COPYRIGHT SIGN} 2002-2014
License: CC-BY-SA-3.0 or LGPL-3
<https://creativecommons.org/licenses/by-sa/3.0/>
<https://gnu.org/licenses/lgpl-3.0.html>
"""

VERSION_STRING = f'tuner-gui ({APP_TITLE}) {VERSION}\n{ABOUT_TEXT}'

DEBUG_BUTTON = False

class _AboutWindow(QWidget):
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowFlag(Qt.WindowType.Window)
        self.setWindowTitle('About')

        self.vbox = QVBoxLayout(self)

        self.text = QLabel(ABOUT_TEXT, self)
        self.text.setCursor(Qt.CursorShape.IBeamCursor)
        self.text.setTextInteractionFlags(
                                Qt.TextInteractionFlag.TextSelectableByMouse)

        self.config_text = QLabel('Config file path:\n' + ap.CONFIG_PATH, self)
        self.config_text.setCursor(Qt.CursorShape.IBeamCursor)
        self.config_text.setTextInteractionFlags(
                                Qt.TextInteractionFlag.TextSelectableByMouse)

        th = self.text.fontMetrics().height()
        pal = QApplication.palette()
        text_color = pal.color(QPalette.ColorRole.WindowText)
        bg_color = pal.color(QPalette.ColorRole.Window)
        lightmode = text_color.lightness() < bg_color.lightness()

        if lightmode:
            self.logo = QSvgWidget(gcom.LOGO_DARK)
        else:
            self.logo = QSvgWidget(gcom.LOGO_LIGHT)
        self.logo.renderer().setAspectRatioMode(
                                Qt.AspectRatioMode.KeepAspectRatio)
        self.logo.setFixedSize(int(35 * th), int(7 * th))
        self.vbox.addWidget(self.logo)

        self.ver = QLabel(f'Version {VERSION}', self)
        self.ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(16)
        self.ver.setFont(font)
        self.ver.setCursor(Qt.CursorShape.IBeamCursor)
        self.ver.setTextInteractionFlags(
                                Qt.TextInteractionFlag.TextSelectableByMouse)
        self.vbox.addWidget(self.ver)

        self.vbox.addWidget(self.text)

        self.vbox.addWidget(self.config_text)

        self.hboxwidget = QWidget()
        self.hbox = QHBoxLayout(self.hboxwidget)
        self.hbox.setAlignment(Qt.AlignmentFlag.AlignLeft)

        if lightmode:
            self.gpl = QSvgWidget(gcom.GPL_RED)
        else:
            self.gpl = QSvgWidget(gcom.GPL_WHITE)
        self.gpl.renderer().setAspectRatioMode(
                                Qt.AspectRatioMode.KeepAspectRatio)
        self.gpl.setFixedSize(int(7 * th), int(4 * th))
        self.hbox.addWidget(self.gpl)

        if lightmode:
            self.brainmade = QSvgWidget(gcom.BRAINMADE_BLACK)
        else:
            self.brainmade = QSvgWidget(gcom.BRAINMADE_WHITE)
        self.brainmade.renderer().setAspectRatioMode(
                                Qt.AspectRatioMode.KeepAspectRatio)
        self.brainmade.setFixedSize(int(5 * th), int(1.5 * th))
        self.hbox.addWidget(self.brainmade)

        self.vbox.addWidget(self.hboxwidget)

        self.button = QPushButton('Close')
        self.button.clicked.connect(self.close)
        self.vbox.addWidget(self.button)

    def close(self):
        """Close the window."""
        self.hide()


class _Slider(QSlider):
    MouseReleased = pyqtSignal()
    MousePressed = pyqtSignal()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.MousePressed.emit()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.MouseReleased.emit()


class _MainUI(QMainWindow):
    def __init__(self, args, message_queue):
        super().__init__()

        self.args = args
        self.message_queue = message_queue
        self._slider_update_enabled = True
        self.duration = None
        self._exporting_in_progress = False
        self._currently_playing_start = None
        self._currently_playing_end = None

        self.exit_act = QAction(QIcon.fromTheme(gcom.ICON_EXIT),
                                'Exit',
                                self)
        self.exit_act.setShortcut(QKeySequence('Ctrl+Q'))
        self.exit_act.setStatusTip('Exit application')
        self.exit_act.triggered.connect(QApplication.instance().quit)

        self.showhidden_act = QAction('Show &hidden files', self)
        self.showhidden_act.setCheckable(True)
        self.showhidden_act.setShortcut(QKeySequence('Ctrl+H'))

        self.play_start_end_act = QAction(
                f'Play between {gcom.OPTION_START} and {gcom.OPTION_END}')
        self.play_start_end_act.setCheckable(True)
        self.play_start_end_act.toggled.connect(self._play_start_end_toggled)

        self.toggle_options_panel_act = QAction('Show &options panel', self)
        self.toggle_options_panel_act.setCheckable(True)
        self.toggle_options_panel_act.setChecked(False)
        self.toggle_options_panel_act.setShortcut('F2')
        self.toggle_options_panel_act.setStatusTip(
                            'Switch between file selector and options panel')
        self.toggle_options_panel_act.triggered.connect(
                                                self._toggle_options_panel)

        self.toggle_toggle_options_panel_act = QAction(self)
        self.toggle_toggle_options_panel_act.setIcon(QIcon(gcom.ICON_OPTIONS))
        self.toggle_toggle_options_panel_act.setStatusTip(
                            'Switch between file selector and options panel')
        self.toggle_toggle_options_panel_act.triggered.connect(
                                            self._toggle_toggle_options_panel)

        self.cancel_act = QAction(self)
        self.cancel_act.setIcon(QIcon.fromTheme(gcom.ICON_CANCEL))
        self.cancel_act.setShortcut('Escape')
        self.cancel_act.setStatusTip('Cancel')

        self.export_act = QAction('&Export Audio...')
        self.export_act.triggered.connect(self._export)
        if com.mpv_error is not None:
            self.export_act.setEnabled(False)

        self.about_act = QAction('&About ' + APP_TITLE, self)
        self.about_act.setIcon(QIcon.fromTheme(gcom.ICON_ABOUT))
        self.about_act.triggered.connect(self._about_show)

        self.log_viewer_act = gcom.SplitAction('&Message log', self)
        self.log_viewer_act.setShortcut(QKeySequence('Ctrl+E'))
        self.log_viewer_act.setIcon(QIcon.fromTheme(gcom.ICON_MESSAGE_LOG))
        self.log_viewer_act.setStatusTip('View message log')
        self.log_viewer_act.triggered_connect(self._log_show)

        self.device_window_act = QAction('Select audio output &device...')
        self.device_window_act.setIcon(QIcon.fromTheme(gcom.ICON_AUDIO_DEVICE))
        self.device_window_act.setStatusTip('Select audio output device')
        self.device_window_act.triggered.connect(self._device_window_show)

        self.show_log_plot_act = QAction('Show &dB plot')
        self.show_log_plot_act.setStatusTip('Show a plot of dB vs frequency')
        self.show_log_plot_act.triggered.connect(self._show_log_plot)

        self.show_linear_plot_act = QAction('Show &power plot')
        self.show_linear_plot_act.setStatusTip(
                                        'Show a plot of power vs frequency')
        self.show_linear_plot_act.triggered.connect(self._show_linear_plot)

        self.debug_drag_act = QAction('Debug dragging')
        self.debug_drag_act.setCheckable(True)
        self.debug_drag_act.setChecked(False)

        self.play_act = QAction(self)
        self.play_act.setShortcuts([QKeySequence('Ctrl+P'),
                                    Qt.Key.Key_MediaPlay])
        self.play_act.setIcon(QIcon.fromTheme(gcom.ICON_PLAY))
        self.play_act.setStatusTip('Play (Ctrl+P)')
        self.play_act.triggered.connect(self._play)

        self.pause_act = QAction(self)
        self.pause_act.setShortcuts(['Space',
                                     Qt.Key.Key_MediaPause])
        self.pause_act.setIcon(QIcon.fromTheme(gcom.ICON_PAUSE))
        self.pause_act.setStatusTip('Pause (Spacebar)')
        self.pause_act.triggered.connect(self._pause)

        self.stop_act = QAction(self)
        self.stop_act.setShortcuts([QKeySequence('Ctrl+S'),
                                    Qt.Key.Key_MediaStop])
        self.stop_act.setIcon(QIcon.fromTheme(gcom.ICON_STOP))
        self.stop_act.setStatusTip('Stop (Ctrl+S)')
        self.stop_act.triggered.connect(self._stop)

        if DEBUG_BUTTON:
            self.debug_act = QAction(self)
            #self.debug_act.setShortcut(QKeySequence('Ctrl+P'))
            self.debug_act.setIcon(QIcon.fromTheme(gcom.ICON_ABOUT))
            self.debug_act.setStatusTip('Print stuffs')
            self.debug_act.triggered.connect(self._debug)

        self.player_back_act = QAction(self)
        self.player_back_act.setShortcut('Left')
        self.player_back_act.setIcon(QIcon.fromTheme(gcom.ICON_PLAYER_BACK))
        self.player_back_act.setStatusTip('Rewind 10 seconds (Left arrow)')

        self.player_forward_act = QAction(self)
        self.player_forward_act.setShortcut('Right')
        self.player_forward_act.setIcon(QIcon.fromTheme(
                                                    gcom.ICON_PLAYER_FORWARD))
        self.player_forward_act.setStatusTip('Jump ahead 10 seconds'
                                                    ' (Right arrow)')


        self._initUI()

        self._nothing_selected()

        self.setAcceptDrops(True)

        for arg in args.file:
            self.file_selector.handle_command_line_arg(arg)


    def dragEnterEvent(self, event):
        if self.debug_drag_act.isChecked():
            s = (f'\ndragEnterEvent\n'
                 f'source: {event.source()}\n'
                 f'hasUrls: {event.mimeData().hasUrls()}\n'
                 f'possibleActions: {event.possibleActions()}\n'
                 f'proposedAction: {event.proposedAction()}')
            self._log(s, lv.LOG_LEVEL_NORMAL)
        possible = event.possibleActions()
        acceptable = Qt.DropAction.CopyAction | Qt.DropAction.LinkAction
        if (event.source() is None
          and possible & acceptable
          and event.mimeData().hasUrls()):
            if event.proposedAction() & acceptable:
                event.acceptProposedAction()
            elif Qt.DropAction.LinkAction & possible:
                event.setDropAction(Qt.DropAction.LinkAction)
                event.accept()
            elif Qt.DropAction.CopyAction & possible:
                event.setDropAction(Qt.DropAction.CopyAction)
                event.accept()


    def dropEvent(self, event):
        possible = event.possibleActions()
        acceptable = Qt.DropAction.CopyAction | Qt.DropAction.LinkAction
        if event.proposedAction() & acceptable:
            event.acceptProposedAction()
        elif Qt.DropAction.LinkAction & possible:
            event.setDropAction(Qt.DropAction.LinkAction)
            event.accept()
        elif Qt.DropAction.CopyAction & possible:
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if not path:
                path = url.toString()
            self.file_selector.handle_drop(path)


    def closeEvent(self, event):
        reply = QMessageBox.question(
                                self,
                                'Confirm',
                                QUIT_CONFIRMATION_MESSAGE,
                                QMessageBox.StandardButton.Yes
                                | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.analyzed_audio.close()
            self.export_window.quit_thread()
            event.accept()
        else:
            event.ignore()

    def _init_menubar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu('&File')
        file_menu.addAction(self.export_act)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_act)

        view_menu = menubar.addMenu('&View')
        view_menu.addAction(self.show_log_plot_act)
        view_menu.addAction(self.show_linear_plot_act)
        view_menu.addSeparator()
        view_menu.addAction(self.log_viewer_act.menu())

        option_menu = menubar.addMenu('&Options')
        option_menu.addAction(self.showhidden_act)
        option_menu.addAction(self.play_start_end_act)
        option_menu.addAction(self.toggle_options_panel_act)
        option_menu.addSeparator()
        option_menu.addAction(self.device_window_act)
        option_menu.addSeparator()
        option_menu.addAction(self.debug_drag_act)

        go_menu = menubar.addMenu('&Go')
        go_menu.addAction(self.file_selector.up_act.menu())
        go_menu.addAction(self.file_selector.back_act.menu())
        go_menu.addAction(self.file_selector.forward_act.menu())
        go_menu.addAction(self.file_selector.home_act.menu())

        help_menu = menubar.addMenu('&Help')
        help_menu.addAction(self.about_act)

        self.menubar = menubar

    def _init_statusbar(self):
        self.prog_bar = QProgressBar()
        self.prog_bar.setRange(0, 100)
        sp = QSizePolicy()
        self.prog_bar.setSizePolicy(sp)
        self.statusBar().addPermanentWidget(self.prog_bar, 2)
        self.cancel_button = QToolButton()
        self.cancel_button.setDefaultAction(self.cancel_act)
        self.statusBar().addPermanentWidget(self.cancel_button)
        self.prog_bar.hide()
        self.cancel_button.hide()
        self.cancel_act.setEnabled(False)
        self.statusBar().showMessage(INIT_STATUS_MESSAGE)

    def _update_progbar(self, progress):
        if progress >= 0:
            self.prog_bar.setValue(int(progress * 100))
        else:
            self.prog_bar.reset()

    def _update_statusbar(self, status):
        self.statusBar().showMessage(status)

    def _init_toolbar(self):
        self.toolbar = self.addToolBar('Toolbar')

        self.toolbar.addAction(self.toggle_toggle_options_panel_act)
        self.toolbar.addAction(self.log_viewer_act.button())

        self.toolbar.addSeparator()

        self.toolbar.addAction(self.play_act)
        self.pause_button = QToolButton()
        self.pause_button.setDefaultAction(self.pause_act)
        self.toolbar.addWidget(self.pause_button)
        self.toolbar.addAction(self.stop_act)
        self.toolbar.addAction(self.player_back_act)
        self.toolbar.addAction(self.player_forward_act)
        if DEBUG_BUTTON:
            self.toolbar.addAction(self.debug_act)

        lcd_style = ('QLCDNumber {'
                    f' background-color: {disp.DISPLAY_BG_COLOR.name()};'
                    f' color: {disp.DISPLAY_DATA_COLOR.name()};'
                    ' }')
        self.lcd1 = QLCDNumber()
        self.lcd1.setDigitCount(5)
        self.lcd1.setStyleSheet(lcd_style)
        self.toolbar.addWidget(self.lcd1)
        self.lcd1.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        self.lcd1.display('--:--')

        self.slider = _Slider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setMinimumWidth(100)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBothSides)
        self.toolbar.addWidget(self.slider)

        self.lcd2 = QLCDNumber()
        self.lcd2.setDigitCount(6)
        self.toolbar.addWidget(self.lcd2)
        self.lcd2.setStyleSheet(lcd_style)
        self.lcd2.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        self.lcd2.display('---:--')

        self.now_playing = QLabel()
        self.now_playing.setTextFormat(Qt.TextFormat.PlainText)
        self.now_playing.setMinimumWidth(30)
        self.now_playing.setSizePolicy(QSizePolicy.Policy.Minimum,
                                       QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(self.now_playing)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding,
                             QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer)
        self.toolbar.addAction(self.exit_act)

    def _toggle_toggle_options_panel(self):
        if self.toggle_options_panel_act.isChecked():
            self.toggle_options_panel_act.setChecked(False)
            self._toggle_options_panel(False)
        else:
            self.toggle_options_panel_act.setChecked(True)
            self._toggle_options_panel(True)

    def _show_options_panel(self):
        if not self.toggle_options_panel_act.isChecked():
            self.toggle_options_panel_act.setChecked(True)
            self._toggle_options_panel(True)

    def _toggle_options_panel(self, checked):
        if checked:
            self.stack.setCurrentWidget(self.option_panel)
            self.toggle_toggle_options_panel_act.setIcon(
                                                    QIcon(gcom.ICON_FILES))
        else:
            self.stack.setCurrentWidget(self.file_selector)
            self.toggle_toggle_options_panel_act.setIcon(
                                                    QIcon(gcom.ICON_OPTIONS))

    def _starting_processing(self):
        self.cancel_act.setEnabled(True)
        self.prog_bar.show()
        self.cancel_button.show()

    def _finished_processing(self):
        self._pitch_change(self.option_panel.widgets[gcom.OPTION_PITCH].get())
        self.prog_bar.hide()
        self.cancel_button.hide()
        self.cancel_act.setEnabled(False)

    def _export(self):
        self.export_window.show(self.analyzed_audio.current_selection,
                                self.analyzed_audio.current_listed_title,
                                self.analyzed_audio.current_options,
                                self.analyzed_audio.current_metadata)

    def _starting_exporting(self):
        self._exporting_in_progress = True
        self.export_act.setEnabled(False)

    def _finished_exporting(self):
        self._exporting_in_progress = False
        if com.mpv_error is not None:
            self.export_act.setEnabled(True)

    def _about_show(self):
        self.about_window.show()

    def _log_show(self):
        self.log_viewer.show()
        self.log_viewer_act.setIcon(QIcon.fromTheme(gcom.ICON_MESSAGE_LOG))

    def _device_window_show(self):
        try:
            self.player.show_device_window()
        except OSError:
            self.device_window_act.setEnabled(False)

    def _show_log_plot(self):
        self.analyzed_audio.show_plot('log')

    def _show_linear_plot(self):
        self.analyzed_audio.show_plot('linear')

    def _log(self, message, level):
        if level == lv.LOG_LEVEL_ERROR and not self.log_viewer.isVisible():
            self.log_viewer_act.setIcon(QIcon.fromTheme(gcom.ICON_ALERT))
        self.log_viewer.add_message(message + '\n', level)

    def _handle_option_error(self, option):
        self.option_panel.widgets[option].set_error()
        self.option_panel.ensure_visible()

    def _something_selected(self):
        self._pitch_change(self.option_panel.widgets[gcom.OPTION_PITCH].get())
        self.something_selected=True
        self.option_panel.set_apply_enabled(True)
        self.show_log_plot_act.setEnabled(True)
        self.show_linear_plot_act.setEnabled(True)
        if not self._exporting_in_progress and com.mpv_error is None:
            self.export_act.setEnabled(True)

    def _nothing_selected(self):
        self.something_selected=False
        self.option_panel.set_apply_enabled(False)
        self.show_log_plot_act.setEnabled(False)
        self.show_linear_plot_act.setEnabled(False)
        self.export_act.setEnabled(False)

    def _play_start_end_toggled(self, checked):
        if checked:
            start = self._currently_playing_start
            end = self._currently_playing_end
        else:
            start = None
            end = None
        self.player.update_corrections(None, None, start, end)

    def _play(self):
        path = self.analyzed_audio.current_selection
        if path:
            if self.player.get_currently_playing() != path:
                options = self.analyzed_audio.current_options
                self.duration = self.analyzed_audio.current_duration
                self._currently_playing_start = options[gcom.OPTION_START]
                self._currently_playing_end = options[gcom.OPTION_END]
                if self.play_start_end_act.isChecked():
                    start = options[gcom.OPTION_START]
                    end = options[gcom.OPTION_END]
                else:
                    start = None
                    end = None
                try:
                    self.player.play(path,
                                     self.duration,
                                     options[gcom.OPTION_PITCH],
                                     options[gcom.OPTION_TEMPO],
                                     start,
                                     end,
                                    )
                except OSError:
                    self.play_act.setEnabled(False)
                    return
                self.now_playing.setText(self.analyzed_audio.current_title)
                if self.duration is not None:
                    self.slider.setTickInterval(
                                            6000//max(int(self.duration), 1))
            elif self.slider.value() >= 99:
                self.player.set_percent(0)
            self.option_panel.start_end_enable(True)
        self.player.set_pause(False)

    def _pause(self):
        self.player.toggle_pause()

    def _update_pause(self, pause):
        self.pause_button.setDown(pause)

    def _stop(self):
        self.player.stop()
        self.now_playing.clear()
        self.option_panel.start_end_enable(False)

    def _back(self):
        self.player.back()

    def _forward(self):
        self.player.forward()

    def _debug(self):
        pass

    def _update_time_pos(self, is_valid, time_pos):
        if is_valid:
            t = min(time_pos, 5999)
            display = f'{t//60:0>2}:{t%60:0>2}'
        else:
            display = '--:--'
        self.lcd1.display(display)

    def _enable_slider_update(self):
        self._slider_update_enabled = True

    def _disable_slider_update(self):
        self._slider_update_enabled = False

    def _update_percent(self, percent):
        if self._slider_update_enabled and not self.slider.isSliderDown():
            self.slider.setValue(percent)
        if self.duration is None:
            self.duration = self.player.get_duration()
            if self.duration is not None:
                self.slider.setTickInterval(6000//max(int(self.duration), 1))

    def _set_percent(self):
        self.player.set_percent(self.slider.value())
        self._enable_slider_update()

    def _update_time_rem(self, is_valid, time_rem):
        if is_valid:
            t = min(time_rem, 5999)
            display = f'-{t//60:0>2}:{t%60:0>2}'
        else:
            display = '---:--'
        self.lcd2.display(display)

    def _update_now_playing(self, title, result_rows=None):
        path = self.analyzed_audio.current_selection
        if path and title != ' ':
            if self.player.get_currently_playing() == path:
                self.now_playing.setText(title)

    def _update_corrections(self, options, reread_requested):
        if (self.analyzed_audio.current_selection
              == self.player.get_currently_playing()):
            self._currently_playing_start = options[gcom.OPTION_START]
            self._currently_playing_end = options[gcom.OPTION_END]
            if self.play_start_end_act.isChecked():
                start = options[gcom.OPTION_START]
                end = options[gcom.OPTION_END]
            else:
                start = None
                end = None
            self.player.update_corrections(options[gcom.OPTION_PITCH],
                                           options[gcom.OPTION_TEMPO],
                                           start,
                                           end,
                                          )

    def _pitch_change(self, factor):
        if self.something_selected:
            options = self.analyzed_audio.current_options
            relative_change = factor / options[gcom.OPTION_PITCH]
            cents = com.ratio_to_cents(relative_change)
            self.display.update_ghost_offset(cents)

    def _set_start_now(self):
        now = self.player.get_current_position()
        self.option_panel.set_start(now)

    def _set_end_now(self):
        now = self.player.get_current_position()
        self.option_panel.set_end(now)

    def _initUI(self):
        self.resize(800, 850)
        self.setWindowTitle(APP_TITLE)
        self.setWindowIcon(QIcon(gcom.APP_ICON))

        option_panel = op.OptionPanel(self.args)
        self.option_panel = option_panel
        file_selector = fs.FileSelector(option_panel)
        self.file_selector = file_selector
        analyzed_audio = ga.AnalyzedAudio()
        self.analyzed_audio = analyzed_audio
        display = disp.Display()
        self.display = display

        self.player = pl.Player(self)
        if com.mpv_error is not None:
            self.play_act.setEnabled(False)
            self.stop_act.setEnabled(False)
            self.pause_act.setEnabled(False)
            self.player_back_act.setEnabled(False)
            self.player_forward_act.setEnabled(False)
            self.device_window_act.setEnabled(False)

        option_panel.set_default_options()

        self.cancel_act.triggered.connect(analyzed_audio.cancel)

        stack = QStackedWidget()
        self.stack = stack
        stack.addWidget(file_selector)
        stack.addWidget(option_panel)

        hsplitter = QSplitter(Qt.Orientation.Horizontal)
        hsplitter.addWidget(analyzed_audio)
        hsplitter.insertWidget(0, stack)

        vsplitter = QSplitter(Qt.Orientation.Vertical)
        vsplitter.addWidget(display)
        vsplitter.addWidget(hsplitter)

        self.setCentralWidget(vsplitter)

        self._init_menubar()
        self._init_statusbar()
        self._init_toolbar()

        self.export_window = ex.ExportWindow(self)
        self.export_window.set_dir(self.file_selector.model.rootDirectory())

        file_selector.SelectForAnalysis.connect(analyzed_audio.add_audio)
        self.showhidden_act.toggled.connect(file_selector._set_show_hidden)
        file_selector.UpdateStatusbar.connect(self._update_statusbar)
        file_selector.model.rootPathChanged.connect(self.export_window.set_dir)
        self.analyzed_audio.UpdateStatusbar.connect(self._update_statusbar)
        self.analyzed_audio.UpdateProgbar.connect(self._update_progbar)
        self.analyzed_audio.Starting.connect(self._starting_processing)
        self.analyzed_audio.Finished.connect(self._finished_processing)
        self.analyzed_audio.AddToLog.connect(self._log)
        self.analyzed_audio.OptionError.connect(self._handle_option_error)
        self.analyzed_audio.SomethingSelected.connect(self._something_selected)
        self.analyzed_audio.NothingSelected.connect(self._nothing_selected)
        self.option_panel.PushOptions.connect(analyzed_audio.change_options)
        self.option_panel.PushOptions.connect(self._update_corrections)
        self.option_panel.PitchChange.connect(self._pitch_change)
        self.option_panel.widgets[gcom.OPTION_START].button_clicked.connect(
                self._set_start_now)
        self.option_panel.widgets[gcom.OPTION_END].button_clicked.connect(
                self._set_end_now)
        self.option_panel.PayAttentionToMe.connect(self._show_options_panel)
        self.player.TickPos.connect(self._update_time_pos)
        self.player.TickRem.connect(self._update_time_rem)
        self.player.Percent.connect(self._update_percent)
        self.player.PauseStatus.connect(self._update_pause)
        self.player.AddToLog.connect(self._log)
        self.slider.MousePressed.connect(self._disable_slider_update)
        self.slider.MouseReleased.connect(self._set_percent)
        self.player_back_act.triggered.connect(self._back)
        self.player_forward_act.triggered.connect(self._forward)
        self.export_window.AddToLog.connect(self._log)
        self.export_window.Starting.connect(self._starting_exporting)
        self.export_window.Finished.connect(self._finished_exporting)

        analyzed_audio.DisplayResult.connect(display.update_data,
                                            Qt.ConnectionType.QueuedConnection)
        analyzed_audio.DisplayResult.connect(self._update_now_playing)
        analyzed_audio.PushOptions.connect(option_panel.set_options)

        self.about_window = _AboutWindow(self)

        self.log_viewer = lv.LogViewer(self)

        self.show()

        hsplitter.moveSplitter(500, 1)
        vsplitter.moveSplitter(342, 1)

        while self.message_queue:
            message = self.message_queue.popleft()
            self._log(message.msg, message.level)


class _Message():
    def __init__(self, msg, level):
        self.msg = msg
        self.level = level


class _MessageQueue(deque):
    def add_msg(self, msg, level=eh.NORMAL):
        self.append(_Message(msg, level))


def main():
    parser = ap.get_arg_parser(version=VERSION_STRING,
                               description=DESCRIPTION,
                               gui_mode=True)
    cli_args, unparsed = parser.parse_known_args_gm()
    message_queue = _MessageQueue()
    args = ap.merge_args(cli_args, print_msg=message_queue.add_msg)
    if not ap.validate(args):
        return 2

    app = QApplication(sys.argv[:1] + unparsed)

    # Needed to make libmpv work
    if os.name != 'nt':
        import locale
        locale.setlocale(locale.LC_NUMERIC, 'C')

    ui = _MainUI(args, message_queue)

    return app.exec()

if __name__ == '__main__':
    sys.exit(main())
