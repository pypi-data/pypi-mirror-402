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


"""Analysis display widget for the GUI."""


__author__ = 'Jessie Blue Cassell'


__all__ = [
            'Display',
          ]


import math

from PyQt6.QtCore import (
                          Qt,
                          pyqtSignal,
                          QRectF,
                          QPointF,
                         )
from PyQt6.QtWidgets import (
                             QGraphicsView,
                             QGraphicsScene,
                             QGraphicsItem,
                             QGraphicsTextItem,
                             QGraphicsLineItem,
                             QGraphicsPolygonItem,
                             QGraphicsRectItem,
                            )
                              
from PyQt6.QtGui import (
                         QColor,
                         QPainter,
                         QPen,
                         QBrush,
                         QTransform,
                         QPolygonF,
                         QLinearGradient,
                        )

import audio_tuner.common as com


DISPLAY_BG_COLOR = QColor(10, 10, 20)
_DISPLAY_HEADER_COLOR = QColor(200, 200, 200)
_DISPLAY_BRIGHT_COLOR = QColor(20, 180, 30)
DISPLAY_DATA_COLOR = QColor(10, 150, 20)
_METER_SCALE_COLOR = QColor(100, 100, 100)
_METER_ZERO_COLOR = QColor(240, 240, 240)

_TITLE_X = .015
_TITLE_Y = .033
_TITLE_H = .045

_HEADER_Y = .07
_HEADER_H = .035
_HEADER_DATA = (
                ('Note', .025),
                ('Standard', .142),
                ('Measured', .295),
                ('Discrepancy', .445),
                ('Correction', .87),
              )


class _DisplayScene(QGraphicsScene):
    def drawBackground(self, painter, rect):
        w = self.width()
        h = self.height()
        margin = 1
        x = margin
        y = margin
        w -= 2 * margin
        h -= 2 * margin
        painter.setBrush(DISPLAY_BG_COLOR)
        painter.setPen(Qt.PenStyle.NoPen)
        r = .02 * w
        painter.drawRoundedRect(QRectF(x, y, w, h), r, r)


class _Text(QGraphicsTextItem):
    def __init__(self, string, color):
        super().__init__(string)
        self.setDefaultTextColor(color)
        self.setTextInteractionFlags(
                            Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setCursor(Qt.CursorShape.IBeamCursor)

    def set_geo(self, x, y, h=None, right=False):
        self.orig_w = self.boundingRect().width()
        self.orig_h = self.boundingRect().height()
        parent = self.parentItem()
        if parent:
            parent_scale = parent.scale()
        else:
            parent_scale = 1.0
        if h:
            scalefactor = h / (self.orig_h * parent_scale)
            self.setScale(scalefactor)
            self.scalefactor = scalefactor
        else:
            scalefactor = self.scale() * parent_scale
            h = self.orig_h * scalefactor
        if right:
            x -= self.orig_w * scalefactor
        y -= h/2
        self.setPos(x / parent_scale, y)

    def set_squish(self, squish_factor):
        self.setTransform(QTransform(squish_factor, 0, 0,
                                     1, 0, 0),
                          combine=False)


class _TitleText():
    def __init__(self, scene, string, color):
        text = _Text(string, color)
        scene.addItem(text)
        self.text = text

    def update_data(self, string):
        self.text.setPlainText(string)
        self.set_geo(self.x, self.y, self.h, self.max_w)

    def set_geo(self, x, y, h, max_w=None):
        self.x = x
        self.y = y
        self.h = h
        self.max_w = max_w
        self.text.set_geo(x, y, h)
        if max_w is not None:
            w = self.text.boundingRect().width() * self.text.scale()
            squish_factor = max_w / w
            if squish_factor < 1:
                self.text.set_squish(squish_factor)
            else:
                self.text.set_squish(1)
            


class _Headers():
    def __init__(self, scene, color):
        self.data = _HEADER_DATA

        self.headers = []
        for x in self.data:
            header = _Text(x[0], color)
            self.headers.append(header)
            scene.addItem(header)
            header.setZValue(2)

    def show(self):
        for header in self.headers:
            header.show()

    def hide(self):
        for header in self.headers:
            header.hide()

    def update_size(self, view_w, view_h):
        for i, header in enumerate(self.headers):
            x = self.data[i][1] * view_w
            y = _HEADER_Y * view_w
            h = _HEADER_H * view_w
            header.set_geo(x, y, h)


class _Meter():
    def __init__(self):
        self.main_thickness = .4
        needle_length = 6
        needle_thickness = 2.6
        needle_middle = 1
        minor_tick_length = 1
        major_tick_length = 2

        main_color = _METER_SCALE_COLOR
        zero_color = _METER_ZERO_COLOR
        needle_color = _DISPLAY_BRIGHT_COLOR

        main_pen = QPen(main_color, self.main_thickness)
        zero_pen = QPen(zero_color, self.main_thickness)
        needle_brush = QBrush(needle_color)
        self.mainline = QGraphicsLineItem(-50, 0, 50, 0)
        self.mainline.setPen(main_pen)

        needlepoly = QPolygonF((
                           QPointF(-needle_thickness / 2, needle_length / 2),
                           QPointF(needle_thickness / 2, needle_length / 2),
                           QPointF(needle_middle / 2, 0),
                           QPointF(needle_thickness / 2, -needle_length / 2),
                           QPointF(-needle_thickness / 2, -needle_length / 2),
                           QPointF(-needle_middle / 2, 0),
                         ))
        needle = QGraphicsPolygonItem(needlepoly)
        needle.setPen(QPen(Qt.PenStyle.NoPen))
        needle.setBrush(needle_brush)
        needle.setParentItem(self.mainline)
        needle.setFlag(QGraphicsItem.GraphicsItemFlag.ItemStacksBehindParent)
        self.needle = needle

        ghostneedle = QGraphicsPolygonItem(needlepoly)
        ghostneedle.setPen(QPen(needle_color, self.main_thickness / 2))
        ghostneedle.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        ghostneedle.setParentItem(self.needle)
        ghostneedle.setFlag(
                        QGraphicsItem.GraphicsItemFlag.ItemStacksBehindParent)
        self.ghostneedle = ghostneedle

        for x in range(-50, 51, 25):
            if x == 0:
                pen = zero_pen
            else:
                pen = main_pen
            if x % 50 == 0:
                y = major_tick_length
            else:
                y = minor_tick_length
            QGraphicsLineItem(x, 0,
                              x, y,
                              self.mainline).setPen(pen)

        for x in range(975, 1026, 5):
            if x == 1000:
                pen = zero_pen
            else:
                pen = main_pen
            if x % 10 == 0:
                y = major_tick_length
            else:
                y = minor_tick_length
            x = (-1.0) * com.ratio_to_cents(x/1000)
            QGraphicsLineItem(x, 0,
                              x, -y,
                              self.mainline).setPen(pen)

    def setParentItem(self, parent):
        self.parent = parent
        self.mainline.setParentItem(parent)

    def set_data(self, cents):
        self.needle.setPos(cents, 0)

    def set_ghost_offset(self, cents):
        self.ghostneedle.setPos(cents, 0)

    def set_geo(self, x, y, w):
        scalefactor = w / 100
        self.mainline.setScale(scalefactor)
        self.mainline.setPos(x, y)


class _Row():
    pass


class _ReferencePoint(QGraphicsItem):
    def boundingRect(self):
        return QRectF(self.x(), self.y(), 0, 0)

    def paint(self, a, b, c):
        pass


class _ClipRect(QGraphicsRectItem):
    def paint(self, a, b, c):
        pass


class _Rows(list):
    def __init__(self, scene):
        super().__init__()
        self.view_w = None

        self.color1 = DISPLAY_DATA_COLOR

        self.vertical_offset = 0.0

        self.scene = scene

        self.cliprect = _ClipRect()
        self.cliprect.setFlag(
                    QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape)
        self.cliprect.setFlag(
                    QGraphicsItem.GraphicsItemFlag.ItemHasNoContents)
        scene.addItem(self.cliprect)

        self.headers = _Headers(scene, _DISPLAY_HEADER_COLOR)
        self.headers.hide()

        self.top_fade = QGraphicsRectItem()
        self.bot_fade = QGraphicsRectItem()
        self.top_fade.setZValue(1)
        self.bot_fade.setZValue(1)
        self.top_fade.setPen(QPen(Qt.PenStyle.NoPen))
        self.bot_fade.setPen(QPen(Qt.PenStyle.NoPen))
        top_grad = QLinearGradient()
        top_grad.setCoordinateMode(QLinearGradient.CoordinateMode.ObjectMode)
        transparent = QColor(DISPLAY_BG_COLOR)
        transparent.setAlpha(0)
        top_grad.setColorAt(1, transparent)
        top_grad.setColorAt(0, DISPLAY_BG_COLOR)
        top_grad.setStart(QPointF(0, 0))
        top_grad.setFinalStop(QPointF(0, 1))
        bot_grad = QLinearGradient(top_grad)
        bot_grad.setStart(QPointF(0, 1))
        bot_grad.setFinalStop(QPointF(0, 0))
        self.top_fade.setBrush(QBrush(top_grad))
        self.bot_fade.setBrush(QBrush(bot_grad))
        scene.addItem(self.top_fade)
        scene.addItem(self.bot_fade)

        self.bar = QGraphicsRectItem()
        self.bar.setZValue(1.5)
        self.bar.setBrush(QBrush(self.color1))
        self.bar.setPen(QPen(Qt.PenStyle.NoPen))
        self.bar.hide()
        scene.addItem(self.bar)

    def add_row(self):
        row = _Row()
        row.parent = _ReferencePoint()
        row.parent.setFlag(
                    QGraphicsItem.GraphicsItemFlag.ItemHasNoContents)
        if len(self) == 0:
            self.headers.show()
            row.parent.setParentItem(self.cliprect)
            row.parent.setFlag(
                    QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        else:
            row.parent.setParentItem(self[0].parent)
        row.note = _Text(' ', self.color1)
        row.note.setParentItem(row.parent)
        row.standard = _Text(' ', self.color1)
        row.standard.setParentItem(row.parent)
        row.measured = _Text(' ', self.color1)
        row.measured.setParentItem(row.parent)
        row.cents = _Text(' ', self.color1)
        row.cents.setParentItem(row.parent)
        row.meter = _Meter()
        row.meter.setParentItem(row.parent)
        row.correction = _Text(' ', self.color1)
        row.correction.setParentItem(row.parent)
        self.append(row)

    def remove_row(self):
        self.scene.removeItem(self[-1].parent)
        del self[-1]
        if len(self) == 0:
            self.headers.hide()

    def update_data(self, result_rows):
        """Update the data displayed in the rows.

        Parameters
        ----------
        result_rows : list[audio_tuner_gui.common.RowData]
            The row data for each row.
        """

        while len(self) > len(result_rows):
            self.remove_row()
        while len(self) < len(result_rows):
            self.add_row()

        for i, row in enumerate(result_rows):
            self[i].note.setPlainText(row['note'])
            self[i].standard.setPlainText(f'{row["standard"]:>8.2f} Hz')
            self[i].measured.setPlainText(f'{row["measured"]:>8.2f} Hz')
            self[i].cents.setPlainText(f'{row["cents"]:>+3.0f} c')
            self[i].meter.set_data(row['cents'])
            self[i].correction.setPlainText(f'{row["correction"]:>8.3f}')
        self.update_size(self.view_w, self.view_h, force=True)

    def update_ghost_offset(self, cents):
        for row in self:
            row.meter.set_ghost_offset(cents)

    def update_size(self, view_w, view_h, force=False):
        old_view_w = self.view_w
        self.view_w = view_w
        self.view_h = view_h
        clip_x = .023 * view_w
        clip_y = .08 * view_w - 2
        self.clip_y = clip_y
        clip_w = .962 * view_w
        clip_h = view_h - (clip_y + 6)
        self.clip_h = clip_h
        fade_x = clip_x
        fade_w = clip_w - 5
        fade_h = view_w * .015
        self.cliprect.setRect(QRectF(clip_x, clip_y,
                                     clip_w, clip_h))
        self.top_fade.setRect(QRectF(fade_x, clip_y - 2,
                                     fade_w, fade_h))
        self.bot_fade.setRect(QRectF(fade_x, clip_y + clip_h - fade_h + 2,
                                     fade_w, fade_h))
        for i, row in enumerate(self):
            h = .04 * view_w
            if i == 0:
                row.parent.setPos(clip_x,
                                  .1 * view_w + self.vertical_offset)
            elif old_view_w != view_w or force:
                row.parent.setPos(0, .03 * i * view_w)
                self.headers.update_size(view_w, view_h)
            if old_view_w != view_w or force:
                row.note.set_geo(0, 0, h)
                row.standard.set_geo(.24 * view_w, 0, h, right=True)
                row.measured.set_geo(.4 * view_w, 0, h, right=True)
                row.cents.set_geo(.486 * view_w, 0, h, right=True)
                row.meter.set_geo(.68 * view_w, 0, .37 * view_w)
                row.correction.set_geo(.855 * view_w, 0, h, right=False)
        self.max_drag = (len(self) * .03 * self.view_w
                       - self.view_h
                       + .11 * self.view_w)
        self.vertical_drag(0)
        self.update_bar()

    def update_bar(self):
        try:
            bar_h_factor = ((self.view_h - .11 * self.view_w) 
                          / (len(self) * .03 * self.view_w))
        except ZeroDivisionError:
            bar_h_factor = 2
        if bar_h_factor < 1:
            bar_h = bar_h_factor * self.clip_h
            self.bar_h = bar_h
            bar_offset = ((-self.vertical_offset / self.max_drag)
                         * (self.clip_h - bar_h))
            self.bar.setRect(QRectF(.985 * self.view_w,
                                    self.clip_y + bar_offset,
                                    .005 * self.view_w,
                                    bar_h))
            self.bar.show()
        else:
            self.bar.hide()

    def vertical_drag(self, event, scroll_bar_click=False):
        if scroll_bar_click:
            event = -((event / (self.clip_h - self.bar_h)) * self.max_drag)
        delta = max(event, -self.max_drag - self.vertical_offset)
        delta = min(delta, -self.vertical_offset)
        try:
            self[0].parent.moveBy(0, delta)
        except IndexError:
            return
        self.vertical_offset += delta
        self.update_bar()

    def one_up(self):
        self.vertical_drag(.03 * self.view_w)

    def one_down(self):
        self.vertical_drag(-.03 * self.view_w)

    def page_up(self):
        n = math.floor((self.view_h - .1 * self.view_w) / (.03 * self.view_w))
        self.vertical_drag(.03 * self.view_w * n)

    def page_down(self):
        n = math.floor((self.view_h - .1 * self.view_w) / (.03 * self.view_w))
        self.vertical_drag(-.03 * self.view_w * n)


class Display(QGraphicsView):
    """A widget that displays the results of the analysis.  Inherits
    from QGraphicsView.
    """

    VerticalDrag = pyqtSignal(float, bool)
    """
    """

    def __init__(self):
        self._w = 101
        self._h = 101
        self._old_w = 101
        self._old_h = 101
        self._scroll_bar_click = False

        self._margin = 10

        self._scene = _DisplayScene(0, 0, self._w, self._h)

        super().__init__(self._scene)

        self._init_display(' ')

        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.setAcceptDrops(False)

    def _init_display(self, title):
        self._title = _TitleText(self._scene, title, DISPLAY_DATA_COLOR)

        self._rows = _Rows(self._scene)
        self.VerticalDrag.connect(self._rows.vertical_drag,
                                  Qt.ConnectionType.QueuedConnection)

    def mousePressEvent(self, event):
        xpos = ((event.pos().x() - self._margin)
              / (self._total_w - 2 * self._margin))
        self._scroll_bar_click = xpos > .983
        self._prev_mouse_pos = event.globalPosition().y()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            mouse_pos = event.globalPosition().y()
            mouse_delta = mouse_pos - self._prev_mouse_pos
            self._prev_mouse_pos = mouse_pos
            self.VerticalDrag.emit(mouse_delta, self._scroll_bar_click)
        super().mouseMoveEvent(event)

    def wheelEvent(self, event):
        self._rows.vertical_drag(event.angleDelta().y())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Up:
            self._rows.one_up()
        if event.key() == Qt.Key.Key_Down:
            self._rows.one_down()
        if event.key() == Qt.Key.Key_PageUp:
            self._rows.page_up()
        if event.key() == Qt.Key.Key_PageDown:
            self._rows.page_down()
        super().keyPressEvent(event)

    def resizeEvent(self, event):
        margin = self._margin
        self._total_w = event.size().width()
        self._total_h = event.size().height()
        w = self._total_w - 2 * margin
        h = self._total_h - 2 * margin
        # force even numbers to prevent jitter in the position of the
        # display while resizing
        h = (h // 2) * 2
        w = (w // 2) * 2
        self._w = w
        self._h = h
        if self._old_w != w:
            self.setMinimumHeight(int(.12 * event.size().width() + 2 * margin))
        if self._old_w != w or self._old_h != h:
            self._old_w = w
            self._old_h = h
            self.setSceneRect(0, 0, w, h)
            super().resizeEvent(event)
            self.update()
            self._scene.setSceneRect(0, 0, w, h)
            self._title.set_geo(_TITLE_X * w,
                               _TITLE_Y * w,
                               _TITLE_H * w, w * .98)
            self._rows.update_size(w, h)
            self._scene.update()

    def _add_row(self):
        pass

    def update_ghost_offset(self, cents):
        """Set the offset of the ghost needles away from the main
        needles.

        Parameters
        ----------
        cents : float
            The offset in cents.
        """

        self._rows.update_ghost_offset(cents)

    def update_data(self, filename, result_rows):
        """Update the displayed data.

        Parameters
        ----------
        filename : str
            The name of the song.
        result_rows : list[audio_tuner_gui.common.RowData]
            The row data for each row.
        """

        try:
            self._title.update_data(filename)
        except AttributeError:
            self._init_display(filename)
        self._rows.update_data(result_rows)
