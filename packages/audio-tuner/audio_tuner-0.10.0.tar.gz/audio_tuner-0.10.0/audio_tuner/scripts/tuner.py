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


"""Command line program for measuring the prominent frequencies in an
audio file and comparing them to the frequencies of a tuning system.
"""


__author__ = 'Jessie Blue Cassell'


import sys
import os
import logging

# colorama is only needed on Windows.
has_colorama = False
if os.name == 'nt':
    try:
        import colorama
        has_colorama = True
    except ModuleNotFoundError:
        pass

import audio_tuner.tuning_systems as tuning_systems
import audio_tuner.common as com
import audio_tuner.analysis as anal
import audio_tuner.error_handling as eh
import audio_tuner.argument_parser as ap

from audio_tuner import VERSION


DESCRIPTION = ('Measure audio frequencies in a recording and compare them'
               ' to a standard.')

VERSION_STRING = 'tuner (Audio Tuner) ' + VERSION + """
Copyright (C) 2025, 2026 Jessie Blue Cassell.
License GPLv3+: GNU GPL version 3 or later <https://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law."""


# Terminal colors
_CSI = '\033['
_COLOR_DIM = _CSI + '2m'
_COLOR_RESET_ALL = _CSI + '0m'


def main():
    parser = ap.get_arg_parser(version=VERSION_STRING, description=DESCRIPTION)
    cli_args = parser.parse_args_gm()
    args = ap.merge_args(cli_args)

    check_unitarity = False
    if args.verbose:
        eh.logger.setLevel(logging.INFO)
        check_unitarity = True
    if args.debug:
        eh.logger.setLevel(logging.DEBUG)

    if not ap.validate(args):
        return 2


    size = 2**args.size_exp


    try:
        if args.tuning == 'equal_temperament':
            tuning_system = tuning_systems.EqualTemperament(
                                args.ref_note, args.ref_freq)
        elif args.tuning == 'pythagorean':
            tuning_system = tuning_systems.Pythagorean(
                                args.ref_note, args.ref_freq)
    except ValueError:
        ap.arg_error(f'invalid ref_note: {args.ref_note}')
        return 2


    # pylint: disable=possibly-used-before-assignment
    if has_colorama:
        colorama.init()

    color_ok = has_colorama or os.name == 'posix'

    for inputfile in args.file:
        print()

        analysis = anal.Analysis(inputfile,
                                 try_sequence=args.backends)

        if not args.nopad:
            pad_amounts = (size * 2, size * 2)
        else:
            pad_amounts = None

        try:
            analysis.load_data(start=args.start,
                               end=args.end,
                               samplerate=args.samplerate,
                               pad=pad_amounts)
        except eh.LoadError:
            eh.warning(f'skipping {inputfile}')
            continue

        print(inputfile)
        if analysis.file_title is not None:
            print(analysis.file_title)

        keep_all = args.plot == 'spectrogram'
        try:
            analysis.fft(size=size,
                         keep_all=keep_all,
                         check_unitarity=check_unitarity)
        except eh.ShortError:
            eh.warning(eh.ERRMSG_SHORT +
                  '.  Try enabling padding or decreasing size_exp.')
            eh.warning(f'skipping {inputfile}')
            continue

        # The total energy of the original signal and the energy of the
        # computed spectrum should in principle be the same, as per
        # Parseval's theorem.
        if check_unitarity:
            e_in = analysis.energy_in
            e_out = analysis.energy_out
            print(f'Energy in original signal: {e_in}')
            print(f'Energy in spectrum:        {e_out}')
            print(f'Ratio (spectrum/original): {e_out/e_in}')

        peaks = analysis.find_peaks(low_cut=args.low_cut,
                                    high_cut=args.high_cut,
                                    max_peaks = args.max_peaks,
                                    dB_range=args.dB_range)


        print('  Note    Standard     Measured   Discrepancy'
              '                         Correction')

        for note in tuning_system(args.low_cut, args.high_cut):
            note_freq, note_name, band_bottom, band_top = note
            for peak in [p[0] for p in peaks]:
                if peak > band_bottom and peak <= band_top:
                    freq_ratio = note_freq/peak
                    cents = -com.ratio_to_cents(freq_ratio)
                    meter = list('[------------+------------]')
                    if cents < -50:
                        meter[1] = '<'
                    elif cents > 50:
                        meter [-2] = '>'
                    else:
                        meter[round(cents/4)+13] = 'I'

                    if color_ok and (args.color or sys.stdout.isatty()):
                        for c in range(1, len(meter) - 1):
                            if '-' in meter[c] and not '-' in meter[c-1]:
                                meter[c] = _COLOR_DIM + meter[c]
                            if '-' in meter[c] and not '-' in meter[c+1]:
                                meter[c] = meter[c] + _COLOR_RESET_ALL

                    note_str = note_name
                    if note_freq < 10000:
                        if len(note_str) < 6:
                            note_str = '  ' + note_str
                        else:
                            note_str = ' ' + note_str
                    else:
                        if len(note_str) < 5:
                            note_str = '  ' + note_str
                        elif len(note_str) == 5:
                            note_str = ' ' + note_str
                    print(' {0:7}'
                          '{1:>8.2f} Hz'
                          '  {2:>8.2f} Hz'
                          '  {3:>+3.0f} c'
                          '  {4}'
                          '  {5:>8.3f}'.format(
                                note_str,
                                note_freq,
                                peak,
                                cents,
                                ''.join(meter),
                                freq_ratio))

        # Make sure the output is actually shown before moving on to the
        # plotting.
        sys.stdout.flush()

        if args.plot is not None:
            try:
                analysis.show_plot(plot_type=args.plot)
            except ModuleNotFoundError:
                eh.warning('matplotlib not found.  Plotting disabled.')
                args.plot = None

    return 0

if __name__ == '__main__':
    sys.exit(main())
