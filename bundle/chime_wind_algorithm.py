# SPDX-FileCopyrightText: Copyright (c) 2023 JG for Cedar Grove Maker Studios
# SPDX-License-Identifier: MIT

"""
`chime_wind_algorithm`
===============================================================================
A test of a windchime wind speed algorithm.

* Author(s): JG for Cedar Grove Maker Studios

Implementation Notes
--------------------

**Software and Dependencies:**
* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads
"""

import time
import board
import random
import audiobusio
import audiomixer
from simpleio import map_range
from cedargrove_chime import Chime, Scale, Voice, Material, Striker

# Instantiate I2S output and mixer buffer for synthesizer
audio_output = audiobusio.I2SOut(
    bit_clock=board.D12, word_select=board.D9, data=board.D6
)
mixer = audiomixer.Mixer(
    sample_rate=11020, buffer_size=4096, voice_count=1, channel_count=1
)
audio_output.play(mixer)

# Set the overall output volume level
mixer.voice[0].level = 0.8

# Instantiate the chime synth with mostly default parameters
chime = Chime(mixer.voice[0], scale=Scale.HarryDavidPear)

# Play scale notes sequentially at full volume
for index, note in enumerate(chime.scale):
    chime.strike(note, 1)
    time.sleep(0.4)
time.sleep(1)

WIND_SPEED = 0

while True:
    """Play chimes in proportion to wind speed.
    Builds an index list of notes to play (note sequence). It's assumed that
    the chime tubes are mounted in a circle and that no more than half the
    tubes could sound when the striker moves due to wind.
    The initial chime tube note (chime_index[0]) is selected randomly from
    chime.scale. The inital struck note will be followed by up adjacent notes
    either to the right or left as determined by the random direction variable.
    The playable note indicies are contained in the chime_index list.
    Note amplitude and the delay between note sequences is proportional to
    the wind speed."""

    """Populate the chime_index list with the inital note then add the
    additional notes."""
    chime_index = []
    chime_index.append(random.randrange(len(chime.scale)))

    direction = random.choice((-1, 1))
    for count in range(1, len(chime.scale) // 2):
        chime_index.append((chime_index[count-1] + direction) % len(chime.scale))

    """Randomly select the number of notes to play in the sequence based on the
    length of the chime_index list."""
    notes_to_play = random.randrange(len(chime_index) + 1)

    """Play the note sequence with a random delay between each."""
    note_amplitude = map_range(WIND_SPEED, 0, 50, 0.4, 1.0)
    for count in range(notes_to_play):
        chime.strike(chime.scale[chime_index[count]], note_amplitude)
        time.sleep(random.randrange(10, 60) * 0.01)  # random delay of 0.10 to 0.50 seconds

    """Delay the next note sequence inversely based on wind speed plus a
    random interval."""
    time.sleep(map_range(WIND_SPEED, 0, 50, 2.0, 0.01) + (random.random()/2))
