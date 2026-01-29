Audio Tuner
===========

A tool for musicians that analyzes and corrects the pitch of recorded audio.

This package provides the python library and a simple CLI front end.  A GUI
front end is also available in the `audio-tuner-gui`_ package that can play
and export audio with the pitch corrected.

.. _audio-tuner-gui:  https://pypi.org/project/audio-tuner-gui/

Motivation
~~~~~~~~~~

A surprisingly high proportion of recorded music doesn't conform to any
standard tuning system.  You expect an A4 to be 440 Hz, but when you try to
play along you realize it's not.  Audio Tuner is a tool for measuring the
frequencies in an audio recording so it can be corrected if necessary.  It's
designed to be convenient enough to use that you can do it with a musical
instrument strapped to you.

The primary use case is to correct the tuning of your favorite songs so you
can practice playing an instrument by playing along with them, but it can be
used in any situation where you need to analyze and correct the pitch of a
recording.

What it's not
~~~~~~~~~~~~~

Audio Tuner is not autotune.  It pitch corrects entire songs, not individual
notes.

CLI Usage
~~~~~~~~~

Type 'tuner' at a shell prompt followed by the name(s) of the file(s) you
want to analyze.

For more detailed usage information, run:

.. code:: bash

    tuner --help

Dependencies
~~~~~~~~~~~~

Audio Tuner requires **Python version 3.11 or higher** and **libmpv2**.  In
addition, The following dependencies will be installed automatically by pip or
pipx:

* `numpy`_
* `python-mpv`_
* `namedpipe`_ (Only on Windows)
* `platformdirs`_

.. _numpy: https://www.numpy.org
.. _python-mpv: https://github.com/jaseg/python-mpv
.. _namedpipe: https://github.com/python-ffmpegio/python-namedpipe
.. _platformdirs: https://github.com/platformdirs/platformdirs

Note that pip is not able to install **libmpv2**.  If your operating system
has a package manager, use that to install it.  See the `documentation`_
for details.

Audio Tuner can be configured to use **ffmpeg** and **ffprobe** instead of
libmpv2, but this is not recommended if you install the GUI.

.. _documentation: https://audio-tuner.readthedocs.io/en/latest/

Free as in Freedom
~~~~~~~~~~~~~~~~~~

Audio Tuner is licensed under the `GNU General Public License`_ version 3 or
later.

.. _GNU General Public License: https://gnu.org/licenses/gpl.html

See
`What is Free Software? <https://www.gnu.org/philosophy/free-sw.html>`_
and
`Copyleft: Pragmatic Idealism
<https://www.gnu.org/philosophy/pragmatic.html>`_.

Versioning
~~~~~~~~~~

Audio Tuner attempts to use `Semantic Versioning`_, but with `PEP 440`_
compatible version numbers.

New versions of the base Audio Tuner package and Audio Tuner GUI are released
at the same time with the same version numbers.  The API is already reasonably
stable, but of course nothing's guaranteed until it reaches version 1.0.0.  

.. _Semantic Versioning: https://semver.org
.. _PEP 440: https://peps.python.org/pep-0440/

See Also
~~~~~~~~

audio-tuner-gui:  https://pypi.org/project/audio-tuner-gui/
