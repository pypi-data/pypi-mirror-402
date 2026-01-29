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


"""Miscellaneous functions used by Audio Tuner.  This also includes
`mpv_error`, and thus should be imported by other modules before they
import mpv so that they can check `mpv_error` first.

Parameters
----------
mpv_error : str
    If there was a problem importing mpv, this contains the error message.
    None if there was no problem.
ffmpeg_error : str
    If ffmpeg is not found, this contains an error message.  None if
    ffmpeg is available.
ffprobe_error : str
    If ffprobe is not found, this contains an error message.  None if
    ffprobe is available.
FFMPEG_BINARY : str
    The path to ffmpeg, or None of it's not found.
FFPROBE_BINARY : str
    The path to ffprobe, or None of it's not found.
"""


__author__ = 'Jessie Blue Cassell'


__all__ = [
            'mpv_error',
            'ratio_to_cents',
            'cents_to_ratio',
            'raw_to_string',
            'string_to_raw',
            'ffmpeg_error',
            'ffprobe_error',
            'FFMPEG_BINARY',
            'FFPROBE_BINARY',
          ]


import os
import math
import shutil

# pylint: disable=unused-import
try:
    import mpv
    mpv_error = None
except OSError as err:
    mpv_error = str(err)


ffmpeg_error = None
ffprobe_error = None
FFMPEG_BINARY = shutil.which('ffmpeg')
FFPROBE_BINARY = shutil.which('ffprobe')
if not FFMPEG_BINARY:
    ffmpeg_error = 'ffmpeg not found'
if not FFPROBE_BINARY:
    ffprobe_error = 'ffprobe not found'


def ratio_to_cents(ratio):
    """Convert a ratio of frequencies to cents.  Ratios greater than one
    convert to a positive number of cents, less than one convert to
    negative.
    
    Parameters
    ----------
    ratio : float
        The ratio of frequencies.

    Returns
    -------
    float
        The note difference in cents.
    """

    return math.log2(ratio) * 1200


def cents_to_ratio(cents):
    """Convert a note difference in cents to a frequency ratio.  This is
    the inverse of `ratio_to_cents`.

    Parameters
    ----------
    cents : float
        The note difference in cents.

    Returns
    -------
    float
        The ratio of frequencies.
    """

    return math.exp2(cents / 1200)


def raw_to_string(path):
    """Convert a bytes object representing a path to a string.

    Parameters
    ----------
    path : bytes
        The path, or None.

    Returns
    -------
    str
        The path as a string, or None if `path` is None.
    """

    if path is None:
        return None
    return os.fsdecode(path)


def string_to_raw(path):
    """Convert a string representing a path to a bytes object.

    Parameters
    ----------
    path : str
        The path, or None.

    Returns
    -------
    bytes
        The path as a bytes object, or None if `path` is None.
    """

    if path is None:
        return None
    return os.fsencode(path)
