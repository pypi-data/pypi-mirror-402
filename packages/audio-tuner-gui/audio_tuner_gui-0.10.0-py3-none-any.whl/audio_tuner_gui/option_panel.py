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


"""Option panel for the GUI."""


__author__ = 'Jessie Blue Cassell'


__all__ = [
            'OptionPanel',
          ]


from PyQt6.QtCore import (
                          pyqtSignal,
                         )
from PyQt6.QtWidgets import (
                             QWidget,
                             QPushButton,
                             QVBoxLayout,
                             QHBoxLayout,
                             QLineEdit,
                             QSizePolicy,
                             QCheckBox,
                             QScrollArea,
                             QLabel,
                             QGridLayout,
                             QComboBox,
                             QSpinBox,
                             QDoubleSpinBox,
                             QFrame,
                             QToolButton,
                            )
from PyQt6.QtGui import (
                         QColor,
                         QPalette,
                        )

import audio_tuner.tuning_systems as tuning_systems
import audio_tuner.common as com
import audio_tuner_gui.common as gcom


class _OptionLineEdit(QWidget):
    def __init__(self, label, unit=None, none_sentinel=None):
        super().__init__()

        self.none_sentinel = none_sentinel

        self.error_condition = False
        self.label = QLabel(label)
        self.label.setSizePolicy(QSizePolicy())
        self.default = None

        if unit is None:
            self.bottom = self.init_main_widget()
            self.bottom.setSizePolicy(QSizePolicy())
            self.widget = self.bottom
        else:
            self.bottom = QWidget()
            self.hbox = QHBoxLayout(self.bottom)
            self.widget = self.init_main_widget()
            self.widget.setSizePolicy(QSizePolicy())

            self.init_unit(unit)

            self.hbox.addWidget(self.widget)
            self.hbox.addWidget(self.unit)
            self.hbox.addStretch()
            self.hbox.setContentsMargins(0, 0, 0, 0)

        self.vbox = QVBoxLayout(self)
        self.vbox.addStretch()
        self.vbox.addWidget(self.label)
        self.vbox.addWidget(self.bottom)
        self.vbox.addStretch()

        self.orig_palette = self.palette()

    def init_main_widget(self):
        line_edit = QLineEdit()
        line_edit.editingFinished.connect(self._edit_finished)
        return line_edit

    def init_unit(self, unit):
        self.unit = QLabel(unit)
        self.unit.setSizePolicy(QSizePolicy())

    def _edit_finished(self):
        selection = self.widget.text()
        if self.default and (selection is None or selection == ''):
            self.set(self.default)

    def set(self, selection):
        if self.none_sentinel is not None and selection is None:
            selection = self.none_sentinel
        self.widget.setText(selection)
        self.unset_error()

    def get(self):
        self.unset_error()
        ret = self.widget.text().strip()
        if self.none_sentinel is not None and ret == self.none_sentinel:
            ret = None
        return ret

    def set_error(self):
        self.error_condition = True
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 0, 0))
        self.setPalette(palette)
        self.widget.setFocus()

    def unset_error(self):
        if self.error_condition:
            self.error_condition = False
            self.setPalette(self.orig_palette)


class _OptionStartEnd(_OptionLineEdit):
    button_clicked = pyqtSignal()

    def init_unit(self, unit):
        self.unit = QToolButton()
        self.unit.setText('Set to now')
        self.unit.setStatusTip('Set to current position')
        self.unit.setEnabled(False)
        self.unit.clicked.connect(self.button_clicked.emit)

    def _edit_finished(self):
        selection = self.widget.text()
        if self.none_sentinel and (selection is None or selection == ''):
            self.set(self.none_sentinel)

    def get(self) -> str:
        self.unset_error()
        ret = self.widget.text().replace('#', '').strip()
        if self.none_sentinel is not None and ret == self.none_sentinel:
            ret = None
        return ret


class _OptionCheckBox(QWidget):
    def __init__(self, label):
        super().__init__()

        self.vbox = QVBoxLayout(self)
        self.widget = QCheckBox(label)
        self.vbox.addWidget(self.widget)
        self.vbox.setContentsMargins(15, 5, 5, 5)

    def set(self, selection):
        self.widget.setChecked(selection)

    def get(self):
        return self.widget.isChecked()


class _OptionFloatLineEdit(_OptionLineEdit):
    def set(self, selection):
        super().set(str(selection))

    def get(self):
        try:
            ret = float(super().get())
            if ret <= 0:
                raise ValueError
        except ValueError:
            self.set_error()
            return gcom.ERROR_SENTINEL
        return ret


class _OptionIntSpinBox(_OptionLineEdit):
    def init_main_widget(self):
        widget = QSpinBox()
        widget.setMinimum(1)

        self._revert_to_default = False
        widget.lineEdit().textEdited.connect(self._text_edited)
        widget.lineEdit().editingFinished.connect(self._edit_finished)

        return widget

    def _edit_finished(self):
        if self.default and self._revert_to_default:
            self.set(self.default)
        self._revert_to_default = False

    def _text_edited(self, text):
        if text == '':
            self._revert_to_default = True
        else:
            self._revert_to_default = False

    def set(self, selection):
        self.widget.setValue(selection)
        self.unset_error()

    def get(self):
        self.unset_error()
        try:
            ret = self.widget.value()
            if ret <= 0:
                raise ValueError
        except ValueError:
            self.set_error()
            return gcom.ERROR_SENTINEL
        return ret


class _OptionFloatSpinBox(_OptionIntSpinBox):
    def init_main_widget(self):
        widget = QDoubleSpinBox()
        widget.setDecimals(3)
        widget.setMinimum(0.25)
        widget.setMaximum(4.0)
        widget.setSingleStep(.001)

        self._revert_to_default = False
        widget.lineEdit().textEdited.connect(self._text_edited)
        widget.lineEdit().editingFinished.connect(self._edit_finished)

        return widget

    def set(self, selection):
        super().set(selection)
        self._precise_value = selection

    def get_precise(self):
        imprecise = super().get()
        if (imprecise != gcom.ERROR_SENTINEL
          and abs(imprecise - self._precise_value) < .0006):
            return self._precise_value
        else:
            return imprecise


def _prettify(text):
    text = text.replace('b', tuning_systems.flat_symbol)
    text = text.replace('#', tuning_systems.sharp_symbol)
    return text


class _OptionRefnoteLineEdit(_OptionLineEdit):
    def get(self):
        text = self.widget.text().strip()
        text = text.capitalize()
        text = _prettify(text)
        self.set(text)
        return text

    def set(self, selection):
        super().set(_prettify(selection))


class _OptionComboBox(_OptionLineEdit):
    def __init__(self, label, items):
        self.items = items
        super().__init__(label)

    def init_main_widget(self):
        widget = QComboBox()
        widget.addItems(self.items)
        return widget

    def set(self, selection):
        self.widget.setCurrentText(selection)

    def get(self):
        return self.widget.currentText()


class OptionPanel(QWidget):
    """Panel full of option widgets.  Inherits from QWidget.  Includes a
    `Hold` checkbox to hold options at their current values, a `Revert
    to defaults` button and an `Apply to selected` button.  The user can
    request that an individual widget return to it's default value by
    setting it's line edit box to a blank value (this only works for
    widgets that actually have a line edit box, and only if the widget's
    `default` attribute has been set, which can be done using the
    `is_defaults` parameter of the `set_options` method (The
    `set_default_options` convenience method, which is what the `Revert
    to defaults` button is connected to, does this automatically)).

    Parameters
    ----------
    args : argparse.Namespace
        Stores the default options which the `set_default_options`
        method uses.  Note that the defaults aren't actually set until
        `set_default_options` is called.

    Attributes
    ----------
    widgets : dict
        The widgets.  The keys are the option names defined in
        audio_tuner_gui.common.
    """

    PushOptions = pyqtSignal(gcom.Options, bool)
    """Signal emitted when the user pushes a button to request that
    options be applied to the selected analyzed audio.

    Parameters
    ----------
    audio_tuner_gui.common.Options
        The options to apply.
    """

    PitchChange = pyqtSignal(float)
    """Signal emitted when the value in the pitch correction widget
    changes.

    Parameters
    ----------
    float
        The new pitch correction value.
    """

    PayAttentionToMe = pyqtSignal()
    """Signal emitted to request that the option panel be made visible
    if it isn't already.
    """


    def __init__(self, args):
        super().__init__()

        self._args = args
        self._link_ok = True

        self._init_option_area()
        self._init_buttons()

        vbox = QVBoxLayout(self)
        vbox.addWidget(self._scroll_area)
        vbox.addWidget(self._button_panel)
        vbox.setSpacing(5)
        vbox.setContentsMargins(3, 3, 3, 3)

        self._default_options = gcom.Options(args)

    def _init_option_area(self):
        self.widgets = {}

        self._scroll_area = QScrollArea()
        self._panel = QWidget()
        self._grid = QGridLayout(self._panel)

        box_widget = QWidget()
        hbox = QHBoxLayout(box_widget)

        # pitch correction
        title = gcom.OPTION_PITCH
        widget = _OptionFloatSpinBox(title)
        hbox.addWidget(widget)
        self.widgets[title] = widget

        # Link button
        widget = QToolButton()
        widget.setText('&Link')
        widget.setCheckable(True)
        hbox.addWidget(widget)
        self._link = widget

        # tempo correction
        title = gcom.OPTION_TEMPO
        widget = _OptionFloatSpinBox(title)
        hbox.addWidget(widget)
        self.widgets[title] = widget

        self._grid.addWidget(box_widget, 0, 0, 1, 2)

        keybox = QWidget()
        khbox = QHBoxLayout(keybox)
        khbox.setContentsMargins(0, 0, 0, 0)

        # down one
        widget = QToolButton()
        widget.setText('-100c')
        widget.setShortcut('<')
        widget.clicked.connect(self._pitch_down)
        khbox.addWidget(widget)

        # up one
        widget = QToolButton()
        widget.setText('+100c')
        widget.setShortcut('>')
        widget.clicked.connect(self._pitch_up)
        khbox.addWidget(widget)

        self._grid.addWidget(keybox, 1, 0)

        # Reread button
        self._reread_button = QPushButton()
        self._reread_button.setText('&Reread file with correction')
        self._reread_button.clicked.connect(self._reread)
        self._grid.addWidget(self._reread_button, 1, 1)

        # Separator line
        widget = QFrame()
        widget.setFrameShape(QFrame.Shape.HLine)
        widget.setFrameShadow(QFrame.Shadow.Sunken)
        self._grid.addWidget(widget, 2, 0, 1, 2)

        # Analysis option widgets

        # Tuning System
        title = gcom.OPTION_TUNING_SYSTEM
        widget = _OptionComboBox(title,
                                ('Equal Temperament',
                                 'Pythagorean'))
        self._grid.addWidget(widget, 3, 0)
        self.widgets[title] = widget

        # Reference Frequency
        title = gcom.OPTION_REF_FREQ
        widget = _OptionFloatLineEdit(title, unit='Hz')
        widget.setStatusTip('Frequency of the reference note')
        self._grid.addWidget(widget, 4, 0)
        self.widgets[title] = widget

        # Reference Note
        title = gcom.OPTION_REF_NOTE
        widget = _OptionRefnoteLineEdit(title)
        self._grid.addWidget(widget, 5, 0)
        self.widgets[title] = widget

        # Start Time
        title = gcom.OPTION_START
        widget = _OptionStartEnd(title, unit=True, none_sentinel='Beginning')
        widget.setStatusTip('Ignore audio before this time')
        self._grid.addWidget(widget, 3, 1)
        self.widgets[title] = widget

        # End Time
        title = gcom.OPTION_END
        widget = _OptionStartEnd(title, unit=True, none_sentinel='End')
        widget.setStatusTip('Ignore the audio after this time')
        self._grid.addWidget(widget, 4, 1)
        self.widgets[title] = widget

        # Low Cut
        title = gcom.OPTION_LOW_CUT
        widget = _OptionFloatLineEdit(title, unit='Hz')
        widget.setStatusTip('Ignore frequencies below this')
        self._grid.addWidget(widget, 6, 0)
        self.widgets[title] = widget

        # High Cut
        title = gcom.OPTION_HIGH_CUT
        widget = _OptionFloatLineEdit(title, unit='Hz')
        widget.setStatusTip('Ignore frequencies above this')
        self._grid.addWidget(widget, 7, 0)
        self.widgets[title] = widget

        # dB Range
        title = gcom.OPTION_DB_RANGE
        widget = _OptionFloatLineEdit(title, unit='dB')
        widget.setStatusTip('Ignore frequencies this much fainter'
                            ' than the highest peak')
        self._grid.addWidget(widget, 5, 1)
        self.widgets[title] = widget

        # Max Peaks
        title = gcom.OPTION_MAX_PEAKS
        widget = _OptionIntSpinBox(title)
        widget.setStatusTip('Maximum number of frequencies to show')
        self._grid.addWidget(widget, 6, 1)
        self.widgets[title] = widget

        # Pad input
        title = gcom.OPTION_PAD
        widget = _OptionCheckBox(title)
        widget.setStatusTip("Pad the audio with zeros to ensure the FFT"
                            " window doesn't miss the very beginning and end")
        self._grid.addWidget(widget, 7, 1)
        self.widgets[title] = widget


        self.widgets[gcom.OPTION_PITCH].widget.valueChanged.connect(
                                                        self._pitch_changed)
        self.widgets[gcom.OPTION_TEMPO].widget.valueChanged.connect(
                                                        self._tempo_changed)
        self._link.toggled.connect(self._link_toggled)


        self._scroll_area.setWidget(self._panel)

    def _init_buttons(self):
        self._button_panel = QWidget(self)
        hbox = QHBoxLayout(self._button_panel)

        self._hold = QCheckBox('Hold')
        self._hold.setStatusTip("Don't update settings to reflect selection")
        hbox.addWidget(self._hold)
        self._to_defaults = QPushButton('Revert to &defaults')
        self._to_defaults.clicked.connect(self.set_default_options)
        hbox.addWidget(self._to_defaults)
        self._to_selected = QPushButton('&Apply to selected')
        self._to_selected.clicked.connect(self._push_options)
        hbox.addWidget(self._to_selected)
        hbox.setContentsMargins(0, 0, 0, 0)

    def _link_toggled(self, event):
        if event:
            self._link_ok = False
            pitch = self.widgets[gcom.OPTION_PITCH].get()
            self.widgets[gcom.OPTION_TEMPO].set(pitch)
            self._link_ok = True

    def _pitch_changed(self, event):
        self.PitchChange.emit(event)
        if self._link_ok and self._link.isChecked():
            self._link_ok = False
            self.widgets[gcom.OPTION_TEMPO].set(event)
            self._link_ok = True

    def _tempo_changed(self, event):
        if self._link_ok and self._link.isChecked():
            self._link_ok = False
            self.widgets[gcom.OPTION_PITCH].set(event)
            self._link_ok = True

    def _pitch_up(self):
        p = self.widgets[gcom.OPTION_PITCH].get_precise()
        p *= com.cents_to_ratio(100)
        self.widgets[gcom.OPTION_PITCH].set(p)

    def _pitch_down(self):
        p = self.widgets[gcom.OPTION_PITCH].get_precise()
        p /= com.cents_to_ratio(100)
        self.widgets[gcom.OPTION_PITCH].set(p)

    def set_start(self, start):
        """Set the value of the start time option.

        Parameters
        ----------
        start : str
            The start time.
        """

        if start is not None:
            self.widgets[gcom.OPTION_START].set(f'{start:.3f}')

    def set_end(self, end):
        """Set the value of the end time option.

        Parameters
        ----------
        end : str
            The end time.
        """

        if end is not None:
            self.widgets[gcom.OPTION_END].set(f'{end:.3f}')

    def start_end_enable(self, enable):
        """Enable or disable the buttons that set the start and end
        values to the current player position.

        Parameters
        ----------
        enable : bool
            Enable if True, disable if False.
        """

        self.widgets[gcom.OPTION_START].unit.setEnabled(enable)
        self.widgets[gcom.OPTION_END].unit.setEnabled(enable)

    def ensure_visible(self):
        """Trigger emission of the PayAttentionToMe signal."""

        self.PayAttentionToMe.emit()

    def set_options(self, options, force=False, is_defaults=False):
        """Set all the widgets in the panel to the specified values,
        unless the `Hold` checkbox is checked, in which case nothing
        changes (however, a `PitchChange` signal is still emitted in
        that case, to make sure anything that uses that signal updates
        properly even when `Hold` is checked).

        Parameters
        ----------
        options : audio_tuner_gui.common.Options
            An Options object containing the values to set.
        force : bool, optional
            If True, ignore the `Hold` checkbox and set the options even
            if it's checked.  Default False.
        is_defaults : bool, optional
            If the options being set are the defaults, set this to True.
            This causes the `default` attribute of the widgets to be set
            in addition to the value, so that the widgets know how to
            return themselves to the default setting if the user
            requests it.
        """

        if force or not self._hold.isChecked():
            for opt in options:
                try:
                    self.widgets[opt].set(options[opt])
                    if is_defaults:
                        self.widgets[opt].default = options[opt]
                except KeyError:
                    pass
        else:
            factor = self.widgets[gcom.OPTION_PITCH].get()
            self.PitchChange.emit(factor)

    def get_options(self) -> gcom.Options:
        """Get the values currently set in the option widgets.

        Returns
        -------
        audio_tuner_gui.common.Options
            The values.
        """

        options = gcom.Options(self._args)
        for title in self.widgets:
            options[title] = self.widgets[title].get()
        try:
            self.widgets[gcom.OPTION_REF_NOTE].unset_error()
            options.init_tuning_system()
        except ValueError as err:
            if err.args[0] == 'Invalid reference note':
                self.widgets[gcom.OPTION_REF_NOTE].set_error()
                options[gcom.OPTION_REF_NOTE] = gcom.ERROR_SENTINEL
        for title in self.widgets:
            if options[title] == gcom.ERROR_SENTINEL:
                return None
        return options

    def _push_options(self):
        options = self.get_options()
        if options is not None:
            self.PushOptions.emit(options, False)

    def set_apply_enabled(self, enable):
        """Enable or disable the `Apply to selected` button.

        Parameters
        ----------
        enable : bool
            Enable if True, disable if False.
        """

        self._to_selected.setEnabled(enable)
        self._reread_button.setEnabled(enable)

    def _reread(self):
        options = self.get_options()
        if options is not None:
            options.reread_requested = True
            self.PushOptions.emit(options, True)

    def set_default_options(self):
        """Set the widgets to the values passed in the constructor's
        `args` parameter.  This calls `set_options` with force=True and
        is_defaults=True.  It also sets the link button to the linked state.
        """

        self.set_options(self._default_options, force=True, is_defaults=True)
        self._link.setChecked(True)
