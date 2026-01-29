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


"""Audio player for the GUI."""


__author__ = 'Jessie Blue Cassell'


__all__ = [
            'Player',
          ]


import atexit

from PyQt6.QtCore import (
                          Qt,
                          QObject,
                          pyqtSignal,
                         )
from PyQt6.QtWidgets import (
                             QWidget,
                             QVBoxLayout,
                             QHBoxLayout,
                             QPushButton,
                             QTableView,
                            )
from PyQt6.QtGui import (
                         QStandardItemModel,
                         QStandardItem,
                        )

import audio_tuner_gui.log_viewer as lv
import audio_tuner.common as com

mpv_error = com.mpv_error
if mpv_error is None:
    import mpv


class _DeviceView(QTableView):
    def __init__(self):
        super().__init__()

        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.setShowGrid(False)


class _DeviceWindow(QWidget):
    Select = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowFlag(Qt.WindowType.Window)
        self.setWindowTitle('Audio Devices')

        self.vbox = QVBoxLayout(self)

        self._init_device_view()

        self.vbox.addWidget(self.view)

        self._init_button_panel()
        self.vbox.addWidget(self.button_panel)

        self.resize(600, 400)

    def _init_device_view(self):
        model = QStandardItemModel(0, 2, self)
        headers = ('Name', 'Description')
        model.setHorizontalHeaderLabels(headers)

        view = _DeviceView()
        view.setModel(model)

        view.setColumnWidth(0, 200)
        view.setColumnWidth(1, 400)

        self.model = model
        self.view = view

    def _init_button_panel(self):
        self.button_panel = QWidget()
        self.hbox = QHBoxLayout(self.button_panel)

        self.cancel_button = QPushButton('Cancel')
        self.cancel_button.setShortcut('Esc')
        self.hbox.addWidget(self.cancel_button)
        self.cancel_button.clicked.connect(self.close)

        self.select_button = QPushButton('OK')
        self.select_button.setShortcut('Return')
        self.hbox.addWidget(self.select_button)
        self.select_button.clicked.connect(self.select)

    def set_device_list(self, devices, current_device):
        self.model.setRowCount(0)
        selection = None
        for i, device in enumerate(devices):
            name = device['name']
            description = device['description']
            if name == current_device:
                selection = i
            name_item = QStandardItem(name)
            description_item = QStandardItem(description)
            self.model.appendRow((name_item, description_item))
        if selection is not None:
            self.view.selectRow(selection)

    def select(self):
        row = self.view.selectedIndexes()[0].row()
        name = self.model.item(row, 0).text()
        self.Select.emit(name)
        self.close()

    def close(self):
        self.hide()



def _hms_to_seconds(time):
    hrmin, c, sec = time.rpartition(':')
    hr, c, minute = hrmin.rpartition(':')

    if hr:
        hrf = float(hr)
    else:
        hrf = 0
    if minute:
        minutef = float(minute)
    else:
        minutef = 0
    if sec:
        secf = float(sec)
    else:
        secf = 0

    minutef += hrf * 60
    secf += minutef * 60

    return secf


class Player(QObject):
    """Audio player that uses libmpv as a backend.  Inherits from
    QObject.  It plays audio from the start position to the end position
    with pitch and tempo correction, with the `start`, `end`, `pitch`
    and `tempo` parameters set by the `play` and `update_corrections`
    methods.

    Parameters
    ----------
    parent
        The parent widget.

    Attributes
    ----------
    time_number : int
        The total number of times a TickPos or TickRem signal has been
        emitted.  This can be used for diagnostic purposes.  If it
        increases too much faster than 60 times per second, libmpv may
        be misbehaving.
    """

    TickPos = pyqtSignal(bool, int)
    """Signal emitted when the time from the beginning of the audio
    changes.  Although it has one second resolution, it may be emitted
    more than once per second.  The exact rate is controlled by libmpv.
    Note that this is the time from the beginning of the audio, not the
    `start` position.  If tempo correction is applied, it won't change
    the time, but it will tick at a rate other than 1 second per second.

    Parameters
    ----------
    bool
        True if audio is loaded and the time is valid, False otherwise.
    int
        The time in seconds.
    """

    TickRem = pyqtSignal(bool, int)
    """Signal emitted when the time remaining to the end of the audio
    changes.  Although it has one second resolution, it may be emitted
    more than once per second.  The exact rate is controlled by libmpv.
    Note that this is the time to the end of the audio, not the `end`
    position.  If tempo correction is applied, it won't change the time,
    but it will tick at a rate other than 1 second per second.

    Parameters
    ----------
    bool
        True if audio is loaded and the time is valid, False otherwise.
    int
        The time in seconds.
    """

    Percent = pyqtSignal(int)
    """Signal emitted to indicate the position in the audio as a
    percentage.  Unlike TickPos and TickRem, this does take into account
    the `start` and `end` positions, so it will progresses from 0% to
    100% even if `start` to `end` only covers a small portion of the
    audio.
    
    Parameters
    ----------
    int
        The percentage
    """

    PauseStatus = pyqtSignal(bool)
    """Signal emitted when the pause status changes.

    Parameters
    ----------
    bool
        True if paused, False otherwise.
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

    def __init__(self, parent):
        super().__init__()

        self._player = None

        self._time_pos = None
        self._time_rem = None
        self.time_number = 0

        self._pitch_t = 1.0
        self._pitch = 1.0
        self._tempo = 1.0
        self._start = None
        self._end = None
        self._duration = None

        self._start_percent = 0

        self._device = 'auto'

        self._device_window = _DeviceWindow(parent)
        self._device_window.Select.connect(self.set_device)

        atexit.register(self._stop_player)

    def _player_time_to_percent(self, time: str, endmode: bool=False):
        p = None

        if time is None:
            time = 'none'

        time = time.strip(' ')
        if time.startswith('-'):
            time = time.lstrip('-')
            negative = True
        else:
            negative = False

        if time == 'none':
            return 100.0 if endmode else 0.0

        if time.endswith('%'):
            try:
                p = float(time.rstrip('%'))
            except ValueError:
                return None

        elif d := self.get_duration():
            try:
                secf = _hms_to_seconds(time)
            except ValueError:
                return None
            p = 100.0 * (secf / d)

        if p:
            if negative:
                return 100 - p
            else:
                return p

        return None

    def _player_time_to_seconds(self, time: str, endmode: bool=False):
        p = None
        d = self.get_duration()

        if time is None:
            time = 'none'

        time = time.strip(' ')
        if time.startswith('-'):
            time = time.lstrip('-')
            negative = True
        else:
            negative = False

        if time == 'none':
            return d if endmode else 0.0

        if time.endswith('%'):
            try:
                p = float(time.rstrip('%'))
            except ValueError:
                return None
            secf = (p / 100.0) * d

        else:
            try:
                secf = _hms_to_seconds(time)
            except ValueError:
                return None

        if secf:
            if negative:
                return d - secf
            else:
                return secf

        return None

    def _percent_player_to_slider(self, percent):
        if self._player is not None:
            start = self._start
            end = self._end

            startf = self._player_time_to_percent(start)
            endf = self._player_time_to_percent(end, endmode=True)
            if startf is None or endf is None:
                return percent

            ret = (percent - startf) * (100.0 / (endf - startf))
            return max(0.0, min(100.0, ret))

    def _percent_slider_to_player(self, percent):
        if self._player is not None:
            start = self._start
            end = self._end

            startf = self._player_time_to_percent(start)
            endf = self._player_time_to_percent(end, endmode=True)
            if startf is None or endf is None:
                return percent

            ret = (percent * (endf - startf)) / 100 + startf
            return max(0.0, min(100.0, ret))

    def _ensure_player_is_running(self,
                                  pitch=1.0,
                                  tempo=1.0,
                                  start=None,
                                  end=None):
        if mpv_error is not None:
            self.AddToLog.emit(mpv_error, lv.LOG_LEVEL_ERROR)
            raise OSError

        if self._player is not None and self._player.core_shutdown:
            self._unobserve()
            self._player.terminate()
            self._player = None
        if self._player is None:
            pitch_t = pitch / tempo
            self._pitch_t = pitch_t
            self._pitch = pitch
            self._tempo = tempo
            mpv_opts = {
                        'audio_pitch_correction': 'no',
                        'keep_open': 'yes',
                        'audio_device': self._device,
                        'audio_fallback_to_null': 'yes',
                        'af': f'@rb:rubberband=pitch-scale={pitch_t:.3f}',
                        'speed': f'{tempo:.3f}'
                       }
            if start:
                mpv_opts['start'] = start
                self._start = start
            if end:
                mpv_opts['end'] = end
                self._end = end
            self._player = mpv.MPV(**mpv_opts)

            if self._player.audio_device == 'null':
                s = f'Unable to open output device {self._device}'
                self.AddToLog.emit(s, lv.LOG_LEVEL_ERROR)

            self._player.observe_property('time-pos',
                                          self._time_pos_observer)
            self._player.observe_property('time-remaining',
                                          self._time_rem_observer)
            self._player.observe_property('percent-pos',
                                          self._percent_observer)
            self._player.observe_property('pause',
                                          self._pause_observer)

    def _unobserve(self):
        if self._player is not None:
            try:
                self._player.unobserve_property('time-pos',
                                                self._time_pos_observer)
            except ValueError as err:
                self.AddToLog.emit(str(err), lv.LOG_LEVEL_ERROR)
            try:
                self._player.unobserve_property('time-remaining',
                                                self._time_rem_observer)
            except ValueError as err:
                self.AddToLog.emit(str(err), lv.LOG_LEVEL_ERROR)
            try:
                self._player.unobserve_property('percent-pos',
                                                self._percent_observer)
            except ValueError as err:
                self.AddToLog.emit(str(err), lv.LOG_LEVEL_ERROR)
            try:
                self._player.unobserve_property('pause',
                                                self._pause_observer)
            except ValueError as err:
                self.AddToLog.emit(str(err), lv.LOG_LEVEL_ERROR)

    def _restart_mpv(self, pitch=1.0, tempo=1.0, start=None, end=None):
        if self._player is None:
            self._ensure_player_is_running(pitch, tempo, start, end)
        else:
            path = com.raw_to_string(self._player.raw.path)
            pause = self._player.pause
            time_pos = self._player.time_pos

            self._stop_player()

            if path is not None:
                self.play(path, pitch, tempo, start, end)
                self._player.pause = pause
                self._player.time_pos = time_pos
            else:
                self._ensure_player_is_running(pitch, tempo, start, end)
                self._player.pause = pause

    def update_corrections(self, pitch=None, tempo=None, start=None, end=None):
        """Update the pitch correction, tempo correction, start time and
        end time.  See the `--start` option in the `mpv` manpage to find
        out how to format the `start` and `end` parameters.

        Parameters
        ----------
        pitch : float, optional
            Pitch correction factor.  Default None.
        tempo : float, optional
            Tempo correction factor.  Default None.
        start : str, optional
            The position to start playing at.  If None, start at the
            beginning.  This causes a seek iff the starting position set
            is after the current position.  Default None.
        end : str, optional
            The position to stop playing at.  If None, end at the end.
            Default None.
        """

        if self._player is not None:
            if pitch is None and tempo is None:
                self._update_start_end(start, end)
                return

            if pitch is None:
                pitch = self._pitch
            else:
                self._pitch = pitch
            if tempo is None:
                tempo = self._tempo
            pitch_t = pitch / tempo
            try:
                if abs(pitch_t - self._pitch_t) > .0011:
                    self._player.af_command('rb',
                                            'set-pitch',
                                            f'{pitch_t:.3f}')
                    self._pitch_t = pitch_t
                if abs(tempo - self._tempo) > .0011:
                    self._player.speed = f'{tempo:.3f}'
                    self._tempo = tempo
                self._update_start_end(start, end)
            except SystemError:
                self._restart_mpv(pitch, tempo, start, end)

    def _update_start_end(self, start, end):
        if self._player is not None:
            try:
                if start:
                    self._player.start = start
                    self._start = start
                else:
                    self._player.start = 'none'
                    self._start = None
                if end:
                    self._player.end = end
                    self._end = end
                else:
                    self._player.end = 'none'
                    self._end = None
            except SystemError:
                self._restart_mpv(self._pitch, self._tempo, start, end)

            minimum = self._player_time_to_seconds(self._start)
            try:
                if self._player.time_pos < minimum:
                    self._player.time_pos = minimum
            except TypeError:
                pass

    def play(self,
             path: str,
             duration=None,
             pitch=1.0,
             tempo=1.0,
             start=None,
             end=None):
        """Load an audio file and play it.

        Parameters
        ----------
        path : str
            The path to the audio file.
        duration : int, optional
            The duration of the audio in the file.  If this is not set,
            the duration will be estimated by libmpv, which may be
            inaccurate.
        pitch : float, optional
            Pitch correction factor.  Default 1.0.
        tempo : float, optional
            Tempo correction factor.  Default 1.0.
        start : str, optional
            The position to start playing at.  If None, start at the
            beginning.  Default None.
        end : str, optional
            The position to stop playing at.  If None, end at the end.
            Default None.
        """

        self._ensure_player_is_running(pitch, tempo, start, end)

        self.update_corrections(pitch, tempo, start, end)

        if self.get_currently_playing() is not None:
            self.stop()

        self._duration = duration

        if self._start_percent == 0:
            self._player.command('loadfile',
                                 com.string_to_raw(path),
                                 'replace')
        else:
            p = self._percent_slider_to_player(self._start_percent)
            self._player.command('loadfile',
                                 com.string_to_raw(path),
                                 'replace',
                                 f'start={p}%')
            self._start_percent = 0

    def stop(self):
        """Stop playing and unload the file."""

        if self._player is not None:
            self._player.stop()

    def toggle_pause(self):
        """Pause if unpaused, unpause if paused."""

        if self._player is not None:
            self._player.cycle('pause')

    def set_pause(self, pause):
        """Set the pause state.

        Parameters
        ----------
        pause : bool
            Pause if True, unpause if False.
        """

        if self._player is not None:
            self._player.pause = pause

    def _pause_observer(self, name, value):
        self.PauseStatus.emit(value)

    def get_currently_playing(self):
        """Get the path of the currently loaded file.

        Returns
        -------
        str
            The path of the file.
        """

        if self._player is None:
            return None
        else:
            return com.raw_to_string(self._player.raw.path)

    def get_duration(self):
        """Get the duration of the audio in the currently loaded file.

        Returns
        -------
        float
            The duration in seconds.
        """

        if self._player is None:
            return None
        if not self._duration:
            self._duration = self._player.duration
        return self._duration

    def _time_pos_observer(self, name, value):
        self.time_number += 1
        try:
            cur_time = int(value)
            if cur_time != self._time_pos:
                self._time_pos = cur_time
                self.TickPos.emit(True, cur_time)
        except TypeError:
            self._time_pos = None
            self.TickPos.emit(False, 0)

    def _time_rem_observer(self, name, value):
        self.time_number += 1
        try:
            cur_time = int(value + .9)
            if cur_time != self._time_rem:
                self._time_rem = cur_time
                self.TickRem.emit(True, cur_time)
        except TypeError:
            self._time_rem = None
            self.TickRem.emit(False, 0)

    def _percent_observer(self, name, value):
        if value is None:
            self.Percent.emit(0)
        else:
            self.Percent.emit(int(self._percent_player_to_slider(value)))

    def set_percent(self, percent):
        """Set the playback position as a percentage.  The percentage
        works the same as in the `Percent` signal, so 0% sets it to
        whatever position `start` is set to and 100% sets it to whatever
        position `end` is set to.

        Parameters
        ----------
        percent : numeric type
            The percentage.
        """

        if self._player is not None and self._player.raw.path is not None:
            self._player.percent_pos = self._percent_slider_to_player(percent)
        else:
            self._start_percent = percent

    def back(self, amount=10.0):
        """Seek backwards.  If that would put the play position before
        `start`, it goes to `start` instead.

        Parameters
        ----------
        amount : float, optional
            The amount of time to seek in seconds.  Default 10.
        """

        if self._player is not None:
            minimum = self._player_time_to_seconds(self._start)
            if minimum is not None:
                new = max(self._time_pos - amount, minimum)
                self._player.time_pos = new

    def forward(self, amount=10.0):
        """Seek forwards.  If that would put the play position after
        `end`, it goes to `end` instead.

        Parameters
        ----------
        amount : float, optional
            The amount of time to seek in seconds.  Default 10.
        """

        if self._player is not None:
            self._player.seek(amount)

    def get_current_position(self):
        """Get the current play position, or None if the player is not
        running.

        Returns
        -------
        float
            The play position.
        """

        if self._player is not None:
            return self._player.time_pos

    def show_device_window(self):
        """Open a window where  the user can select an audio output
        device.
        """

        self._ensure_player_is_running()
        self._device_window.set_device_list(self._player.audio_device_list,
                                            self._player.audio_device)
        self._device_window.show()

    def set_device(self, device):
        """Set the audio output device.

        Parameters
        ----------
        device : str
            The device.  See `--audio-device` in the mpv manpage for a
            description of what to put here.
        """

        self._device = device
        if self._player is not None:
            self._player.audio_device = device

    def _stop_player(self):
        if self._player is not None:
            self._unobserve()
            self._player.command('quit')
            self._player.terminate()
            self._player = None
