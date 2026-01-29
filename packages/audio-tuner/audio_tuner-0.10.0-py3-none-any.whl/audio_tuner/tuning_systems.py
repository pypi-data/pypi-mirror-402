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


"""Classes representing tuning systems.  The API of each tuning system
class is identical.  They all take `ref_note` and `ref_freq` arguments
at instantiation, and the instances are iterators that take `start_freq`
and `end_freq` arguments and yield notes covering at least that
range.  Allowed values for `ref_note` may differ, however."""


__author__ = 'Jessie Blue Cassell'


__all__ = [
            'EqualTemperament',
            'Pythagorean',
            'flat_symbol',
            'sharp_symbol'
          ]


import math
import re

import audio_tuner.common as com


flat_symbol = '\N{MUSIC FLAT SIGN}'
sharp_symbol = '\N{MUSIC SHARP SIGN}'


# Tuning system classes.  Because valid values for `ref_note` are not
# necessarily the same for all possible tuning systems, input validation
# needs to happen at class instantiation and not before.  This is one
# reason for not using generator functions for this.

class EqualTemperament:
    """Iterate over notes in the equal temperament tuning system.

    Parameters
    ----------
    ref_note : str, optional
        The note who's frequency is set by ref_freq.  Acceptable note
        names are capital letters from A to G, optionally followed by a
        single sharp of flat sign and/or an octave number, with no
        spaces.  The default octave if the number is left off is 4.
        Sharp and flat symbols can be '#' and 'b', or the 'MUSIC SHARP
        SIGN' or 'MUSIC FLAT SIGN' Unicode characters.  Default 'A4'.
    ref_freq : float, optional
        The frequency of ref_note in Hz. If None, a value is
        automatically chosen that will make A4 have a frequency of 440
        Hz. Default None.

    Attributes
    ----------
    ref_note : str
        The note who's frequency is set by ref_freq.
    ref_freq : float
        The frequency of ref_note in Hz.

    Raises
    ------
    ValueError
        For invalid `ref_note`.
    """

    def __init__(self, ref_note='A4', ref_freq=None):
        self.ref_note = ref_note

        self.ref_note = self.ref_note.replace(flat_symbol, 'b')
        self.ref_note = self.ref_note.replace(sharp_symbol, '#')

        if not re.match(r'^[A-G][#b]?-?\d*$', self.ref_note):
            raise ValueError('Invalid reference note')

        self._notenames = ['C','C#','D','Eb','E','F',
                           'F#','G','Ab','A','Bb','B']

        if not self.ref_note.lstrip('ABCDEFG#b-').isnumeric():
            self.ref_note += '4'

        self.ref_note = self.ref_note.replace('Db', 'C#')
        self.ref_note = self.ref_note.replace('D#', 'Eb')
        self.ref_note = self.ref_note.replace('Gb', 'F#')
        self.ref_note = self.ref_note.replace('G#', 'Ab')
        self.ref_note = self.ref_note.replace('A#', 'Bb')
        self.ref_note = self.ref_note.replace('B#', 'C')
        self.ref_note = self.ref_note.replace('Fb', 'E')
        self.ref_note = self.ref_note.replace('E#', 'F')
        self.ref_note = self.ref_note.replace('Cb', 'B')

        self._ref_n = (int(self.ref_note.lstrip('ABCDEFG#b')) * 12
                 + self._notenames.index(self.ref_note.rstrip('0123456789-'))
                 - 57)

        if ref_freq is None:
            self.ref_freq = 440 * 2**(self._ref_n/12)
        else:
            self.ref_freq = ref_freq

        self._A4_freq = self.ref_freq * 2**(-self._ref_n/12)

        self._start_freq = None
        self._end_freq = None

    def __call__(self, start_freq, end_freq):
        """Set the range of frequencies to cover.  When iterating, the
        object will yield a range of notes covering AT LEAST the
        specified frequency range.

        Parameters
        ----------
        start_freq : float
            The lower end of the frequency range, in Hz.
        end_freq:
            The upper end of the frequency range, in Hz.

        Returns
        -------
        EqualTemperament
            `self`, since it's an iterator.
        """

        self._start_freq = start_freq
        self._end_freq = end_freq
        return self

    def __iter__(self):
        """Iterate over notes.

        Yields
        ------
        note_freq : float
            The frequency of the note.
        note_name : str
            The name of the note.  This is normally no more than 6
            characters long, but could be longer if the octave number
            has enough digits.
        band_bottom : float
        band_top : float
            The top and bottom of a band of frequencies closer in pitch
            to the note than any other note (in other words, the Voronoi
            region on a log scale).
        """

        start_n = math.floor(12*math.log2(self._start_freq/self._A4_freq)) - 3
        end_n = math.ceil(12*math.log2(self._end_freq/self._A4_freq)) + 3

        next_note_freq = -1
        band_top = -1
        for n in range(start_n, end_n):
            note_freq = next_note_freq
            band_bottom = band_top
            next_note_freq = self._A4_freq * 2**((n+1)/12)

            if note_freq < 0:
                continue

            band_top = (note_freq*next_note_freq)**(1/2)

            if band_bottom < 0:
                continue

            note_name = self._notenames[n%12-3] + str(math.floor((n-3)/12) + 5)

            note_name = note_name.replace('b', flat_symbol)
            note_name = note_name.replace('#', sharp_symbol)

            yield note_freq, note_name, band_bottom, band_top



class Pythagorean:
    """Iterate over notes in the Pythagorean tuning system.

    Parameters
    ----------
    ref_note : str, optional
        The starting note when building the scale.  Acceptable note
        names are capital letters from A to G, optionally followed by a
        single sharp of flat sign and/or an octave number, with no
        spaces.  The default octave if the number is left off is 4.
        Sharp and flat symbols can be '#' and 'b', or the 'MUSIC SHARP
        SIGN' or 'MUSIC FLAT SIGN' Unicode characters.  Default 'A4'.
    ref_freq : float, optional
        The frequency of ref_note in Hz.  If None, an appropriate value
        is automatically chosen from the A440 equal temperament system.
        This ensures the note frequencies won't change too drastically
        as ref_note is changed.  Default None.

    Attributes
    ----------
    ref_note : str
        The note who's frequency is set by ref_freq.
    ref_freq : float
        The frequency of ref_note in Hz.

    Raises
    ------
    ValueError
        For invalid `ref_note`.
    """

    def __init__(self, ref_note='A4', ref_freq=None):
        self.ref_note = ref_note

        self.ref_note = self.ref_note.replace(flat_symbol, 'b')
        self.ref_note = self.ref_note.replace(sharp_symbol, '#')

        if not re.match(r'^[A-G][#b]?-?\d*$', self.ref_note):
            raise ValueError('Invalid reference note')

        self._note_name_tolerance = 1

        if not self.ref_note.lstrip('ABCDEFG#b-').isnumeric():
            self.ref_note += '4'

        ref_note_split = (self.ref_note.rstrip('0123456789-'),
                          int(self.ref_note.lstrip('ABCDEFG#b')))

        if ref_note_split[0] == 'C':
            self._ref_n = -9
            self._octave_offset = 3
        elif ref_note_split[0] == 'B#':
            self._ref_n = -9
            self._octave_offset = 3
        elif ref_note_split[0] == 'Db':
            self._ref_n = -8
            self._octave_offset = 3
        elif ref_note_split[0] == 'C#':
            self._ref_n = -8
            self._octave_offset = 3
        elif ref_note_split[0] == 'D':
            self._ref_n = -7
            self._octave_offset = 3
        elif ref_note_split[0] == 'Eb':
            self._ref_n = -6
            self._octave_offset = 3
        elif ref_note_split[0] == 'D#':
            self._ref_n = -6
            self._octave_offset = 3
        elif ref_note_split[0] == 'Fb':
            self._ref_n = -5
            self._octave_offset = 4
        elif ref_note_split[0] == 'E':
            self._ref_n = -5
            self._octave_offset = 3
        elif ref_note_split[0] == 'F':
            self._ref_n = -4
            self._octave_offset = 3
        elif ref_note_split[0] == 'E#':
            self._ref_n = -4
            self._octave_offset = 3
        elif ref_note_split[0] == 'Gb':
            self._ref_n = -3
            self._octave_offset = 3
        elif ref_note_split[0] == 'F#':
            self._ref_n = -3
            self._octave_offset = 3
        elif ref_note_split[0] == 'G':
            self._ref_n = -2
            self._octave_offset = 3
        elif ref_note_split[0] == 'Ab':
            self._ref_n = -1
            self._octave_offset = 3
        elif ref_note_split[0] == 'G#':
            self._ref_n = -1
            self._octave_offset = 3
        elif ref_note_split[0] == 'A':
            self._ref_n = 0
            self._octave_offset = 3
        elif ref_note_split[0] == 'Bb':
            self._ref_n = 1
            self._octave_offset = 3
        elif ref_note_split[0] == 'A#':
            self._ref_n = 1
            self._octave_offset = 3
        elif ref_note_split[0] == 'Cb':
            self._ref_n = 2
            self._octave_offset = 4
        elif ref_note_split[0] == 'B':
            self._ref_n = 2
            self._octave_offset = 3
        else:
            raise RuntimeError('Something went wrong with ref_note handling')

        self._ref_n += (ref_note_split[1] - 4) * 12

        # Building a Pythagorean scale from fifths and octaves is easy
        # enough, but identifying what notes have been generated is
        # trickier.  This helps with that.

        note_freqs = [
            [1,                 'C'],
            [1.01364326477051,  'B#'],
            [1.05349794238683,  'Db'],
            [1.06787109375,     'C#'],
            [1.10985791461329,  'Ebb'],
            [1.125,             'D'],
            [1.14034867286682,  'C##'],
            [1.18518518518519,  'Eb'],
            [1.20135498046875,  'D#'],
            [1.24859015393995,  'Fb'],
            [1.265625,          'E'],
            [1.28289225697517,  'D##'],
            [1.31538715806019,  'Gbb'],
            [1.33333333333333,  'F'],
            [1.35152435302734,  'E#'],
            [1.40466392318244,  'Gb'],
            [1.423828125,       'F#'],
            [1.44325378909707,  'E##'],
            [1.47981055281772,  'Abb'],
            [1.5,               'G'],
            [1.52046489715576,  'F##'],
            [1.58024691358025,  'Ab'],
            [1.601806640625,    'G#'],
            [1.66478687191993,  'Bbb'],
            [1.6875,            'A'],
            [1.71052300930023,  'G##'],
            [1.77777777777778,  'Bb'],
            [1.80203247070312,  'A#'],
            [1.87288523090992,  'Cb'],
            [1.8984375,         'B'],
            [1.92433838546276,  'A##'],
            [1.97308073709029,  'Dbb']]

        if ref_freq is None:
            self.ref_freq = 440 * 2**(self._ref_n/12)
        else:
            self.ref_freq = ref_freq

        factor = 1
        for i, note_freq in enumerate(note_freqs):
            if note_freq[1] == self.ref_note.rstrip('0123456789-'):
                factor = note_freq[0]
        for i in range(len(note_freqs)):
            note_freqs[i][0] /= factor
            if note_freqs[i][0] < 1:
                note_freqs[i][0] *= 2

        # Build a Pythagorean scale out of perfect fifths and octaves.

        self._scale_freqs = []
        for i in range(-5, 7):
            self._scale_freqs.append(3**i * 2**(-i))
            while self._scale_freqs[-1] < 1:
                self._scale_freqs[-1] *= 2
            while self._scale_freqs[-1] > 2:
                self._scale_freqs[-1] /= 2
        self._scale_freqs.sort()

        # Name the notes in the scale

        self._scale_note_names = []
        for scale_freq in self._scale_freqs:
            for i, note_freq in enumerate(note_freqs):
                cents = math.fabs(com.ratio_to_cents(scale_freq/note_freq[0]))
                if cents < self._note_name_tolerance:
                    self._scale_note_names.append(note_freq[1])
        if not len(self._scale_freqs) == len(self._scale_note_names):
            raise RuntimeError('Unable to find names for all notes')

        self._start_freq = None
        self._end_freq = None


    def __call__(self, start_freq, end_freq):
        """Set the range of frequencies to cover.  When iterating, the
        object will yield a range of notes covering AT LEAST the
        specified frequency range.

        Parameters
        ----------
        start_freq : float
            The lower end of the frequency range, in Hz.
        end_freq:
            The upper end of the frequency range, in Hz.

        Returns
        -------
        Pythagorean
            `self`, since it's an iterator.
        """

        self._start_freq = start_freq
        self._end_freq = end_freq
        return self


    def __iter__(self):
        """Iterate over notes.

        Yields
        ------
        note_freq : float
            The frequency of the note.
        note_name : str
            The name of the note.  This is normally no more than 6
            characters long, but could be longer if the octave number
            has enough digits.
        band_bottom : float
        band_top : float
            The top and bottom of a band of frequencies closer in pitch
            to the note than any other note (in other words, the Voronoi
            region on a log scale).
        """

        start_n = (math.floor(math.log2(self._start_freq / self.ref_freq))
                  * 12 - 3)
        end_n = (math.ceil(math.log2(self._end_freq / self.ref_freq))
                * 12 + 3)

        next_note_freq = -1
        band_top = -1
        for n in range(start_n, end_n):
            note_freq = next_note_freq
            band_bottom = band_top
            next_note_freq = (self.ref_freq
                             * 2**((n+1)//12)
                             * self._scale_freqs[(n+1)%12])

            if note_freq < 0:
                continue

            band_top = (note_freq*next_note_freq)**(1/2)

            if band_bottom < 0:
                continue

            note_name = (self._scale_note_names[n%12]
                         + str(math.floor(((n+self._ref_n)
                                          - self._octave_offset)/12) + 5))

            note_name = note_name.replace('b', flat_symbol)
            note_name = note_name.replace('#', sharp_symbol)

            yield note_freq, note_name, band_bottom, band_top

# TODO:  More tuning systems
