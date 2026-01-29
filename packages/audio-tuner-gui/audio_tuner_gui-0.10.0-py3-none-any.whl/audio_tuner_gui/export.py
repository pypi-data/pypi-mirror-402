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


"""Audio export functionality for the GUI."""


__author__ = 'Jessie Blue Cassell'


__all__ = [
            'ExportWindow',
          ]


import os
from dataclasses import dataclass
from contextlib import contextmanager

from PyQt6.QtCore import (
                          Qt,
                          pyqtSignal,
                          QDir,
                          QObject,
                          QThread,
                         )
from PyQt6.QtWidgets import (
                             QWidget,
                             QPushButton,
                             QVBoxLayout,
                             QHBoxLayout,
                             QLineEdit,
                             QFileDialog,
                             QComboBox,
                             QCheckBox,
                             QTableView,
                            )
from PyQt6.QtGui import (
                         QStandardItemModel,
                         QStandardItem,
                        )

import audio_tuner.analysis as anal
import audio_tuner.common as com

import audio_tuner_gui.common as gcom
import audio_tuner_gui.log_viewer as lv

mpv_error = com.mpv_error
if mpv_error is None:
    import mpv


_OUTPUT_FORMATS = [
    {'name': 'flac', 'ext': 'flac', 'desc': 'Free Lossless Audio Codec'},
    {'name': 'ogg', 'ext': 'ogg', 'desc': 'Ogg Vorbis'},
    {'name': 'opus', 'ext': 'opus', 'desc': 'Ogg Opus'},
    {'name': 'spx', 'ext': 'spx', 'desc': 'Ogg Speex'},
    {'name': 'aiff', 'ext': 'aiff', 'desc': 'Audio Interchange File Format'},
    {'name': 'au', 'ext': 'au', 'desc': 'Sun Au'},
    {'name': 'mp3', 'ext': 'mp3', 'desc': 'MPEG audio layer 3'},
    {'name': 'wav', 'ext': 'wav', 'desc': 'Waveform Audio'},
    ]

_DEFAULT_EXT = 'flac'

_ENCODER_TAGS = (
                  'encoder',
                  'encoded_by',
                )


@dataclass
class _ExportOptions():
    input_file: str
    output_file: str
    output_format: str
    tags: dict = None
    pitch: float = 1.0
    tempo: float = 1.0
    start: str = None
    end: str = None


@contextmanager
def _in_progress(start_signal, finish_signal):
    try:
        start_signal.emit()
        yield None
    finally:
        finish_signal.emit()


class _Worker(QObject):
    AddToLog = pyqtSignal(str, int)
    Starting = pyqtSignal()
    Finished = pyqtSignal()
    Success = pyqtSignal()

    def _mpv_error_checker(self, evt):
        self._mpv_err = b'unknown error'
        evt_dict = evt.as_dict()
        self._loaded = evt_dict['event'] == b'file-loaded'
        if not self._loaded:
            try:
                self._mpv_err = evt_dict['file_error']
            except KeyError:
                pass
        return True

    def _log_handler(self, level, prefix, text):
        if level == 'warn':
            if 'Estimating duration from bitrate' in text:
                return
            self.AddToLog.emit(f'libmpv: {prefix}: {text}'.rstrip('\n'),
                               lv.LOG_LEVEL_WARNING)
        if level in ['fatal', 'error']:
            self.AddToLog.emit(f'libmpv: {prefix}: {text}'.rstrip('\n'),
                               lv.LOG_LEVEL_ERROR)

    def export(self, export_options: _ExportOptions):
        with _in_progress(self.Starting, self.Finished):
            s = f'\nExport {export_options.input_file}'
            self.AddToLog.emit(s, lv.LOG_LEVEL_NORMAL)
            s = f'     as {export_options.output_file}'
            self.AddToLog.emit(s, lv.LOG_LEVEL_NORMAL)
            if export_options.start:
                s = f'start {export_options.start}'
                self.AddToLog.emit(s, lv.LOG_LEVEL_NORMAL)
            if export_options.end:
                s = f'end   {export_options.end}'
                self.AddToLog.emit(s, lv.LOG_LEVEL_NORMAL)
            s = f'pitch {export_options.pitch:.3f}'
            self.AddToLog.emit(s, lv.LOG_LEVEL_NORMAL)
            s = f'tempo {export_options.tempo:.3f}'
            self.AddToLog.emit(s, lv.LOG_LEVEL_NORMAL)
            s = 'Exporting...'
            self.AddToLog.emit(s, lv.LOG_LEVEL_NORMAL)

            pitch = export_options.pitch
            tempo = export_options.tempo
            pitch_t = pitch / tempo

            mpv_opts = {
                        'video': 'no',
                        'o': export_options.output_file,
                        'of': export_options.output_format,
                        'audio_pitch_correction': 'no',
                        'ocopy_metadata': 'no',
                       }
            if export_options.tags:
                t = export_options.tags
                tagstring = ','.join([f'{k}="{v}"' for k, v in t.items()])
                mpv_opts['oset_metadata'] = tagstring
            if abs(tempo - 1.0) > .0005:
                mpv_opts['speed'] = f'{tempo:.3f}'
            if abs(pitch_t - 1.0) > .0005:
                mpv_opts['af'] = f'@rb:rubberband=pitch-scale={pitch_t:.3f}'
            if export_options.start:
                mpv_opts['start'] = export_options.start
            if export_options.end:
                mpv_opts['end'] = export_options.end

            out_dir = os.path.dirname(export_options.output_file)
            if not os.path.isdir(out_dir):
                s = f'No such directory:  {out_dir}'
                self.AddToLog.emit(s, lv.LOG_LEVEL_ERROR)
                self.AddToLog.emit('Aborting.', lv.LOG_LEVEL_WARNING)
                return

            # Create the file now instead of letting mpv create it to
            # avoid a race condition in existence checking.
            try:
                with open(export_options.output_file, 'x'):
                    pass
            except OSError as err:
                self.AddToLog.emit(str(err), lv.LOG_LEVEL_ERROR)
                self.AddToLog.emit('Aborting.', lv.LOG_LEVEL_WARNING)
                return

            with anal.mpv_cm(log_handler=self._log_handler,
                             **mpv_opts) as (err, player):
                if err is not None:
                    self.AddToLog.emit('Aborting.', lv.LOG_LEVEL_WARNING)
                    return
                with player.prepare_and_wait_for_event(
                                            'file_loaded',
                                             'end_file',
                                             cond=self._mpv_error_checker,
                                             timeout=5):
                    player.command('loadfile',
                               com.string_to_raw(export_options.input_file),
                               'replace')
                if self._loaded:
                    player.wait_for_playback()
            file = export_options.output_file
            if os.path.exists(file) and os.path.getsize(file) > 0:
                self.AddToLog.emit('Done', lv.LOG_LEVEL_NORMAL)
                self.Success.emit()
                return
            self.AddToLog.emit('Export failed', lv.LOG_LEVEL_ERROR)


def _split_extension(path):
    directory, file = os.path.split(path)
    name, dot, ext = file.rpartition('.')
    return (os.path.join(directory, name if name else file), ext)


class _TagEditor(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        model = QStandardItemModel(0, 2, self)
        headers = ('Tag', 'Value')
        model.setHorizontalHeaderLabels(headers)

        vbox = QVBoxLayout()
        self.setLayout(vbox)

        view = QTableView()
        view.setModel(model)
        view.setColumnWidth(0, 200)
        view.setColumnWidth(1, 450)
        view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        view.setSelectionMode(QTableView.SelectionMode.SingleSelection)

        vbox.addWidget(view)

        buttons = QWidget()
        hbox = QHBoxLayout()
        buttons.setLayout(hbox)

        delete_button = QPushButton('Delete selected tag')
        delete_button.clicked.connect(self.delete_tag)
        hbox.addWidget(delete_button)
        add_button = QPushButton('Insert empty tag before selection')
        add_button.clicked.connect(self.insert_before)
        hbox.addWidget(add_button)
        add_button = QPushButton('Insert empty tag after selection')
        add_button.clicked.connect(self.insert_after)
        hbox.addWidget(add_button)

        vbox.addWidget(buttons)

        self.model = model
        self.view = view

    def add_tag(self, tag, value):
        tag_item = QStandardItem(tag)
        value_item = QStandardItem(value)
        self.model.appendRow((tag_item, value_item))

    def insert_before(self):
        indexes = self.view.selectionModel().selectedRows()
        if indexes:
            index = max([x.row() for x in indexes])
        else:
            index = 0
        self.model.insertRow(index)

    def insert_after(self):
        indexes = self.view.selectionModel().selectedRows()
        if indexes:
            index = max([x.row() for x in indexes])
        else:
            index = -1
        self.model.insertRow(index + 1)

    def delete_tag(self):
        indexes = self.view.selectionModel().selectedRows()
        for index in indexes:
            self.model.removeRow(index.row())

    def clear_tags(self):
        self.model.setRowCount(0)

    def tags(self):
        n = self.model.rowCount()
        i = 0
        while i < n:
            k = self.model.item(i, 0).text()
            v = self.model.item(i, 1).text()
            i += 1
            yield (k, v)


class ExportWindow(QWidget):
    """A window that handles exporting audio, including editing tags.
    Inherits from QWidget.

    Parameters
    ----------
    parent
        The parent widget.
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

    Export = pyqtSignal(_ExportOptions)
    """Signal emitted to tell the worker thread to do an export.

    Parameters
    ----------
    _ExportOptions
        The export options.
    """

    Starting = pyqtSignal()
    """Signal emitted when exporting is starting."""

    Finished = pyqtSignal()
    """Signal emitted when exporting is finished."""


    def __init__(self, parent):
        super().__init__(parent)

        self._ext = _DEFAULT_EXT
        self._line_edit_update_needed = False
        self._thread_started = False

        self.setWindowFlag(Qt.WindowType.Window)
        self.setWindowTitle('Export')

        vbox = QVBoxLayout(self)

        self._path_chooser = QWidget()
        self._path_chooser_layout = QHBoxLayout(self._path_chooser)
        self._path_chooser_layout.setContentsMargins(0, 0, 0, 0)
        self._line_edit = QLineEdit()
        self._path_chooser_layout.addWidget(self._line_edit)
        self._path_button = QPushButton('Choose path...')
        self._path_button.clicked.connect(self._choose_path)
        self._path_chooser_layout.addWidget(self._path_button)
        vbox.addWidget(self._path_chooser)

        self._format_chooser = QComboBox()
        for item in _OUTPUT_FORMATS:
            s = f'{item["name"]} ({item["desc"]})'
            self._format_chooser.addItem(s, item)
        vbox.addWidget(self._format_chooser)
        self._format_chooser.currentIndexChanged.connect(self._format_selected)
        self._line_edit.editingFinished.connect(self._text_edited)

        self._option_controls = QWidget()
        self._option_controls_layout = QHBoxLayout(self._option_controls)
        self._start_end = QCheckBox(
            f'Only export between {gcom.OPTION_START} and {gcom.OPTION_END}')
        self._option_controls_layout.addWidget(self._start_end)

        vbox.addWidget(self._option_controls)

        self._tag_editor = _TagEditor()
        vbox.addWidget(self._tag_editor)

        self._buttons = QWidget()
        self._buttons_layout = QHBoxLayout(self._buttons)
        self._buttons_layout.setContentsMargins(0, 0, 0, 0)
        self._close_button = QPushButton('Close')
        self._close_button.setShortcut('Escape')
        self._close_button.clicked.connect(self.hide)
        self._buttons_layout.addWidget(self._close_button)
        self._export_button = QPushButton('Export')
        self._export_button.clicked.connect(self._export,
                                        Qt.ConnectionType.SingleShotConnection)
        self._buttons_layout.addWidget(self._export_button)
        vbox.addWidget(self._buttons)

        self._set_format_from_ext(_DEFAULT_EXT)

        self.resize(720, 400)

    def show(self, original_path, title, options, metadata: dict={}):
        """Show the window, or try to give it focus if it's already
        shown.

        Parameters
        ----------
        original_path : str or QDir
            The path of the original audio file to be exported.
        title : str
            The title of the audio.  This overrides the `title` or
            `TITLE` tag.
        options : audio_tuner_gui.common.Options
            The options set for the audio.
        metadata : dict
            The tags to fill in the tag editor with.  Tags in
            `_ENCODER_TAGS` are ignored, and `title` and `TITLE` tags
            have their value replaced with the value of the title
            parameter.
        """

        if mpv_error is not None:
            self.AddToLog.emit(mpv_error, lv.LOG_LEVEL_ERROR)
            return
        if isinstance(original_path, QDir):
            self._original_path = original_path.path()
        else:
            self._original_path = original_path
        file = os.path.basename(self._original_path)
        self._file_name, self._orig_ext = _split_extension(file)
        self._options = options

        self._line_edit_update_needed = True
        self._update_line_edit()
        if not self._thread_started:
            self._start_worker_thread()

        self._tag_editor.clear_tags()
        if title is not None and not ('title' in metadata
                                      or 'TITLE' in metadata):
            self._tag_editor.add_tag('title', title)
        for tag, value in metadata.items():
            if tag in ('title', 'TITLE'):
                value = title
            if tag not in _ENCODER_TAGS:
                self._tag_editor.add_tag(tag, value)

        super().show()
        self.activateWindow()

    def _start_worker_thread(self):
        worker_thread = QThread(self)
        self._worker_thread = worker_thread
        self._worker = _Worker()
        self._worker.moveToThread(worker_thread)
        self.Export.connect(self._worker.export,
                            Qt.ConnectionType.QueuedConnection)
        self._worker.AddToLog.connect(self._handle_log_message,
                            Qt.ConnectionType.QueuedConnection)
        self._worker.Starting.connect(self._starting,
                            Qt.ConnectionType.QueuedConnection)
        self._worker.Finished.connect(self._finished,
                            Qt.ConnectionType.QueuedConnection)
        self._worker.Success.connect(self._success,
                            Qt.ConnectionType.QueuedConnection)
        worker_thread.start()
        self._thread_started = True

    def _handle_log_message(self, message, level):
        self.AddToLog.emit(message, level)

    def set_dir(self, directory):
        """Set the directory.  This does not immediately update the path
        shown in the line edit widget, but does affect what directory is
        shown the next time it's updated.

        Parameters
        ----------
        directory : str or QDir
            The directory.
        """

        if isinstance(directory, QDir):
            d = directory.path()
        else:
            d = directory
        self._directory = d

    def _export(self):
        output_file = self._line_edit.text()
        output_format = self._format_chooser.currentData()['name']
        pitch = self._options[gcom.OPTION_PITCH]
        tempo = self._options[gcom.OPTION_TEMPO]
        tags = {k: v for k, v in self._tag_editor.tags()}
        export_options = _ExportOptions(input_file=self._original_path,
                                        output_file=output_file,
                                        output_format=output_format,
                                        tags=tags,
                                        pitch=pitch,
                                        tempo=tempo)
        if self._start_end.isChecked():
            export_options.start = self._options[gcom.OPTION_START]
            export_options.end = self._options[gcom.OPTION_END]
        self.Export.emit(export_options)

    def _starting(self):
        self._export_button.setEnabled(False)
        self.Starting.emit()

    def _finished(self):
        self._export_button.clicked.connect(self._export,
                                        Qt.ConnectionType.SingleShotConnection)
        self.Finished.emit()
        self._export_button.setEnabled(True)

    def _success(self):
        self.hide()

    def _set_format_from_ext(self, ext):
        for item in _OUTPUT_FORMATS:
            if item['ext'] == ext:
                s = f'{item["name"]} ({item["desc"]})'
                self._format_chooser.setCurrentText(s)
                return True
        return False

    def _text_edited(self):
        path = self._line_edit.text()
        spath, ext = _split_extension(path)
        if spath:
            directory, self._file_name = os.path.split(spath)
            self.set_dir(directory)
            self._line_edit_update_needed = True
            self._set_format_from_ext(ext)
            if self._line_edit_update_needed:
                self._update_line_edit()

    def _format_selected(self, index):
        self._ext = self._format_chooser.itemData(index)['ext']
        self._update_line_edit()

    def _update_line_edit(self):
        new_file = f'{self._file_name}.{self._ext}'
        new_path = os.path.join(self._directory, new_file)
        self._line_edit.setText(QDir.toNativeSeparators(new_path))
        self._line_edit_update_needed = False

    def _choose_path(self):
        p = os.path.join(self._directory, f'{self._file_name}.{self._ext}')
        path = QFileDialog.getSaveFileName(parent=self,
                                           caption='Choose path',
                                           directory=p)
        spath, ext = _split_extension(path[0])
        if spath:
            directory, self._file_name = os.path.split(spath)
            self.set_dir(directory)
            self._line_edit_update_needed = True
            self._set_format_from_ext(ext)
            if self._line_edit_update_needed:
                self._update_line_edit()

    def quit_thread(self):
        """Stop the worker thread.  Call this before closing the app."""

        if self._thread_started:
            self._worker_thread.quit()
            self._thread_started = False
