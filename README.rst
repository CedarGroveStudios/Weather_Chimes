Weather Chimes
##############


Introduction
------------

.. image:: https://img.shields.io/discord/327254708534116352.svg
    :target: https://adafru.it/discord
    :alt: Discord

.. image:: https://github.com/CedarGroveStudios/Weather_Chimes/workflows/Build%20CI/badge.svg
    :target: https://github.com/CedarGroveStudios/Weather_Chimes/actions
    :alt: Build Status

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    :alt: Code Style: Black

A CircuitPython project for "windless" electronic chimes that play in accordance with the outdoor wind speed.

.. image:: https://github.com/CedarGroveStudios/CircuitPython_AD5245/blob/master/media/AD5245_breakout_for_fritzing.png

The `Weather Chimes` project connects to the Adafruit NTP service for network time and to OpenWeatherMap.org for wind
speed data. The wind speed data is retrieved every twenty minutes and is used to adjust wind chime playback
in a pseudo random pattern. The chime voice synthesizer is provided by the ``CircuitPython_Chimes`` class
and for this project, is sent to an Adafruit MAX98357A amplifier driving a Adafruit 40mm 4-ohm 3-watt speaker.
Although an Unexpected Maker Feather S2 was used for this project, the code should work on just about any
ESP32 device that's capable of running CircuitPython.

The `Weather Chimes` project consists of two code files, ``weather_chimes_code.py`` and ``weather_chimes_wifi.py``.
The ``weather_chimes_code.py`` code is imported via the default ``code.py`` file contained in the Feather S2's root
directory. This code contains the primary non-wifi device definitions and the master ``while...`` loop that plays
the chimes. It also imports the ``WeatherChimesWiFi`` class from ``weather_chimes_wifi.py``.

The WiFi class takes care of all the networking details for connecting and retrieving data from the network services
and weather data API. It also provide helpers for updating and retrieving time and weather as well as properties
for including the essential time and wind speed.

Achieving a realistic pseudo-random chime playback proportional to wind speed involves two factors. First, the
amplitude (audio volume) of the chime notes is directly proportional to wind speed, varying from 40% to 100%
amplitude. Next, the delay between clusters of notes is inversely proportional to wind speed; the delay time interval
ranges proportionally from 2 seconds to 10 milliseconds. A random delay of up to 0.5 second is added to the
calculated delay time interval.

It's assumed that the chime tubes are mounted in a circle and that no more than half the tubes will sound when
the striker moves due to wind. The ``Chime.strike`` method randomly selects the first note to play from the
chime scale and randomly determines the number of notes to play. The initial note will be followed by a cluster
of adjacent notes either to the right or left as determined by a random direction variable and the number of
notes to play, each played in sequence after a random delay that ranges from 0.1 to 0.5 seconds. This algorithm
mimics the observed behavior of the chime striker since it usually moves away from the first struck tube,
hitting a few adjacent chime tubes.

The ``CircuitPython_Chime`` class does the hard work of building a ``synthio`` object with all the overtones and
ADSR envelope characteristics of a set of tubular chimes. The class contains a collection of selectable musical
songs ("scales"); in this case, an emulation of a 1970's `Harry and David Pear` six-tube garden chime scale was selected
because it is a family heirloom with special meaning. To customize the chime, refer to the documentation in the
``CircuitPython_Chime`` repo.




Dependencies
------------
This class depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_
* `CedarGrove CircuitPython_Chime <https://github.com/CedarGroveStudios/CircuitPython_Chime>`_
* `CedarGrove CircuitPython_MIDI_Tools <https://github.com/CedarGroveStudios/CircuitPython_MIDI_Tools>`_

Please ensure all dependencies are available on the CircuitPython filesystem.
This is easily achieved by downloading
`the Adafruit library and driver bundle <https://circuitpython.org/libraries>`_
or individual libraries can be installed using
`circup <https://github.com/adafruit/circup>`_.

Usage Example
-------------
`YouTube video of a test of the Weather_Chimes project <https://youtu.be/85vy7aG6j2c?si=KKtJh1J6P5rkMtYC>`_


Documentation
-------------
...


Planned Updates
---------------
...


Acknowledgements and Thanks
---------------------------
* Lee Hite, '`Tubular Bell Chimes Design Handbook`' for the analysis of tubular chime physics and overtones
* C. McKenzie, T. Schweisinger, and J. Wagner, '`A Mechanical Engineering Laboratory Experiment
  to Investigate the Frequency Analysis of Bells and Chimes with Assessment`' for the analysis
  of bell overtones;
* Liz Clark, '`Circle of Fifths Euclidean Synth with synthio and CircuitPython`' Adafruit Learning Guide
  for the waveform and noise methods;
* Todd Kurt for fundamentally essential `synthio` hints, tricks, and examples
  (https://github.com/todbot/circuitpython-synthio-tricks).

Also, special thanks to Jeff Epler and Adafruit for the comprehensive design and implementation
of the amazing CircuitPython `synthio` module.


