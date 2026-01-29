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


"""This module is all about reading audio files and analyzing the
audio."""


__author__ = 'Jessie Blue Cassell'


__all__ = [
            'Analysis',
            'FNF_ERROR',
            'mpv_cm',
          ]


import subprocess as sp
import sys
import math
import os
import io
import numpy as np
import tempfile
from contextlib import contextmanager

if os.name == 'posix':
    import audio_tuner._namedpipe as namedpipe
else:
    import namedpipe

import audio_tuner.error_handling as eh
import audio_tuner.argument_parser as ap
import audio_tuner.common as com

mpv_error = com.mpv_error
if mpv_error is None:
    import mpv


FNF_ERROR = 'Output file not found'

try:
    # Stops unnecessary terminal windows from popping up on Windows when
    # using the GUI
    _CREATIONFLAGS = sp.CREATE_NO_WINDOW
except AttributeError:
    # The flag only exists when running on Windows, and is unneeded
    # otherwise
    _CREATIONFLAGS = 0


def _weighted_average(x, y):
    return math.fsum([a * b for a, b in zip(x, y)]) / math.fsum(y)


def _quad_inter(x, y):
    c0 = y[1]
    c1 = (y[2] - y[0]) / (x[2] - x[0])
    c2 = (((y[2] - y[1]) / (x[2] - x[1]) - (y[1] - y[0]) / (x[1] - x[0]))
          / (x[2] - x[0]))

    x_est = x[1] - c1/(2*c2)
    y_est = (c2 * (x_est-x[1])**2 + c1 * (x_est-x[1]) + c0)

    return y_est

@contextmanager
def mpv_cm(*args, **kwargs):
    """A context manager that creates an instance of mpv.MPV and then
    terminates it when it finishes.  All parameters are passed directly
    to the mpv.MPV constructor.

    Returns
    -------
    err : ValueError|NameError
        None on success, ValueError if there was something wrong with
        the parameters, or NameError if mpv isn't available.
    player : mpv.MPV
        The created mpv.MPV instance, or None if something went wrong.
    """

    # pylint: disable=possibly-used-before-assignment

    player = None
    err = None
    try:
        player = mpv.MPV(*args, **kwargs)
    except (ValueError, NameError) as e:
        err = e
    try:
        yield err, player
    finally:
        if player is not None:
            if not player.core_shutdown:
                player.command('quit')
            player.terminate()


class Analysis:
    """A class for analyzing an audio file.

    To use, first instantiate the class, passing the file to analyze to
    the `inputfile` parameter.  Then call the `load_data` method to read
    the file, and the `fft` method to run a Fourier analysis.  Spectral
    peaks can then be obtained by calling the `find_peaks` method.

    Parameters
    ----------
    inputfile : str
        The path of the file to analyze.
    try_sequence : iterable, optional
        A sequence of file reading backends to try in order.
        Default [audio_tuner.argument_parser.MPV_PIPE_OPTION,
        audio_tuner.argument_parser.FFMPEG_OPTION]
    default_samplerate : int, optional
        The sample rate, in kHz, to assume if sample rate detection
        fails.  Default 44100.

    Attributes
    ----------
    inputfile : str
        The path of the file being analyzed.
    print_msg : callable
        If not None, this will be called to handle messages.  Should be
        a callable of the form f(msg: str, level: int) -> None, where
        msg is the message and level is the severity level (either
        DEBUG, NORMAL, WARNING or ERROR from the error_handling module).
        Default None.
    try_sequence : iterable
        A sequence of file reading backends to try in order.
    default_samplerate : int
        The default sample rate, in kHz, as set by the
        default_samplerate parameter.
    file_samplerate : int
        The actual sample rate, in kHz, as read from the file header by
        the `load_metadata` method.  None if `load_metadata` has not yet
        been run.
    samplerate : int
        The sample rate, in kHz, actually used in the analysis.  Set by
        the `load_data` method.  None if unset.
    pitch : float
        The pitch correction factor to apply when reading data.
        Initialized to 1.0.
    tempo : float
        The tempo correction factor to apply when reading data.
        Initialized to 1.0.
    file_title : str
        The title of the song as read from the file header by the
        `load_metadata` method.  None if `load_metadata` has not yet
        been run.
    file_track : str
        The track number of the song as read from the file header by the
        `load_metadata` method.  This is read directly from the tag and
        may be in the form "track number/number of tracks on album".
        None if `load_metadata` has not yet been run.
    file_duration : float
        The duration of the audio in seconds.  None if unset.
    file_metadata : dict
        File tags
    energy_in : np.float64
        The total energy in the input audio, as a dimensionless number.
        Set by the `fft` method if it's `check_unitarity` parameter is
        True.  None if unset.
    energy_out : np.float64
        The total energy in the frequency spectrum, as a dimensionless
        number.  Set by the `fft` method if it's `check_unitarity`
        parameter is True.  Should be close to energy_in, otherwise
        something's gone wrong.  None if unset.
    peaks : list
        A list of lists, generated by `find_peaks`.  Each list consists
        of three floats:  The frequency of the peak in Hz, the
        prominence of the peak compared to nearby frequencies in dB, and
        the loudness of the peak in dB.  None if unset.
    plot_plotted : bool
        Whether a log or linear plot has been plotted.
    """

    def __init__(self,
                 inputfile,
                 print_msg=None,
                 try_sequence=(ap.MPV_PIPE_OPTION, ap.FFMPEG_OPTION),
                 default_samplerate=44100):
        self.inputfile = inputfile
        self.print_msg = print_msg
        self.try_sequence = try_sequence
        self.default_samplerate = default_samplerate
        self.file_samplerate = None
        self.file_title = None
        self.file_track = None
        self.file_metadata = None
        self._metadata_loaded = False
        self.pitch = 1.0
        self.tempo = 1.0
        self.plot_plotted = False

        self._normalization_factor = 2**30

        self.samplerate = None
        self.file_duration = None
        self.energy_in = None
        self.energy_out = None
        self.peaks = None

        self._mpv_err = None
        self._loaded = None
        self._audio_array = None
        self._len_audio_array = None
        self._len_unpadded_array = None
        self._freqs = None
        self._decibels = None
        self._spectrogram = None
        self._size = None
        self._spectrum = None
        self._window_step = None
        self._low_cut = None
        self._high_cut = None


    def load_metadata(self):
        """Get metadata from the file.

        Raises
        ------
        eh.LoadError
            When there's a problem obtaining the metadata.
        """

        tried_mpv = False

        for backend in self.try_sequence:
            if self._metadata_loaded:
                break
            if not tried_mpv and backend in [ap.MPV_PIPE_OPTION,
                                             ap.MPV_TEMPFILE_OPTION]:
                tried_mpv = True
                if mpv_error is not None:
                    if self.print_msg is not None:
                        self.print_msg(mpv_error, eh.ERROR)
                    else:
                        eh.error(mpv_error)
                    continue
                try:
                    self._load_metadata_libmpv()
                except eh.LoadError:
                    s = 'libmpv failed'
                    if self.print_msg is not None:
                        self.print_msg(s, eh.WARNING)
                    else:
                        eh.warning(s)
            elif backend == ap.FFMPEG_OPTION:
                try:
                    self._load_metadata_ffprobe()
                except (eh.LoadError, FileNotFoundError):
                    s = 'ffprobe failed'
                    if self.print_msg is not None:
                        self.print_msg(s, eh.WARNING)
                    else:
                        eh.warning(s)

        if not self._metadata_loaded:
            s = 'Failed to read metadata'
            if self.print_msg is not None:
                self.print_msg(s, eh.ERROR)
            else:
                eh.error(s)
            raise eh.LoadError


    # evt: mpv.MpvEvent
    # (Having this as an actual type hint will cause a crash if mpv is
    # not found, so it has to be a comment only)
    def _mpv_error_checker(self, evt):
        self._mpv_err = b'unknown error'
        evt_dict = evt.as_dict()
        self._loaded = evt_dict['event'] == b'file-loaded'
        if not self._loaded:
            try:
                self._mpv_err = evt_dict['file_error']
            except KeyError:
                pass
        return True


    def _load_metadata_libmpv(self):
        s = 'Reading metadata with libmpv...'
        if self.print_msg is not None:
            self.print_msg(s, eh.NORMAL)
        else:
            eh.debug(s)
        if os.path.isdir(self.inputfile):
            s = f'{self.inputfile} is a directory'
            if self.print_msg is not None:
                self.print_msg(s, eh.ERROR)
            else:
                eh.error(s.rstrip())
            raise eh.LoadError
        with mpv_cm(video='no', ao='null', pause='yes') as (err, player):
            if err is not None:
                s = str(err)
                if self.print_msg is not None:
                    self.print_msg(s, eh.ERROR)
                else:
                    eh.error(s.rstrip(),
                             prefix='mpv')
                raise eh.LoadError
            with player.prepare_and_wait_for_event(
                                                'file_loaded',
                                                 'end_file',
                                                 cond=self._mpv_error_checker,
                                                 timeout=5):
                player.command('loadfile',
                               com.string_to_raw(self.inputfile),
                               'replace')

            if self._loaded:
                params = player.audio_params
                self.file_metadata = player.metadata
            else:
                s = str(self._mpv_err, encoding='utf-8')
                if self.print_msg is not None:
                    self.print_msg(s, eh.ERROR)
                else:
                    eh.error(s.rstrip(),
                             prefix='mpv')
                raise eh.LoadError

        try:
            self.file_samplerate = params['samplerate']
        except (KeyError, TypeError):
            pass
        try:
            self.file_title = self.file_metadata['title']
        except (KeyError, TypeError):
            pass
        try:
            self.file_title = self.file_metadata['TITLE']
        except (KeyError, TypeError):
            pass
        try:
            self.file_track = self.file_metadata['track']
        except (KeyError, TypeError):
            pass
        try:
            self.file_track = self.file_metadata['TRACK']
        except (KeyError, TypeError):
            pass
        self._metadata_loaded = True



    def _load_metadata_ffprobe(self):
        if com.ffprobe_error:
            s = com.ffprobe_error
            if self.print_msg is not None:
                self.print_msg(s, eh.ERROR)
            else:
                eh.error(s.rstrip())
            raise eh.LoadError

        s = 'Reading metadata with ffprobe...'
        if self.print_msg is not None:
            self.print_msg(s, eh.NORMAL)
        else:
            eh.debug(s)
        info_command = [com.FFPROBE_BINARY]
        info_command += ['-hide_banner', '-show_streams', '-show_format']
        info_command += ['-i', self.inputfile]

        try:
            raw_info = sp.run(info_command,
                              check=True,
                              capture_output=True,
                              creationflags=_CREATIONFLAGS)
        except sp.CalledProcessError as err:
            s = str(err.stderr, encoding='utf-8')
            if self.print_msg is not None:
                self.print_msg(s, eh.ERROR)
            else:
                eh.error(s.rstrip(),
                         prefix=err.cmd[0])
            raise eh.LoadError

        self.file_metadata = {}

        for line in str(raw_info.stdout,
                        encoding='utf-8',
                        errors='surrogateescape').splitlines():
            linelist = line.partition('=')
            if linelist[0].startswith('TAG:'):
                self.file_metadata[linelist[0][4:]] = linelist[2]
            if linelist[0] == 'sample_rate':
                self.file_samplerate = int(linelist[2])
            if linelist[0] in ('TAG:TITLE', 'TAG:title'):
                self.file_title = linelist[2]
            if linelist[0] in ('TAG:TRACK', 'TAG:track'):
                self.file_track = linelist[2]

        self._metadata_loaded = True


    def load_data(self,
                  start=None,
                  end=None,
                  samplerate=None,
                  pad=None):
        """Get the audio data from the file.  This also loads metadata
        if it hasn't been done already.

        Parameters
        ----------
        start : str, optional
            Where in the file to start reading.  Passed to the -ss
            option of ffmpeg or the --start option of mpv.  Start at the
            beginning if None.  Default None.
        end : str, optional
            Where in the file to stop reading.  Passed to the -to option
            of ffmpeg or the --end option of mpv.  Go to the end if
            None.  Default None.
        samplerate : int, optional
            The sample rate to use, in Hz.  Overrides the sample rate
            read from the file header or specified at class
            instantiation.
        pad : Sequence, optional
            Should either be None or a Sequence of two ints specifying
            how many samples of silence to add to the beginning and end
            of the audio, respectively.  Padding ensures the FFT window
            doesn't miss anything.  None means no padding.  Default
            None.

        Raises
        ------
        eh.LoadError
            When there's a problem reading the data.
        """

        if not self._metadata_loaded:
            self.load_metadata()

        if samplerate is not None:
            self.samplerate = samplerate
        elif self.file_samplerate is not None:
            self.samplerate = self.file_samplerate
        else:
            self.samplerate = self.default_samplerate

        raw_audio = None
        for backend in self.try_sequence:
            if raw_audio:
                break
            if backend == ap.MPV_PIPE_OPTION:
                if mpv_error is not None:
                    if self.print_msg is not None:
                        self.print_msg(mpv_error, eh.ERROR)
                    else:
                        eh.error(mpv_error)
                    continue
                try:
                    raw_audio = self._load_data_libmpv_pipe(start,
                                                            end,
                                                            self.pitch,
                                                            self.tempo)
                except eh.LoadError:
                    s = 'libmpv failed'
                    if self.print_msg is not None:
                        self.print_msg(s, eh.WARNING)
                    else:
                        eh.warning(s)
            elif backend == ap.FFMPEG_OPTION:
                try:
                    raw_audio = self._load_data_ffmpeg(start,
                                                       end,
                                                       self.pitch,
                                                       self.tempo)
                except (eh.LoadError, FileNotFoundError):
                    s = 'ffmpeg failed'
                    if self.print_msg is not None:
                        self.print_msg(s, eh.WARNING)
                    else:
                        eh.warning(s)
            elif backend == ap.MPV_TEMPFILE_OPTION:
                if mpv_error is not None:
                    if self.print_msg is not None:
                        self.print_msg(mpv_error, eh.ERROR)
                    else:
                        eh.error(mpv_error)
                    continue
                try:
                    raw_audio = self._load_data_libmpv_tempfile(start,
                                                                end,
                                                                self.pitch,
                                                                self.tempo)
                except eh.LoadError:
                    s = 'libmpv failed'
                    if self.print_msg is not None:
                        self.print_msg(s, eh.WARNING)
                    else:
                        eh.warning(s)

        if raw_audio is None:
            s = 'Failed to read audio data'
            if self.print_msg is not None:
                self.print_msg(s, eh.ERROR)
            else:
                eh.error(s)
            raise eh.LoadError

        if pad is not None:
            padlist = [bytes(pad[0] * 2), bytes(pad[1] * 2)]
            self._audio_array = np.frombuffer(
                raw_audio.join(padlist),
                dtype='int16')
            self._len_audio_array = len(self._audio_array)
            self._len_unpadded_array = self._len_audio_array - (sum(pad[:2]))
        else:
            self._audio_array = np.frombuffer(raw_audio,
                                             dtype=np.int16)
            self._len_audio_array = len(self._audio_array)
            self._len_unpadded_array = self._len_audio_array

        self.file_duration = self._len_unpadded_array / self.samplerate


    def _load_data_libmpv_tempfile(self, start, end, pitch=None, tempo=None):
        raw_audio = None

        if sys.byteorder == 'big':
            output_codec = 'pcm_s16be'
        else:
            output_codec = 'pcm_s16le'

        pitch_t = pitch / tempo

        with tempfile.TemporaryDirectory(prefix='pretendpipe') as tmpdir:
            tmppath = os.path.join(tmpdir, 'audio_data_for_tuner')

            s = f'Reading audio with libmpv, using tempfile {tmppath}'
            if self.print_msg is not None:
                self.print_msg(s, eh.NORMAL)
            else:
                eh.debug(s)

            mpv_options = {
                            'video': 'no',
                            'ocopy_metadata': 'no',
                            'audio_channels': 'mono',
                            'audio_samplerate': f'{self.samplerate}',
                            'audio_normalize_downmix': 'yes',
                            'audio_pitch_correction': 'no',
                            'o': tmppath,
                            'of': 'data',
                            'oac': output_codec,
                          }
            if start:
                mpv_options['start'] = start
            if end:
                mpv_options['end'] = end
            if abs(tempo - 1.0) > .0005:
                mpv_options['speed'] = f'{tempo:.3f}'
            if abs(pitch_t - 1.0) > .0005:
                mpv_options['af'] = f'@rb:rubberband=pitch-scale={pitch_t:.3f}'
            with mpv_cm(**mpv_options) as (err, player):
                if err is not None:
                    s = f'{err.args[0]}: '
                    s += str(err.args[2][1], encoding='utf-8')
                    s += '='
                    s += str(err.args[2][2], encoding='utf-8')
                    if self.print_msg is not None:
                        self.print_msg(s, eh.ERROR)
                    else:
                        eh.error(s.rstrip(),
                                 prefix='mpv')
                    raise eh.LoadError
                with player.prepare_and_wait_for_event(
                                            'file_loaded',
                                             'end_file',
                                             cond=self._mpv_error_checker,
                                             timeout=5):
                    player.command('loadfile',
                                   com.string_to_raw(self.inputfile),
                                   'replace')
                if self._loaded:
                    player.wait_for_playback()
                    try:
                        with open(tmppath, 'rb') as f:
                            raw_audio = f.read()
                    except FileNotFoundError as exc:
                        if self.print_msg is not None:
                            self.print_msg(FNF_ERROR, eh.ERROR)
                        else:
                            eh.error(FNF_ERROR.rstrip())
                        raise eh.LoadError from exc
                else:
                    s = str(self._mpv_err, encoding='utf-8')
                    if self.print_msg is not None:
                        self.print_msg(s, eh.ERROR)
                    else:
                        eh.error(s.rstrip(),
                                 prefix='mpv')
                    raise eh.LoadError

        return raw_audio


    def _load_data_libmpv_pipe(self, start, end, pitch=None, tempo=None):
        s = 'Reading audio with libmpv, using named pipe...'
        if self.print_msg is not None:
            self.print_msg(s, eh.NORMAL)
        else:
            eh.debug(s)

        pitch_t = pitch / tempo

        raw_audio = None

        with namedpipe.NPopen(mode='rb') as pipe:
            mpv_options = {
                            'video': 'no',
                            'audio_channels': 'mono',
                            'audio_samplerate': f'{self.samplerate}',
                            'audio_normalize_downmix': 'yes',
                            'audio_pitch_correction': 'no',
                            'audio_format': 's16',
                            'ao': 'pcm',
                            'ao_pcm_waveheader': 'no',
                            'ao_pcm_file': pipe.path,
                          }
            if start:
                mpv_options['start'] = start
            if end:
                mpv_options['end'] = end
            if abs(tempo - 1.0) > .0005:
                mpv_options['speed'] = f'{tempo:.3f}'
            if abs(pitch_t - 1.0) > .0005:
                mpv_options['af'] = f'@rb:rubberband=pitch-scale={pitch_t:.3f}'
            with mpv_cm(**mpv_options) as (err, player):
                if err is not None:
                    s = f'{err.args[0]}: '
                    s += str(err.args[2][1], encoding='utf-8')
                    s += '='
                    s += str(err.args[2][2], encoding='utf-8')
                    if self.print_msg is not None:
                        self.print_msg(s, eh.ERROR)
                    else:
                        eh.error(s.rstrip(),
                                 prefix='mpv')
                    raise eh.LoadError
                with player.prepare_and_wait_for_event(
                                            'file_loaded',
                                             'end_file',
                                             cond=self._mpv_error_checker,
                                             timeout=5):
                    player.command('loadfile',
                                   com.string_to_raw(self.inputfile),
                                   'replace')

                if self._loaded:
                    pipestream = io.BufferedReader(pipe.wait())
                    raw_audio = pipestream.read()
                else:
                    s = str(self._mpv_err, encoding='utf-8')
                    if self.print_msg is not None:
                        self.print_msg(s, eh.ERROR)
                    else:
                        eh.error(s.rstrip(),
                                 prefix='mpv')
                    raise eh.LoadError

        return raw_audio


    def _load_data_ffmpeg(self, start, end, pitch=None, tempo=None):
        if com.ffmpeg_error:
            s = com.ffmpeg_error
            if self.print_msg is not None:
                self.print_msg(s, eh.ERROR)
            else:
                eh.error(s.rstrip())
            raise eh.LoadError

        s = 'Reading audio with ffmpeg...'
        if self.print_msg is not None:
            self.print_msg(s, eh.NORMAL)
        else:
            eh.debug(s)

        command = [com.FFMPEG_BINARY]
        command += ['-hide_banner', '-nostats', '-nostdin', '-vn']
        if start is not None:
            command += ['-ss', start]
        if end is not None:
            command += ['-to', end]
        command += ['-i', self.inputfile]
        command += ['-f', 's16le']
        if sys.byteorder == 'big':
            command += ['-acodec', 'pcm_s16be']
        else:
            command += ['-acodec', 'pcm_s16le']
        command += ['-ar', str(self.samplerate)]
        command += ['-ac', '1']
        if abs(tempo - 1.0) > .0005 or abs(pitch - 1.0) > .0005:
            command += ['-af',
                        f'rubberband=pitch={pitch:.3f}:tempo={tempo:.3f}']
        command += ['-']

        try:
            raw_audio = sp.run(command,
                               check=True,
                               capture_output=True,
                               creationflags=_CREATIONFLAGS)
        except sp.CalledProcessError as err:
            s = str(err.stderr, encoding='utf-8')
            if self.print_msg is not None:
                self.print_msg(s, eh.ERROR)
            else:
                eh.error(s.rstrip(),
                         prefix=err.cmd[0])
            raise eh.LoadError

        return raw_audio.stdout


    def fft(self,
            size=32768,
            overlap=2/3,
            power_correction=8/9,
            keep_all=False,
            check_unitarity=False,
            progress_hook=None,
            keep_audio_array=False):
        """Find the frequency spectrum using Welch's method FFT.

        Parameters
        ----------
        size : int, optional
            Parameter determining the number of frequency bins.  The
            actual number of bins will be size + 1, and the width of the
            window will be 2*size.  Default 32768.
        overlap : float, optional
            The amount of window overlap, in units of window size.
            Default 2/3.
        power_correction : float, optional
            The correction factor to compensate for overcounting or
            undercounting as a result of the amount of window overlap.
            Default 8/9.
        keep_all : bool, optional
            Whether to keep all the FFT results instead of discarding
            them after they've been added to the total.  Keeping them is
            needed for spectrograms to work.  Default False.
        check_unitarity : bool, optional
            Whether to calculate the `energy_in` and `energy_out`
            attributes.
        progress_hook : Callable, optional
            If not None, this will be called periodically with one
            argument, a float representing the amount of progress made
            so far on a scale of 0 to 1.  It should return True if
            processing should continue, and False to cancel.  Default
            None.
        keep_audio_array : bool, optional
            If True, the audio will be kept in memory after the
            analysis.  This is generally not necessary unless you intend
            to do multiple analyses with different options and don't
            want to have to run `load_data` again.
        """

        window = np.hanning(2*size)

        spectrum = np.zeros(size + 1)

        max_i = self._len_audio_array - 2*size

        if max_i <= 0:
            raise eh.ShortError

        num = 0
        window_step = round(2*size*(1 - overlap))

        if keep_all:
            spectrogram = np.zeros(
                (math.ceil(self._len_audio_array / window_step), size + 1))

        for i in range(0, max_i, window_step):
            chunk = self._audio_array[i:i + 2*size]
            fft = np.fft.rfft(window * chunk, norm='ortho')
            afft = np.abs(fft)
            afft **= 2
            np.add(spectrum, afft, out=spectrum)
            if keep_all:
                spectrogram[num] = afft
            num += 1
            if progress_hook:
                if not progress_hook(i / max_i):
                    raise eh.Interrupted

        spectrum[1:-1] *= 2
        spectrum *= power_correction

        if check_unitarity:
            audio_array_f = np.array(self._audio_array, dtype=np.float64)
            self.energy_in = np.sum(audio_array_f**2)
            self.energy_out = np.sum(spectrum)

        if not keep_audio_array:
            del self._audio_array

        spectrum /= self._len_unpadded_array * self._normalization_factor

        self._freqs = np.fft.rfftfreq(2*size, 1 / self.samplerate)

        self._decibels = 10 * np.log10(
            np.maximum(spectrum, np.full_like(spectrum, np.nextafter(0, 1))))

        if keep_all:
            spectrogram[1:-1] *= 2
            spectrogram *= power_correction
            spectrogram /= (self._len_unpadded_array
                            * self._normalization_factor)
            np.log10(spectrogram, out=spectrogram)
            spectrogram *= 10
            self._spectrogram = spectrogram

        self._size = size
        self._spectrum = spectrum
        self._window_step = window_step

        if progress_hook:
            progress_hook(1)


    def find_peaks(self,
                   low_cut=20,
                   high_cut=20000,
                   max_peaks=10,
                   dB_range=30):
        """Find prominent peaks in the spectrum and store them in the
        `peaks` attribute.

        Parameters
        ----------
        low_cut : int, optional
            Ignore peaks below this frequency, in Hz.  Default 20.
        high_cut : int, optional
            Ignore peaks above this frequency, in Hz.  Default 20000.
        max_peaks : int, optional
            The maximum number of peaks to find.  Default 10.
        dB_range : float, optional
            Ignore peaks this number of decibels below the highest peak.
            Default 30.

        Returns
        -------
        peaks : list
            A list of lists.  Each list consists of three floats:  The
            frequency of the peak in Hz, the prominence of the peak
            compared to nearby frequencies in dB, and the loudness of
            the peak in dB.
        """

        blur_size = max(self._size//64-1, 5)

        blur_window = np.hanning(blur_size)
        blurred = (np.convolve(self._decibels, blur_window, mode='same')
                   / np.sum(blur_window))

        spikes = self._decibels - blurred

        peaks = []

        for i in range(2, len(spikes) - 4):
            if self._freqs[i] < low_cut:
                continue
            if self._freqs[i] > high_cut:
                break
            if (spikes[i-2] < spikes[i]
                  and spikes[i-1] < spikes[i]
                  and spikes[i] > spikes[i+1]
                  and spikes[i+2] < spikes[i]):
                # Estimate the frequency of the peak by taking a weighted
                # average of three frequency bins.
                freq_est = _weighted_average(self._freqs[i-1:i+2],
                                             self._spectrum[i-1:i+2])

                # A rough estimate of the peak's power using quadratic
                # interpolation.  This is not very precise with a Hann
                # window.
                decibel_est = _quad_inter(self._freqs[i-1:i+2],
                                          self._decibels[i-1:i+2])

                peaks.append([freq_est, decibel_est - blurred[i], decibel_est])

        if len(peaks) > 0:
            peaks.sort(key=lambda x: x[1])
            peaks = peaks[-max_peaks:]
            while len(peaks) > 1 and peaks[-1][1] - peaks[0][1] > dB_range:
                peaks.pop(0)
            peaks.sort(key=lambda x: x[0])

        self.peaks = peaks
        self._low_cut = low_cut
        self._high_cut = high_cut
        return peaks


    def show_plot(self,
                  plot_type='log',
                  asynchronous = False,
                  title=None,
                  pitch=1.0,
                  update=False):
        """Show a plot of the spectrum.

        Parameters
        ----------
        plot_type : str, optional
            The type of plot.  Valid types are 'log', 'linear', or
            'spectrogram'.
        asynchronous : bool, optional
            If True, show the plot asynchronously without blocking.
            Default False.
        title : str, optional
            The title of the plot.  If None, file_title will be used.
            Default None.
        pitch : float, optional
            The pitch correction factor to apply to the audio in the plot.
        update : bool, optional
            If True, plots that are already being shown will be updated,
            but no new plots will be shown.  Default False.
        """

        if update and not self.plot_plotted:
            return

        # matplotlib is only ever used in this method.
        import matplotlib.pyplot as plt

        pitched_freqs = self._freqs * (pitch / self.pitch)

        plot_title = None
        if title is not None:
            plot_title = title
        elif self.file_title is not None:
            plot_title = self.file_title

        s = f'{self.inputfile} dB plot'
        if plot_type == 'log' or (update and plt.fignum_exists(s)):
            plt.figure(s, clear=True)
            if len(self.peaks) > 0:
                peaks_array = np.array(self.peaks).T
                plt.plot(pitched_freqs,
                         self._decibels,
                         peaks_array[0] * (pitch / self.pitch),
                         peaks_array[2],
                         '+')
            else:
                plt.plot(pitched_freqs, self._decibels)
            plt.xscale('log')
            plt.xlabel('Frequency (Hz)')
            plt.ylabel('Power (dB)')
            plt.axvline(self._low_cut * (pitch / self.pitch), color='.5')
            plt.axvline(self._high_cut * (pitch / self.pitch), color='.5')
            if plot_title:
                plt.suptitle(plot_title)
            if asynchronous:
                plt.ion()
            self.plot_plotted = True
            if not update:
                plt.show()
        s = f'{self.inputfile} power plot'
        if plot_type == 'linear' or (update and plt.fignum_exists(s)):
            plt.figure(s, clear=True)
            if len(self.peaks) > 0:
                peaks_array = np.array(self.peaks).T
                plt.plot(pitched_freqs, self._spectrum,
                         peaks_array[0] * (pitch / self.pitch),
                         10**(peaks_array[2]/10),
                         '+')
            else:
                plt.plot(pitched_freqs, self._spectrum)
            plt.xscale('log')
            plt.xlabel('Frequency (Hz)')
            plt.ylabel('Power')
            plt.axvline(self._low_cut * (pitch / self.pitch), color='.5')
            plt.axvline(self._high_cut * (pitch / self.pitch), color='.5')
            if plot_title:
                plt.suptitle(plot_title)
            if asynchronous:
                plt.ion()
            self.plot_plotted = True
            if not update:
                plt.show()
        if plot_type == 'spectrogram':
            plt.figure(f'{self.inputfile} {plot_type}', clear=True)
            freq_spacing = pitched_freqs[1] - pitched_freqs[0]
            plotfreqs = np.zeros(len(pitched_freqs) + 1)
            plotfreqs[0:-1] = pitched_freqs - freq_spacing/2
            plotfreqs[-1] = plotfreqs[-2] + freq_spacing

            times = np.linspace(
              (-self._window_step/2) / self.samplerate,
              (self._len_audio_array - self._window_step/2) / self.samplerate,
              num=math.ceil(self._len_audio_array / self._window_step) + 1)

            plt.pcolormesh(plotfreqs, times, self._spectrogram)
            plt.xscale('log')
            plt.xlim(self._low_cut, self._high_cut)
            if plot_title:
                plt.suptitle(plot_title)
            if asynchronous:
                plt.ion()
            plt.show()
