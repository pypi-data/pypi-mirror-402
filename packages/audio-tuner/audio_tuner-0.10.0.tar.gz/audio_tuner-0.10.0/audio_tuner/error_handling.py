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


"""Exceptions and functions for handling error messages in the Audio
Tuner command line program.
"""


__author__ = 'Jessie Blue Cassell'


__all__ = [
            'LoadError',
            'ShortError',
            'warning',
            'debug',
            'error',
            'logger',
            'ERROR',
            'WARNING',
            'NORMAL',
            'DEBUG',
            'ERRMSG_SHORT',
          ]


import sys
import os
import logging

# Constants for use with the level argument of print_msg functions
ERROR = 3
WARNING = 2
NORMAL = 1
DEBUG = 0


ERRMSG_SHORT = 'Audio is shorter than the FFT window size'

# pylint: disable=unnecessary-pass,logging-fstring-interpolation

class LoadError(Exception):
    """Raised when anything goes wrong reading file data"""
    pass

class ShortError(Exception):
    """Raised when the audio is too short"""
    pass

class Interrupted(Exception):
    """Raised when processing has been interrupted"""
    pass

_prog = os.path.basename(sys.argv[0])

logging.basicConfig(format=f'{_prog}: %(message)s')
logger = logging.getLogger()

def debug(msg):
    """Log a debug message.

    Parameters
    ----------
    msg : str
        The message.
    """

    logging.debug(f'DEBUG: {msg}')

def info(msg):
    """Log a message.

    Parameters
    ----------
    msg : str
        The message.
    """

    logging.info(msg)

def warning(msg):
    """Log a warning message.

    Parameters
    ----------
    msg : str
        The message.
    """

    logging.warning(f'warning: {msg}')

def error(msg, prefix=''):
    """Log a error message.

    Parameters
    ----------
    msg : str
        The message.
    """

    prefix += ' '
    logging.error(f'{prefix}error: {msg}')
