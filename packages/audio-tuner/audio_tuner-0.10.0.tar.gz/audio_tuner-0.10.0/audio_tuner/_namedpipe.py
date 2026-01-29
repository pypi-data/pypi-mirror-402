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


# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=consider-using-with
# pylint: disable=unspecified-encoding

__author__ = 'Jessie Blue Cassell'

# This is a minimal replacement for the `namedpipe` package.  It
# reimplements a subset of the API, only including the parts needed by
# audio_tuner.analysis on POSIX systems.

# Dropping the dependency on the original namedpipe is useful because
# there are situations where it isn't available (such as installing on
# Debian without using pip).

# The original namedpipe code couldn't be included because it's GPLv2
# only, hence this reimplementation.

import os
import tempfile

FIFO_NAME = 'audio_tuner_fifo'

class NPopen:
    def __init__(self, mode='rb'):
        self.mode = mode
        self.stream = None
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.temp_dir.name, FIFO_NAME)
        os.mkfifo(self.path)

    def wait(self):
        self.stream = open(self.path, mode=self.mode)
        return self.stream

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.stream is not None:
            self.stream.close()
            self.stream = None
        self.temp_dir.cleanup()

        return False
