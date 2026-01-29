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

__all__ = [
            'analysis',
            'common',
            'display',
            'export',
            'file_selector',
            'log_viewer',
            'option_panel',
            'player',
            'VERSION',
            'PKGDIR',
          ]

# Development versions:  X.Y.Z.devN
# Release candidates:  X.Y.ZrcN
# Releases:  X.Y.Z

VERSION = '0.10.0'

from os.path import dirname

PKGDIR = dirname(__spec__.origin)
