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


"""Asynchronous audio analysis for the GUI."""


__author__ = 'Jessie Blue Cassell'


__all__ = [
            'AnalyzedAudio',
          ]


import os

from PyQt6.QtCore import (
                          Qt,
                          QDir,
                          QObject,
                          pyqtSignal,
                          QThread,
                          QPersistentModelIndex,
                         )
from PyQt6.QtWidgets import (
                             QWidget,
                             QVBoxLayout,
                             QHBoxLayout,
                             QToolButton,
                             QTableView,
                             QCheckBox,
                            )
from PyQt6.QtGui import (
                         QIcon,
                         QAction,
                         QStandardItemModel,
                         QStandardItem,
                        )

import audio_tuner.analysis as anal
import audio_tuner.error_handling as eh
import audio_tuner.common as com

import audio_tuner_gui.common as gcom
import audio_tuner_gui.log_viewer as lv


_FFMPEG_ERROR_SS = 'Invalid duration specification for ss'
_FFMPEG_ERROR_TO = 'Invalid duration specification for to'
_MPV_ERROR_START = 'Invalid value for mpv option: start'
_MPV_ERROR_END = 'Invalid value for mpv option: end'
_START_ERRORS = (_FFMPEG_ERROR_SS, _MPV_ERROR_START)
_END_ERRORS = (_FFMPEG_ERROR_TO, _MPV_ERROR_END)


class _AudioView(QTableView):
    def __init__(self):
        super().__init__()

        self.verticalHeader().setSectionsMovable(True)
        rowheight = int(self.fontMetrics().height() * 1.35)
        self.verticalHeader().setDefaultSectionSize(rowheight)
        self.horizontalHeader().setSectionsMovable(True)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.setTabKeyNavigation(False)
        self.setShowGrid(False)


class _Worker(QObject):
    """A worker class to be run in it's own thread that handles
    analysis.  Inherits from QObject.
    """

    UpdateStatusbar = pyqtSignal(str)
    """Signal emitted to request a string be displayed on the status bar.

    Parameters
    ----------
    str
        The string.
    """

    UpdateProgbar = pyqtSignal(float)
    """Signal emitted to request a progress bar update.

    Parameters
    ----------
    float
        The amount of progress, from 0 to 1.
    """

    ResultReady = pyqtSignal(anal.Analysis)
    """Signal emitted when analysis is finished and the result is ready.

    Parameters
    ----------
    audio_tuner.analysis.Analysis
        The analysis object that has finished with it's analysis.
    """

    ProcessingError = pyqtSignal(anal.Analysis)
    """Signal emitted when the analysis object raises an exception
    during analysis.

    Parameters
    ----------
    audio_tuner.analysis.Analysis
        The analysis object.
    """

    AddToLog = pyqtSignal(str, int)
    """Signal emitted to request a message be added to the log.

    Parameters
    ----------
    str
        The message.
    int
        The severity level as defined in audio_tuner_gui.log_viewer
        (LOG_LEVEL_ERROR, LOG_LEVEL_WARNING or LOG_LEVEL_NORMAL).
    """

    OptionError = pyqtSignal(str)
    """Signal emitted when an option is set to an invalid value.

    Parameters
    ----------
    str
        The name of the option, as defined in audio_tuner_gui.common.
    """

    def __init__(self):
        super().__init__()

    def _progress_check(self, progress: float) -> bool:
        self.UpdateProgbar.emit(progress)
        return not QThread.currentThread().isInterruptionRequested()

    def _print_msg(self, msg, level=eh.NORMAL):
        msg = msg.rstrip('\n')
        if level in (eh.DEBUG, eh.NORMAL):
            self.AddToLog.emit(msg, lv.LOG_LEVEL_NORMAL)
        elif level == eh.WARNING:
            self.AddToLog.emit(msg, lv.LOG_LEVEL_WARNING)
        elif level == eh.ERROR:
            self.AddToLog.emit(msg, lv.LOG_LEVEL_ERROR)
            if any(x in msg for x in _START_ERRORS):
                self.OptionError.emit(gcom.OPTION_START)
            if any(x in msg for x in _END_ERRORS):
                self.OptionError.emit(gcom.OPTION_END)

    def analyze(self,
                analysis: anal.Analysis,
                options: gcom.Options,
                reread_requested: bool) -> None:
        """Do the analysis.  This gets passed an instance of
        audio_tuner.analysis.Analysis, and then spits it out again via
        the ResultReady signal when it's done (or via the
        ProcessingError signal if it went wrong).  The Analysis instance
        will have `result_rows` and `options` in addition to it's usual
        attributes.  `result_rows` is a list of
        audio_tuner_gui.common.RowData objects that can be passed to the
        `update_data` method of audio_tuner_gui.display.Display, and
        `options` is the audio_tuner_gui.common.Options object that was
        passed to the `options` parameter of this method.

        Parameters
        ----------
        analysis : audio_tuner.analysis.Analysis
            The Analysis instance.
        options : audio_tuner_gui.common.Options
            The analysis options.
        reread_requested : bool
            If True, forces a reread of the audio data with pitch and
            tempo corrections applied.
        """

        if QThread.currentThread().isInterruptionRequested():
            return
        analysis.try_sequence = options[gcom.OPTION_BACKENDS]
        analysis.print_msg = self._print_msg
        if (reread_requested
          and (analysis.pitch != options[gcom.OPTION_PITCH]
               or analysis.tempo != options[gcom.OPTION_TEMPO])):
            analysis.pitch = options[gcom.OPTION_PITCH]
            analysis.tempo = options[gcom.OPTION_TEMPO]
            redo_level = gcom.REDO_LEVEL_ALL
        else:
            redo_level = options.redo_level(getattr(analysis, 'options', None))
        basename = os.path.basename(analysis.inputfile)
        self.UpdateStatusbar.emit('Analyzing ' + basename + '...')
        if redo_level >= gcom.REDO_LEVEL_ALL:
            try:
                s = '\nLoading "' + basename + '"'
                self.AddToLog.emit(s, lv.LOG_LEVEL_NORMAL)
                size = 2**options[gcom.OPTION_SIZE_EXP]
                if options[gcom.OPTION_PAD]:
                    pad_amounts = (size * 2, size * 2)
                else:
                    pad_amounts = None
                analysis.load_data(start=options[gcom.OPTION_START],
                                   end=options[gcom.OPTION_END],
                                   samplerate=options[gcom.OPTION_SAMPLERATE],
                                   pad=pad_amounts)
            except eh.LoadError:
                s = 'Error processing ' + basename
                self.UpdateStatusbar.emit(s)
                self.ProcessingError.emit(analysis)
                return
            try:
                self.AddToLog.emit('Analyzing "' + basename + '"',
                                   lv.LOG_LEVEL_NORMAL)
                analysis.fft(size=size, progress_hook=self._progress_check)
            except eh.ShortError:
                s = 'Error processing ' + basename
                self.UpdateStatusbar.emit(s)
                self.ProcessingError.emit(analysis)
                self.AddToLog.emit(eh.ERRMSG_SHORT,
                                   lv.LOG_LEVEL_ERROR)
                return
            except eh.Interrupted:
                self.UpdateStatusbar.emit('Processing aborted')
                self.UpdateProgbar.emit(-1)
                self.AddToLog.emit('Processing aborted',
                                   lv.LOG_LEVEL_WARNING)
                return
        if redo_level >= gcom.REDO_LEVEL_FIND_PEAKS:
            analysis.find_peaks(
                    low_cut=options[gcom.OPTION_LOW_CUT] * analysis.pitch,
                    high_cut=options[gcom.OPTION_HIGH_CUT] * analysis.pitch,
                    max_peaks=options[gcom.OPTION_MAX_PEAKS],
                    dB_range=options[gcom.OPTION_DB_RANGE])
        if redo_level >= gcom.REDO_LEVEL_TUNING_SYSTEM:
            peaks = analysis.peaks
            tuning_system = options.tuning_system
            result_rows = []
            pitch_offset = options[gcom.OPTION_PITCH] / analysis.pitch
            for note in tuning_system(
                   options[gcom.OPTION_LOW_CUT] * options[gcom.OPTION_PITCH],
                   options[gcom.OPTION_HIGH_CUT] * options[gcom.OPTION_PITCH]):
                note_freq, note_name, band_bottom, band_top = note
                for peak in [p[0] * pitch_offset for p in peaks]:
                    if peak > band_bottom and peak <= band_top:
                        result_row: gcom.RowData = {
                                      'note': note_name,
                                      'standard': note_freq,
                                      'measured': peak
                                     }
                        freq_ratio = note_freq/peak
                        result_row['cents'] = -com.ratio_to_cents(freq_ratio)
                        result_row['correction'] = freq_ratio * pitch_offset
                        result_rows.append(result_row)
            analysis.result_rows = result_rows

        analysis.options = options

        self.ResultReady.emit(analysis)
        self.UpdateProgbar.emit(-1)
        self.AddToLog.emit('Finished analyzing "' + basename + '"',
                           lv.LOG_LEVEL_NORMAL)


class AnalyzedAudio(QWidget):
    """A widget that analyzes audio and stores the results.  Inherits
    from QWidget.

    .. versionadded:: 0.8.1 current_listed_title

    Attributes
    ----------
    current_title : str
        The title of the currently selected audio, or None if none is
        selected.  This will be the filename if the file has no title
        tag.
    current_listed_title : str
        The title as listed in the widget, or None if it's blank.  The
        only difference between this and `current_title` is that this
        will not fall back to the filename if the file has no title tag.
    current_selection : str
        The canonical file path of the currently selected audio, or None
        if none is selected.
    current_options : audio_tuner_gui.common.Options
        The settings used in the analysis of the currently selected
        audio, or None if none is selected.
    current_duration : float
        The duration in seconds of the currently selected audio, or None
        if none is selected.
    current_metadata : dict
        The tags of the currently selected audio, or None if none is
        selected.
    """

    UpdateStatusbar = pyqtSignal(str)
    """Signal emitted to request a string be displayed on the status bar.

    Parameters
    ----------
    str
        The string.
    """

    UpdateProgbar = pyqtSignal(float)
    """Signal emitted to request a progress bar update.

    Parameters
    ----------
    float
        The amount of progress, from 0 to 1.
    """

    AnalyzeAudio = pyqtSignal(anal.Analysis, gcom.Options, bool)
    """Signal emitted to tell the worker thread to run an analysis.

    Parameters
    ----------
    audio_tuner.analysis.Analysis
        The analysis object to use.
    audio_tuner_gui.common.Options
        The options.
    bool
        Whether to force a reread of the file with pitch and tempo
        corrections.
    """

    DisplayResult = pyqtSignal(str, list)
    """Signal emitted to request a display update.

    Parameters
    ----------
    str
        The name of the song.
    list[audio_tuner_gui.common.RowData]
        The row data for each row.
    """

    PushOptions = pyqtSignal(gcom.Options)
    """Signal emitted when analyzed audio is selected so that the
    options panel can be updated.

    Parameters
    ----------
    audio_tuner_gui.common.Options
        The options of the newly selected analysed audio.
    """

    Starting = pyqtSignal()
    """Signal emitted when analysis is starting."""

    Finished = pyqtSignal()
    """Signal emitted when analysis is finished."""

    AddToLog = pyqtSignal(str, int)
    """Signal emitted to request a message be added to the log.

    Parameters
    ----------
    str
        The message.
    int
        The severity level as defined in audio_tuner_gui.log_viewer
        (LOG_LEVEL_ERROR, LOG_LEVEL_WARNING or LOG_LEVEL_NORMAL).
    """

    OptionError = pyqtSignal(str)
    """Signal emitted when an option is set to an invalid value.

    Parameters
    ----------
    str
        The name of the option, as defined in audio_tuner_gui.common.
    """

    SomethingSelected = pyqtSignal()
    """Signal emitted when analyzed audio is selected."""

    NothingSelected = pyqtSignal()
    """Signal emitted when there's no longer anything selected."""


    def __init__(self):
        super().__init__()

        self.current_title = None
        self.current_listed_title = None
        self.current_selection = None
        self.current_options = None
        self.current_duration = None
        self.current_metadata = None

        self._analysis = {}
        self._in_progress = {}
        self._cancelled = False

        vbox = QVBoxLayout(self)
        vbox.setSpacing(5)
        vbox.setContentsMargins(3, 3, 3, 3)

        self._init_audio_view()
        self._init_control_panel()

        vbox.addWidget(self._view)
        vbox.addWidget(self._panel)

        self._start_worker_thread()

    def _start_worker_thread(self):
        worker_thread = QThread(self)
        self._worker_thread = worker_thread
        self._worker = _Worker()
        self._worker.moveToThread(worker_thread)
        worker_thread.finished.connect(self._worker.deleteLater)
        self.AnalyzeAudio.connect(self._worker.analyze,
                                        Qt.ConnectionType.QueuedConnection)
        self._worker.ResultReady.connect(self._handle_result,
                                        Qt.ConnectionType.QueuedConnection)
        self._worker.UpdateStatusbar.connect(self._update_statusbar,
                                        Qt.ConnectionType.QueuedConnection)
        self._worker.UpdateProgbar.connect(self._update_progbar,
                                        Qt.ConnectionType.QueuedConnection)
        self._worker.ProcessingError.connect(self._handle_error,
                                        Qt.ConnectionType.QueuedConnection)
        self._worker.AddToLog.connect(self._handle_log_message,
                                        Qt.ConnectionType.QueuedConnection)
        self._worker.OptionError.connect(self._handle_option_error,
                                        Qt.ConnectionType.QueuedConnection)
        worker_thread.start()

    def _update_statusbar(self, string):
        self.UpdateStatusbar.emit(string)

    def _update_progbar(self, n):
        self.UpdateProgbar.emit(n)

    def _init_audio_view(self):
        model = QStandardItemModel(0, 3, self)
        headers = ('Trk', 'Title', 'Filename')
        model.setHorizontalHeaderLabels(headers)

        view = _AudioView()
        view.setModel(model)

        view.setColumnWidth(0, 20)

        view.selectionModel().currentRowChanged.connect(self._audio_selected)
        model.itemChanged.connect(self._item_changed)

        self._model = model
        self._view = view

    def _init_control_panel(self):
        panel = QWidget()
        hbox = QHBoxLayout(panel)
        hbox.setContentsMargins(0, 0, 0, 0)

        remove_act = QAction(self)
        remove_act.setIcon(QIcon.fromTheme(gcom.ICON_REMOVE))
        remove_act.setStatusTip('Remove from list (Backspace)')
        remove_act.setShortcut('Backspace')
        remove_act.triggered.connect(self.remove_audio)

        remove_button = QToolButton()
        remove_button.setDefaultAction(remove_act)
        hbox.addWidget(remove_button)

        hbox.addStretch()

        set_remove_enabled_switch = QCheckBox('Enable &removal', self)
        set_remove_enabled_switch.setStatusTip(
                                        'Enable removing items from list')
        set_remove_enabled_switch.setCheckState(Qt.CheckState.Unchecked)
        set_remove_enabled_switch.stateChanged.connect(
                                                self._set_removal_enabled)
        hbox.addWidget(set_remove_enabled_switch)

        self._panel = panel
        self._remove_act = remove_act
        self._remove_button = remove_button
        self._set_removal_enabled(False)

    def _audio_selected(self, new, prev):
        title = None
        item1 = self._model.item(new.row(), 1)
        item2 = self._model.item(new.row(), 2)
        if item1:
            title = item1.text()
            listed_title = title
        if not title or title == ' ':
            listed_title = None
            if item2:
                title = item2.text()
        if title:
            self.current_title = title
            self.current_listed_title = listed_title
            self.current_selection = item2.data()
            self.current_options = self._analysis[item2.data()].options
            self.current_duration = self._analysis[item2.data()].file_duration
            self.current_metadata = self._analysis[item2.data()].file_metadata
            self.DisplayResult.emit(title,
                                    self._analysis[item2.data()].result_rows)
            self.PushOptions.emit(self.current_options)
            self.SomethingSelected.emit()

    def _item_changed(self, item):
        data = item.data()
        if data is not None:
            if item.text() == '':
                self._model.itemChanged.disconnect(self._item_changed)
                file_title = self._analysis[data].file_title
                item.setText(file_title if file_title else ' ')
                self._model.itemChanged.connect(self._item_changed)
            if data == self.current_selection:
                item1 = item
                item2 = self._model.item(item.row(), 2)
                if item1:
                    title = item1.text()
                    listed_title = title
                if not title or title == ' ':
                    listed_title = None
                    if item2:
                        title = item2.text()
                self.current_listed_title = listed_title
                if title:
                    self.current_title = title
                    self.DisplayResult.emit(title,
                                    self._analysis[item2.data()].result_rows)

    def add_audio(self, path, options):
        """Analyze an audio file asynchronously and add it to the list
        of analyzed audio.

        Parameters
        ----------
        path : str
            The path of the audio file to analyze.
        options : audio_tuner_gui.common.Options
            Analysis options.
        """

        if QDir(path).exists():
            return

        canonical_path = os.path.realpath(path)
        if canonical_path in self._in_progress:
            return
        if canonical_path in self._analysis:
            index = self._analysis[canonical_path].index
            self._view.selectRow(index.row())
            return

        if self._cancelled:
            self._worker_thread.quit()
            self._start_worker_thread()
            self._cancelled = False

        if len(self._in_progress) == 0:
            self.Starting.emit()

        self._in_progress[canonical_path] = True
        analysis = anal.Analysis(canonical_path)
        self.AnalyzeAudio.emit(analysis, options, False)

    def change_options(self, new_options, reread_requested):
        """Change the options of the currently selected analyzed audio.

        Parameters
        ----------
        new_options : audio_tuner_gui.common.Options
            The new options.
        reread_requested : bool
            If True, forces a reread of the audio data with pitch and
            tempo corrections applied.
        """

        canonical_path = self.current_selection
        if canonical_path is None or canonical_path in self._in_progress:
            return

        if self._cancelled:
            self._worker_thread.quit()
            self._start_worker_thread()
            self._cancelled = False

        if len(self._in_progress) == 0:
            self.Starting.emit()

        self._in_progress[canonical_path] = True
        analysis = self._analysis[canonical_path]
        self.AnalyzeAudio.emit(analysis, new_options, reread_requested)
        self.current_options = new_options

    def _handle_result(self, analysis):
        canonical_path = analysis.inputfile
        file_title = analysis.file_title
        if canonical_path in self._analysis:
            if canonical_path == self.current_selection:
                self.DisplayResult.emit(self.current_title,
                                    self._analysis[canonical_path].result_rows)
        else:
            file_track = analysis.file_track

            track_num = QStandardItem(file_track.partition('/')[0]
                                      if file_track
                                      else ' ')
            track_num.setData(None)
            title = QStandardItem(file_title if file_title else ' ')
            title.setData(canonical_path)
            filename = QStandardItem(os.path.basename(canonical_path))
            filename.setEditable(False)
            filename.setData(canonical_path)

            self._model.appendRow((track_num, title, filename))

            index = QPersistentModelIndex(self._model.indexFromItem(filename))
            self._model.setVerticalHeaderItem(index.row(), QStandardItem(' '))
            analysis.index = index
            self._analysis[canonical_path] = analysis

        del self._in_progress[canonical_path]
        if len(self._in_progress) == 0:
            self.Finished.emit()
            self.UpdateStatusbar.emit('Done')

        self.show_plot('whatever', update=True)

    def show_plot(self, plot_type, update=False):
        """Open a new window with a plot of the spectrum.  If the window
        is already open, update the plot.

        Parameters
        ----------
        plot_type : str
            The type of plot.  Valid types are 'log' and 'linear'.
        update : bool, optional
            If True, plots that are already being shown will be updated,
            but no new plots will be shown.  Default False.
        """

        canonical_path = self.current_selection
        if canonical_path is not None:
            pitch = self._analysis[canonical_path].options[gcom.OPTION_PITCH]
            try:
                self._analysis[canonical_path].show_plot(plot_type=plot_type,
                                                     asynchronous=True,
                                                     title=self.current_title,
                                                     pitch=pitch,
                                                     update=update)
            except ModuleNotFoundError:
                s = 'matplotlib not found.'
                self.AddToLog.emit(s, lv.LOG_LEVEL_ERROR)

    def _handle_log_message(self, message, level):
        self.AddToLog.emit(message, level)

    def _handle_error(self, analysis):
        del self._in_progress[analysis.inputfile]
        if len(self._in_progress) == 0:
            self.Finished.emit()

    def _handle_option_error(self, option):
        self.OptionError.emit(option)

    def _set_removal_enabled(self, enabled):
        self._remove_act.setEnabled(enabled)
        if enabled:
            self._remove_button.setAutoRaise(False)
        else:
            self._remove_button.setAutoRaise(True)

    def remove_audio(self):
        """Remove the currently selected analyzed audio from the list."""

        try:
            row = self._view.selectedIndexes()[0].row()
        except IndexError:
            return
        path = self._model.item(row, 2).data()
        del self._analysis[path]
        self._model.removeRows(row, 1)
        if len(self._analysis) == 0:
            self.DisplayResult.emit(' ', [])
            self.NothingSelected.emit()
            self.current_title = None
            self.current_listed_title = None
            self.current_selection = None
            self.current_options = None
            self.current_duration = None
            self.current_metadata = None

    def cancel(self):
        """Cancel analysis."""

        self._worker_thread.requestInterruption()
        self._cancelled = True
        self._in_progress = {}
        self.Finished.emit()

    def closeEvent(self, event):
        self._worker_thread.quit()
        super().closeEvent(event)
