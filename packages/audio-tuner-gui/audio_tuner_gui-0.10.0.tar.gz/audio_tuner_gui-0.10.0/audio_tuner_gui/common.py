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


"""Miscellaneous constants and classes for the GUI."""


__author__ = 'Jessie Blue Cassell'


__all__ = [
            'OPTION_TUNING_SYSTEM',
            'OPTION_REF_FREQ',
            'OPTION_REF_NOTE',
            'OPTION_START',
            'OPTION_END',
            'OPTION_LOW_CUT',
            'OPTION_HIGH_CUT',
            'OPTION_DB_RANGE',
            'OPTION_MAX_PEAKS',
            'OPTION_PAD',
            'OPTION_SIZE_EXP',
            'OPTION_SAMPLERATE',
            'OPTION_PITCH',
            'OPTION_BACKENDS',
            'ERROR_SENTINEL',
            'REDO_LEVEL_ALL',
            'REDO_LEVEL_FIND_PEAKS',
            'REDO_LEVEL_TUNING_SYSTEM',
            'REDO_LEVEL_NONE',
            'APP_ICON',
            'ICON_OPTIONS',
            'ICON_FILES',
            'ICON_BACK',
            'ICON_FORWARD',
            'ICON_UP',
            'ICON_HOME',
            'ICON_REMOVE',
            'ICON_CLEAR',
            'ICON_EXIT',
            'ICON_CANCEL',
            'ICON_ABOUT',
            'ICON_MESSAGE_LOG',
            'ICON_ALERT',
            'ICON_PLAYER',
            'ICON_PLAY',
            'ICON_PAUSE',
            'ICON_STOP',
            'ICON_PLAYER_BACK',
            'ICON_PLAYER_FORWARD',
            'ICON_AUDIO_DEVICE',
            'RowData',
            'SplitAction',
            'Options',
          ]


import os
from typing import TypedDict

from PyQt6.QtGui import (
                         QIcon,
                         QAction,
                        )

import audio_tuner.tuning_systems as tuning_systems

from audio_tuner_gui import PKGDIR


# Option names
OPTION_TUNING_SYSTEM = 'Tuning system'
OPTION_REF_FREQ = 'Reference frequency'
OPTION_REF_NOTE = 'Reference note'
OPTION_START = 'Start time'
OPTION_END = 'End time'
OPTION_LOW_CUT = 'Low cut'
OPTION_HIGH_CUT = 'High cut'
OPTION_DB_RANGE = 'dB range'
OPTION_MAX_PEAKS = 'Max peaks'
OPTION_PAD = 'Pad input'
OPTION_SIZE_EXP = 'FFT size exponent'
OPTION_SAMPLERATE = 'Sample rate'
OPTION_BACKENDS = 'backends'
OPTION_PITCH = 'Pitch correction factor'
OPTION_TEMPO = 'Tempo correction factor'

ERROR_SENTINEL = 'ERROR'

REDO_LEVEL_ALL = 3
REDO_LEVEL_FIND_PEAKS = 2
REDO_LEVEL_TUNING_SYSTEM = 1
REDO_LEVEL_NONE = 0

APP_ICON = os.path.join(PKGDIR, 'icons/audio_tuner_icon.svg')

# These are missing from ThemeIcon
ICON_OPTIONS = os.path.join(PKGDIR, 'icons/preferences-other.png')
ICON_FILES = os.path.join(PKGDIR, 'icons/folder.png')

# This one is in ThemeIcon but not on Windows for some reason
ICON_CANCEL = os.path.join(PKGDIR, 'icons/process-stop.png')

LOGO_LIGHT = os.path.join(PKGDIR, 'icons/audio_tuner_logo_light.svg')
LOGO_DARK = os.path.join(PKGDIR, 'icons/audio_tuner_logo_dark.svg')
BRAINMADE_WHITE = os.path.join(PKGDIR, 'icons/white-logo.svg')
BRAINMADE_BLACK = os.path.join(PKGDIR, 'icons/black-logo.svg')
GPL_WHITE = os.path.join(PKGDIR, 'icons/gpl-v3-logo_white.svg')
GPL_RED = os.path.join(PKGDIR, 'icons/gpl-v3-logo_red.svg')

try:
    ICON_BACK = QIcon.ThemeIcon.GoPrevious
    ICON_FORWARD = QIcon.ThemeIcon.GoNext
    ICON_UP = QIcon.ThemeIcon.GoUp
    ICON_HOME = QIcon.ThemeIcon.GoHome
    ICON_REMOVE = QIcon.ThemeIcon.EditDelete
    ICON_CLEAR = QIcon.ThemeIcon.EditDelete
    ICON_EXIT = QIcon.ThemeIcon.ApplicationExit
#   ICON_OPTIONS = 'preferences-other'
#   ICON_CANCEL = QIcon.ThemeIcon.ProcessStop
    ICON_ABOUT = QIcon.ThemeIcon.HelpAbout
    ICON_MESSAGE_LOG = QIcon.ThemeIcon.FormatJustifyLeft
#   ICON_FILES = 'folder'
    ICON_ALERT = QIcon.ThemeIcon.DialogWarning
    ICON_PLAYER = QIcon.ThemeIcon.MultimediaPlayer
    ICON_PLAY = QIcon.ThemeIcon.MediaPlaybackStart
    ICON_PAUSE =  QIcon.ThemeIcon.MediaPlaybackPause
    ICON_STOP = QIcon.ThemeIcon.MediaPlaybackStop
    ICON_PLAYER_BACK = QIcon.ThemeIcon.MediaSeekBackward
    ICON_PLAYER_FORWARD = QIcon.ThemeIcon.MediaSeekForward
    ICON_AUDIO_DEVICE = QIcon.ThemeIcon.AudioCard
except AttributeError:
    ICON_BACK = 'go-previous'
    ICON_FORWARD = 'go-next'
    ICON_UP = 'go-up'
    ICON_HOME = 'go-home'
    ICON_REMOVE = 'edit-delete'
    ICON_CLEAR = 'edit-delete'
    ICON_EXIT = 'application-exit'
#   ICON_OPTIONS = 'preferences-other'
#   ICON_CANCEL = 'process-stop'
    ICON_ABOUT = 'help-about'
    ICON_MESSAGE_LOG = 'format-justify-left'
#   ICON_FILES = 'folder'
    ICON_ALERT = 'dialog-warning'
    ICON_PLAYER = 'multimedia-player'
    ICON_PLAY = 'media-playback-start'
    ICON_PAUSE = 'media-playback-pause'
    ICON_STOP = 'media-playback-stop'
    ICON_PLAYER_BACK = 'media-seek-backward'
    ICON_PLAYER_FORWARD = 'media-seek-forward'
    ICON_AUDIO_DEVICE = 'audio-card'


class RowData(TypedDict):
    """This is the type of the dicts used to send data to the result
    rows in the display.

    Keys
    ----
    note : str
        The name of the note.
    standard : float
        The frequency of the note as defined by the tuning system.
    measured : float
        The actual measured frequency of the note.
    cents : float
        The discrepancy in cents.
    correction : float
        The correction factor needed to make the note match the
        standard.
    """

    note: str
    standard: float
    measured: float
    cents: float
    correction: float


class SplitAction():
    """A class that's two QActions in one.  One is for menu items and
    includes a title, and the other is for buttons and doesn't.  Useful
    for avoiding unwanted tooltips on buttons while still having a title
    available for menus.  It's sort of a drop in replacement for
    QAction, but not quite, since not all the methods are implemented
    and `triggered.connect` is changed to `triggered_connect`.

    Parameters
    ----------
    title : str
        The title of the menu version of the QAction.

    All other parameters are passed to the QAction constructors.
    """

    def __init__(self, title, *args, **kwargs):
        self.menu_action = QAction(title, *args, **kwargs)
        self.button_action = QAction(*args, **kwargs)

    def menu(self):
        """Return the menu version of the QAction."""

        return self.menu_action

    def button(self):
        """Return the button version of the QAction."""

        return self.button_action

    def setIcon(self, *args, **kwargs):
        """Call the `setIcon` method of both QActions."""

        self.menu_action.setIcon(*args, **kwargs)
        self.button_action.setIcon(*args, **kwargs)

    def setShortcut(self, s):
        """Call the `setShortcut` method of only the menu QAction."""

        self.menu_action.setShortcut(s)

    def setEnabled(self, e):
        """Call the `setEnabled` method of both QActions."""

        self.menu_action.setEnabled(e)
        self.button_action.setEnabled(e)

    def setStatusTip(self, s):
        """Call the `setStatusTip` method of both QActions."""

        self.menu_action.setStatusTip(s)
        self.button_action.setStatusTip(s)

    def triggered_connect(self, *args, **kwargs):
        """Call `triggered.connect` on both QActions."""

        self.menu_action.triggered.connect(*args, **kwargs)
        self.button_action.triggered.connect(*args, **kwargs)


class Options(dict):
    """A dictionary subclass for storing options.

    Parameters
    ----------
    args : argparse.Namespace
        The namespace object resulting from calling
        audio_tuner.argument_parser.merge_args.  Used to initialize the
        options.
    
    Attributes
    ----------
    tuning_system
        An instance of one of the tuning systems defined in
        audio_tuner.tuning_systems.  Which one it is depends on the
        value associated with the OPTION_TUNING_SYSTEM key.  Only
        available after `init_tuning_system` has been called.
    """

    def __init__(self, args):
        super().__init__()
        self[OPTION_TUNING_SYSTEM] = self._guify_tuning_system(args.tuning)
        self[OPTION_REF_FREQ] = args.ref_freq
        self[OPTION_REF_NOTE] = args.ref_note
        self[OPTION_START] = args.start
        self[OPTION_END] = args.end
        self[OPTION_LOW_CUT] = args.low_cut
        self[OPTION_HIGH_CUT] = args.high_cut
        self[OPTION_DB_RANGE] = args.dB_range
        self[OPTION_MAX_PEAKS] = args.max_peaks
        self[OPTION_PAD] = not args.nopad
        self[OPTION_SIZE_EXP] = args.size_exp
        self[OPTION_SAMPLERATE] = args.samplerate
        self[OPTION_BACKENDS] = args.backends
        self[OPTION_PITCH] = 1.0
        self[OPTION_TEMPO] = 1.0

    def _guify_tuning_system(self, tuning_system):
        return tuning_system.replace('_', ' ').title()

    def redo_level(self, old_options):
        """Compare the options stored in this instance of Options to the
        options stored in an older one to find out how much analysis
        needs to be redone.

        Parameters
        ----------
        old_options : Options
            The old Options instance.

        Returns
        -------
        int
            The redo level.
        """

        if (old_options is None
         or self[OPTION_START] != old_options[OPTION_START]
         or self[OPTION_END] != old_options[OPTION_END]
         or self[OPTION_PAD] != old_options[OPTION_PAD]
         or self[OPTION_SIZE_EXP] != old_options[OPTION_SIZE_EXP]
         or self[OPTION_BACKENDS] != old_options[OPTION_BACKENDS]
         or self[OPTION_SAMPLERATE] != old_options[OPTION_SAMPLERATE]):
            return REDO_LEVEL_ALL
        if (self[OPTION_LOW_CUT] != old_options[OPTION_LOW_CUT]
         or self[OPTION_HIGH_CUT] != old_options[OPTION_HIGH_CUT]
         or self[OPTION_DB_RANGE] != old_options[OPTION_DB_RANGE]
         or self[OPTION_MAX_PEAKS] != old_options[OPTION_MAX_PEAKS]):
            return REDO_LEVEL_FIND_PEAKS
        if (self[OPTION_TUNING_SYSTEM] != old_options[OPTION_TUNING_SYSTEM]
         or self[OPTION_REF_FREQ] != old_options[OPTION_REF_FREQ]
         or self[OPTION_PITCH] != old_options[OPTION_PITCH]
         or self[OPTION_REF_NOTE] != old_options[OPTION_REF_NOTE]):
            return REDO_LEVEL_TUNING_SYSTEM

        return REDO_LEVEL_NONE

    def init_tuning_system(self):
        """Initialize the tuning system and store it as the
        `tuning_system` attribute.
        """

        ref_note = self[OPTION_REF_NOTE]
        ref_freq = self[OPTION_REF_FREQ]
        if ref_freq == ERROR_SENTINEL:
            self.tuning_system = None
        elif self[OPTION_TUNING_SYSTEM] == 'Equal Temperament':
            self.tuning_system = tuning_systems.EqualTemperament(
                                                            ref_note=ref_note,
                                                            ref_freq=ref_freq)
        elif self[OPTION_TUNING_SYSTEM] == 'Pythagorean':
            self.tuning_system = tuning_systems.Pythagorean(
                                                       ref_note=ref_note,
                                                       ref_freq=ref_freq)
