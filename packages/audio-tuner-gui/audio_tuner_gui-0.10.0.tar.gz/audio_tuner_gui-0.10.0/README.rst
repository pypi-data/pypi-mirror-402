Audio Tuner GUI
===============

This is the GUI front end for Audio Tuner, a tool for musicians that analyzes
and corrects the pitch of recorded audio.

It's under active development, with more features and usability improvements
planned for future versions.  The current version is already usable, however.

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

Dependencies
~~~~~~~~~~~~

**audio-tuner-gui** requires **Python version 3.11 or higher**, **libmpv2**,
and the `audio-tuner`_ and `PyQt6`_ python packages.

Note that pip is not able to install **libmpv2**.  If your operating system
has a package manager, use that to install it.  See the `documentation`_
for details.

Audio Tuner can be configured to use **ffmpeg** and **ffprobe** instead of
libmpv2, at the cost of reduced functionality in the GUI.

.. _documentation: https://audio-tuner.readthedocs.io/en/latest/
.. _audio-tuner: https://pypi.org/project/audio-tuner/
.. _PyQt6: https://www.riverbankcomputing.com/software/pyqt/

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

audio-tuner:  https://pypi.org/project/audio-tuner/
