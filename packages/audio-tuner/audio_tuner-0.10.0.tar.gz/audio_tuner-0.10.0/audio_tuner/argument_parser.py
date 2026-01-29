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


"""Functions and classes for handling command line arguments given to
the Audio Tuner command line and GUI programs.
"""


__author__ = 'Jessie Blue Cassell'


__all__ = [
            'arg_error',
            'validate',
            'get_arg_parser',
            'merge_args',
            'ArgumentParser',
            'MPV_PIPE_OPTION',
            'MPV_TEMPFILE_OPTION',
            'FFMPEG_OPTION',
            'CONFIG_PATH',
          ]


import sys
import argparse
import logging
import os
import configparser

from platformdirs import PlatformDirs

import audio_tuner.error_handling as eh
import audio_tuner.common as com


_CONFIG_FILE = 'audiotuner.conf'

if os.name == 'nt':
    _APPNAME = 'Audio Tuner'
else:
    _APPNAME = 'audiotuner'

_APPAUTHOR = 'BlueSloth'

_dirs = PlatformDirs(_APPNAME, _APPAUTHOR)
CONFIG_PATH = os.path.join(_dirs.user_config_dir, _CONFIG_FILE)

# Strings that can be given in the config file to specify which backends
# to try.
MPV_PIPE_OPTION = 'mpv_pipe'
MPV_TEMPFILE_OPTION = 'mpv_tempfile'
FFMPEG_OPTION = 'ffmpeg'

MPV_NOT_FOUND_ERROR = 'libmpv not found.  Disabling mpv backends.'
if os.name == 'nt':
    MPV_NOT_FOUND_HELP = ('Please install libmpv from'
            '\nhttps://github.com/shinchiro/mpv-winbuild-cmake/releases.')
else:
    MPV_NOT_FOUND_HELP = (
"Please install the package providing libmpv using your system's"
"\npackage mananger.  It may be called something like libmpv2,"
"\nmpv-devel or mpv-libs.")

def _get_default_args(gui_mode: bool = False) -> argparse.Namespace:
    args = argparse.Namespace()

    args.file = []
    args.tuning = 'equal_temperament'
    args.ref_note = 'A4'
    args.ref_freq = 440.0
    args.start = None
    args.end = None
    args.low_cut = 20.0
    args.high_cut = 15000.0
    args.dB_range = 30.0
    args.max_peaks = 10
    args.size_exp = 15
    args.samplerate = None
    args.nopad = False
    args.backends = [MPV_PIPE_OPTION]
    args.config = CONFIG_PATH
    if not gui_mode:
        args.color = False
        args.plot = None
        args.verbose = False
        args.debug = False

    return args


def _parse_config_file(path: str, print_msg: callable = None) -> dict:
    configs = None

    file_parser = configparser.ConfigParser(allow_no_value=True,
                                            empty_lines_in_values=False)
    file_parser.optionxform = str
    with open(path, encoding='utf-8') as f:
        try:
            file_parser.read_file(f, path)
        except configparser.Error as err:
            if print_msg:
                print_msg(err, eh.ERROR)
            else:
                logging.error(err)
            sys.exit(2)

    file_defaults = file_parser['DEFAULT']

    file_argv = []
    for key in file_defaults:
        s = '--' + key
        if value := file_defaults[key]:
            s += '=' + value
        file_argv.append(s)

    parser = get_arg_parser(config_mode=True, print_msg=print_msg)
    parser.usage = argparse.SUPPRESS
    configs = parser.parse_args(file_argv)
    if not validate(configs,
                    prog=parser.prog,
                    config_mode=True,
                    print_msg=print_msg):
        sys.exit(2)

    return configs


def merge_args(cli_args: argparse.Namespace,
               print_msg: callable = None) -> argparse.Namespace:
    """Merges together command line arguments, the config file and the
    defaults.  Command line arguments have priority over the config
    file, which has priority over built in defaults.  It also removes
    backends from the backend list if the associated binary or library
    can't be found.

    Parameters
    ----------
    cli_args : argparse.Namespace
        The namespace object resulting from parsing the command line
        arguments.  It should have the `gui_mode` attribute added to it,
        a bool indicating whether or not to use the GUI version of the
        default options.
    print_msg : callable, optional
        A function to be called if a message needs to be printed.  The
        call signature should be:
            f(msg: str, level: int) -> None
        where `msg` is the message and `level` is one of the severity
        levels defined in audio_tuner.error_handling (ERROR, WARNING,
        NORMAL or DEBUG).

    Returns
    -------
    The argparse.Namespace object that resulted from merging the command
    line, config file and default arguments.
    """

    args = _get_default_args(cli_args.gui_mode)

    if cli_args.config is not None:
        args.config = cli_args.config

    config_args = None
    if args.config:
        try:
            config_args = _parse_config_file(args.config, print_msg=print_msg)
        except SystemExit:
            s = f'ignoring {args.config}'
            if print_msg:
                print_msg(s, eh.WARNING)
            else:
                logging.warning(s)
        except OSError as err:
            if cli_args.config is not None:
                if print_msg:
                    print_msg(err, eh.ERROR)
                logging.error(err)
                sys.exit(2)

    for arg in vars(args):
        if arg == 'config':
            continue
        if config_args is not None:
            if config_arg := getattr(config_args, arg, None):
                setattr(args, arg, config_arg)
        if cli_arg := getattr(cli_args, arg, None):
            setattr(args, arg, cli_arg)

    backends_set = set(args.backends)
    mpv_set = {MPV_PIPE_OPTION, MPV_TEMPFILE_OPTION}
    if com.mpv_error is not None and not backends_set.isdisjoint(mpv_set):
        arg_error(MPV_NOT_FOUND_ERROR,
                  print_msg=print_msg)
        if print_msg:        
            print_msg(MPV_NOT_FOUND_HELP, eh.WARNING)
        else:
            logging.warning(MPV_NOT_FOUND_HELP)
        args.backends = [x for x in args.backends if x not in mpv_set]

    if FFMPEG_OPTION in backends_set:
        ffbad = False
        if com.ffprobe_error is not None:
            ffbad = True
            arg_error('ffprobe not found.', print_msg=print_msg)
        if com.ffmpeg_error is not None:
            ffbad = True
            arg_error('ffmpeg not found.', print_msg=print_msg)
        if ffbad:
            arg_error('Disabling ffmpeg backends.', print_msg=print_msg)
            args.backends = [x for x in args.backends if x != FFMPEG_OPTION]

    return args


def arg_error(msg, argument=None, prog=None, print_msg=None):
    """Print argparse style error messages indicating a command line
    argument problem to stderr.

    Parameters
    ----------
    msg : str
        A message describing the problem.
    argument : optional
        The problematic argument.
    prog : str
        The name of the program.  If None, it will be taken from
        sys.argv.  Default None.
    print_msg : callable, optional
        A function to be used to print the message.  The call signature
        should be:
            f(msg: str, level: int) -> None
        where `msg` is the message and `level` is one of the severity
        levels defined in audio_tuner.error_handling (ERROR, WARNING,
        NORMAL or DEBUG).
        It should handle printing the program name itself, since `prog`
        will be ignored if `print_msg` is not None.
        Default None, in which case the `print` builtin is used.
    """

    if print_msg is None:
        if prog is None:
            prog = os.path.basename(sys.argv[0])
        string = prog + ': error: '
    else:
        string = ''
    if argument is not None:
        string += f'argument {argument}: '
    string += msg
    if print_msg:
        print_msg(string, eh.ERROR)
    else:
        print(string, file=sys.stderr)



class _TuningAction(argparse.Action):
    """Handle abbreviated tuning system names"""

    def __call__(self, parser, namespace, values, option_string=None):
        if parser.config_mode:
            option_string = option_string.lstrip('-')

        tunings = ['equal_temperament', 'pythagorean']

        out = [t for t in tunings if t.startswith(values.lower())]

        if len(out) > 1:
            matches = ', '.join(out)
            arg_error(f'ambiguous choice: {values} could match {matches}',
                      option_string,
                      prog=parser.prog)
            sys.exit(2)
        elif len(out) < 1:
            tunings_str = ', '.join(tunings)
            arg_error(f'invalid choice: {values}'
                      f' (choose from {tunings_str})',
                      option_string,
                      prog=parser.prog)
            sys.exit(2)
        else:
            setattr(namespace, self.dest, out[0])


# Copied from argparse._VersionAction instead of subclassed because
# _VersionAction isn't public API
class _RawVersionAction(argparse.Action):
    """Print version string without messing with the formatting."""

    # pylint: disable=redefined-builtin
    # (It thinks `help` is being redefined)

    def __init__(self,
                 option_strings,
                 version=None,
                 dest=argparse.SUPPRESS,
                 default=argparse.SUPPRESS,
                 help="show program's version number and exit"):
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help)
        self.version = version

    def __call__(self, parser, namespace, values, option_string=None):
        version = self.version
        if version is None:
            version = parser.version
        print(version)
        parser.exit()


class _DefaultConfPathAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        print(CONFIG_PATH)
        parser.exit()


class ArgumentParser(argparse.ArgumentParser):
    """An argument parser class that inherits from argparse.ArgumentParser.

    Parameters
    ----------
    gui_mode : bool : optional
        Namespace objects returned by the parsing methods will have this
        added to them as an attribute, to prepare them to be passed to
        merge_args.  Set this to True if you're parsing command line
        options passed to the GUI frontend.  Default False.
    config_mode : bool, optional
        If true, the `error` method strips the `--` prefixes out of the
        error messages to make them match config file arguments instead
        of command line arguments.  Default False
    print_msg : callable, optional
        A function to be called if a message needs to be printed.  The
        call signature should be:
            f(msg: str, level: int) -> None
        where `msg` is the message and `level` is one of the severity
        levels defined in audio_tuner.error_handling (ERROR, WARNING,
        NORMAL or DEBUG).

    Those three parameters are also available as attributes.

    All argparse.ArgumentParser parameters are also accepted.
    """

    def __init__(self,
                 *posargs,
                 gui_mode=False,
                 config_mode=False,
                 print_msg=None,
                 **kwargs):
        super().__init__(*posargs, **kwargs)
        self.gui_mode = gui_mode
        self.config_mode = config_mode
        self.print_msg = print_msg

    def parse_args_gm(self, *posargs, **kwargs):
        """Like argparse.ArgumentParser.parse_args, except it also adds
        the gui_mode attribute to the resulting namespace object.
        """

        args = super().parse_args(*posargs, **kwargs)
        args.gui_mode = self.gui_mode
        return args

    def parse_known_args_gm(self, *posargs, **kwargs):
        """Like argparse.ArgumentParser.parse_known_args, except it also
        adds the gui_mode attribute to the resulting namespace object.
        """

        args, argv = super().parse_known_args(*posargs, **kwargs)
        args.gui_mode = self.gui_mode
        return args, argv

    # NOTE `format_usage` and `format_help` will need to be updated if
    # the relevant argparse internals change.

    # Copied from argparse with some additions to appease help2man.
    def format_usage(self):
        formatter = self._get_formatter()
        formatter.add_usage(self.usage, self._actions,
                            self._mutually_exclusive_groups,
                            prefix='Usage: ') # Added for help2man
        return formatter.format_help()

    # Copied from argparse with some additions to appease help2man.
    def format_help(self):
        formatter = self._get_formatter()

        # usage
        formatter.add_usage(self.usage, self._actions,
                            self._mutually_exclusive_groups,
                            prefix='Usage: ') # Added for help2man

        # description
        formatter.add_text(self.description)

        # Added for help2man
        formatter.add_text('Options:')

        # positionals, optionals and user-defined groups
        # pylint: disable=protected-access
        for action_group in self._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_text(action_group.description)
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()

        # epilog
        formatter.add_text(self.epilog)

        # determine help from format above
        return formatter.format_help()

    def error(self, message):
        """Print an error message and raise SystemExit.

        Parameters
        ----------
        message : str
            The error message.
        """

        if self.config_mode:
            message = message.replace(' --', ' ')
        if self.print_msg is not None:
            self.print_msg(message, eh.ERROR)
            sys.exit(2)
        else:
            super().error(message)


def validate(args, prog=None, config_mode=False, print_msg=None):
    """Validate a namespace object and print error messages if there's a
    problem.

    Parameters
    ----------
    args : argparse.Namespace
        The namespace to validate.
    prog : str, optional
        The name of the program for use in error messages.  If None, it
        will be taken from sys.argv.  Default None.
    config_mode : bool, optional
        if True, don't include `--` prefixes in error messages.
    print_msg : callable, optional
        A function to be called if a message needs to be printed.  The
        call signature should be:
            f(msg: str, level: int) -> None
        where `msg` is the message and `level` is one of the severity
        levels defined in audio_tuner.error_handling (ERROR, WARNING,
        NORMAL or DEBUG).

    Returns
    -------
    True if everything is ok, False otherwise.
    """

    args_ok = True
    if prog is None:
        prog = os.path.basename(sys.argv[0])
    if config_mode:
        prefix = ''
    else:
        prefix = '--'

    if ((args.high_cut is not None and args.high_cut <= 0)
      or (args.low_cut is not None and args.low_cut <= 0)
      or (args.high_cut is not None
          and args.low_cut is not None
          and args.high_cut <= args.low_cut)):
        arg_error(f'invalid range: {args.low_cut} to {args.high_cut}',
                  f'{prefix}low_cut/{prefix}high_cut',
                  prog=prog,
                  print_msg=print_msg)
        args_ok = False

    if args.dB_range is not None and args.dB_range < 0:
        arg_error(f'invalid value: {args.dB_range} (must not be negative)',
                  f'{prefix}dB_range',
                  prog=prog,
                  print_msg=print_msg)
        args_ok = False

    if args.max_peaks is not None and args.max_peaks <= 0:
        arg_error(f'invalid value: {args.max_peaks} (must be positive)',
                  f'{prefix}max_peaks', 
                  prog=prog,
                  print_msg=print_msg)
        args_ok = False

    if args.ref_freq is not None and args.ref_freq <= 0:
        arg_error(f'invalid value: {args.ref_freq} (must be positive)',
                  f'{prefix}ref_freq',
                  prog=prog,
                  print_msg=print_msg)
        args_ok = False

    if args.size_exp is not None and args.size_exp < 2:
        arg_error(f'invalid value: {args.size_exp} (must be at least 2)',
                  f'-s/{prefix}size_exp',
                  prog=prog,
                  print_msg=print_msg)
        args_ok = False

    if args.samplerate is not None and args.samplerate <= 0:
        arg_error(f'invalid value: {args.samplerate} (must be positive)',
                  f'{prefix}samplerate',
                  prog=prog,
                  print_msg=print_msg)
        args_ok = False

    if args.backends is not None:
        backends_set = set(args.backends)
        good_set = {MPV_PIPE_OPTION, FFMPEG_OPTION, MPV_TEMPFILE_OPTION}
        if args.backends is not None and not backends_set <= good_set:
            bad_values = backends_set - good_set
            arg_error(f'invalid value(s) {bad_values}',
                      f'{prefix}backends',
                      prog=prog,
                      print_msg=print_msg)
            args_ok = False

    return args_ok


def get_arg_parser(version=None,
                   description=None,
                   gui_mode=False,
                   config_mode=False,
                   print_msg=None):
    """Generate an argument parser that parses Audio Tuner options.

    Parameters
    ----------
    version : str, optional
        The string to print if the --version argument is given to the
        parser.  Unlike argparse's original parser, it will print it as
        is, without messing with the formatting.  If None, there will be
        no --version option.  Default None.
    description : str, optional
        A description of Audio Tuner.
    gui_mode : bool, optional
        If True, make a parser for the GUI rather than the CLI.  Default
        False.
    config_mode : bool, optional
        If True, make a parser for config file arguments.
    print_msg : callable, optional
        A function to be called if a message needs to be printed.  The
        call signature should be:
            f(msg: str, level: int) -> None
        where `msg` is the message and `level` is one of the severity
        levels defined in audio_tuner.error_handling (ERROR, WARNING,
        NORMAL or DEBUG).

    Returns
    -------
    ArgumentParser
    """

    if gui_mode:
        _usage = '%(prog)s [options] [file...]'
    else:
        _usage = '%(prog)s [options] file [file ...]'

    parser = ArgumentParser(
        usage=_usage,
        description=description,
        epilog=('Available tuning systems are "equal_temperament" and'
                ' "pythagorean".  Frequencies are in Hz.'),
        add_help=False,
        gui_mode=gui_mode,
        config_mode=config_mode,
        print_msg=print_msg)

    if gui_mode:
        file_nargs = '*'
    else:
        file_nargs = '+'

    if not config_mode:
        parser.add_argument(
            'file',
            nargs=file_nargs,
            help=('File(s) to analyze.'))

    tuning_opts = parser.add_argument_group('tuning options')

    tuning_opts.add_argument(
        '--tuning',
        action=_TuningAction,
        help='Use SYSTEM as the tuning system.  Default: equal_temperament',
        metavar='SYSTEM')

    tuning_opts.add_argument(
        '--ref_note',
        help='Use NOTE as the frequency reference note.  Default: A4',
        metavar='NOTE')

    tuning_opts.add_argument(
        '--ref_freq',
        type=float,
        help='Frequency of the reference note.',
        metavar='FREQ')

    anal_opts = parser.add_argument_group('analysis options')

    anal_opts.add_argument(
        '--start',
        help='Ignore the audio before TIME.',
        metavar='TIME')

    anal_opts.add_argument(
        '--end',
        help='Ignore the audio after TIME.',
        metavar='TIME')

    anal_opts.add_argument(
        '--low_cut',
        type=float,
        help='Ignore frequencies below FREQ.  Default: 20',
        metavar='FREQ')

    anal_opts.add_argument(
        '--high_cut',
        type=float,
        help='Ignore frequencies above FREQ.  Default: 15000',
        metavar='FREQ')

    anal_opts.add_argument(
        '--dB_range',
        type=float,
        help=('Ignore frequencies RANGE dB fainter than the highest peak.'
              '  Default: 30'),
        metavar='RANGE')

    anal_opts.add_argument(
        '--max_peaks',
        type=int,
        help='Maximum number of frequencies to show.  Default: 10',
        metavar='N')

    if (not gui_mode) or config_mode:
        output_opts = parser.add_argument_group('output options')

        output_opts.add_argument(
            '-c', '--color',
            action='store_true',
            help='Force color output even if stdout is a pipe.')

        output_opts.add_argument(
            '-p', '--plot',
            choices=['log', 'linear', 'spectrogram'], nargs='?', const='log',
            help='Show a plot of the spectrum.  The default type is "log".')

    low_opts = parser.add_argument_group('low level options')

    low_opts.add_argument(
        '-s', '--size_exp',
        type=int,
        help=("Use 2^N + 1 frequency bins in the spectrum."
              "  Default: 15 (32769 bins).  Adjust this with care,"
              " and don't go above 19 unless you know what you're doing."),
        metavar='N')

    low_opts.add_argument(
        '--samplerate',
        type=int,
        help='Convert the audio to a sample rate of FREQ.',
        metavar='FREQ')

    low_opts.add_argument(
        '--nopad',
        action='store_true',
        help="Don't pad the audio with zeros at the beginning and end.")

    if config_mode:
        low_opts.add_argument(
            '--backends',
            type=lambda y: [x.strip(' ') for x in y.strip(', ').split(',')]
            )

    if (not gui_mode) or config_mode:
        low_opts.add_argument(
            '--verbose',
            action='store_true',
            help='Enable output of verbose calculation details.')

        low_opts.add_argument(
            '--debug',
            action='store_true',
            help='Enable debugging output.')

    misc_opts = parser.add_argument_group('miscellaneous options')

    if not config_mode:
        misc_opts.add_argument(
            '--config',
            help='Which configuration file to read.  The default varies by'
                 ' platform.  Use the `--default_config_path` option to'
                 ' find out what it is on your system.')

        misc_opts.add_argument(
            '--default_config_path',
            nargs=0,
            help='Show the default path of the configuration file and exit.',
            action=_DefaultConfPathAction)

        if version is not None:
            misc_opts.add_argument(
                '--version',
                action=_RawVersionAction,
                version=version,
                help='show version information and exit')

        misc_opts.add_argument(
            '-h', '--help',
            action='help',
            help='show this help message and exit')

    return parser
