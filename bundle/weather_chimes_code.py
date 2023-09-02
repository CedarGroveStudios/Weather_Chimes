# SPDX-FileCopyrightText: Copyright (c) 2023 JG for Cedar Grove Maker Studios
# SPDX-License-Identifier: MIT

"""
`weather_chimes_code`
===============================================================================
IoT-connected windless garden chimes for the Feather S2.

* Author(s): JG for Cedar Grove Maker Studios

Implementation Notes
--------------------

**Hardware:**
* Feather S2 (ESP32-S2)

**Software and Dependencies:**
* CedarGrove CircuitPython_Chime:
  https://github.com/CedarGroveStudios/CircuitPython_Chime
* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads
"""

import time
import microcontroller
import board
import digitalio
import random
from simpleio import map_range
import adafruit_dotstar
from weather_chimes_wifi import WeatherChimesWiFi

import audiobusio
import audiomixer
from cedargrove_chime import Chime, Scale, Voice, Material, Striker


class State:
    """State machine status definitions."""

    FIRST_RUN = "first_run"
    IDLE = "idle"
    DONE = "done"


class WindColors:
    """A list of wind speed colors based on the NOAA standard.
    List elements are: [0] Wind Speed Minimum, [1] Color Value (hex).
    "NOAA Estimating Wind Speed" https://www.weather.gov/pqr/wind"""

    NOAA = [
        (0, 0x0065CC),
        (1, 0x3365FF),
        (4, 0x33CCFF),
        (8, 0x00FFFF),
        (13, 0x33FFCC),
        (19, 0x00CC00),
        (25, 0x01FF00),
        (32, 0xFFFFCC),
        (39, 0xFFFF00),
        (47, 0xFFCC65),
        (55, 0xFF9A00),
        (64, 0xFF6565),
        (75, 0xFF65FF),
    ]


WIFI_DEBUG = False

LOUDNESS = 0.8
SCALE_1 = Scale.HarryDavidPear

# Specify LED brightness level
LED_BRIGHT = 0.15

# Initialize cpu temperature sensor
corr_cpu_temp = microcontroller.cpu.temperature

# Initialize DotStar
pixel = adafruit_dotstar.DotStar(
    board.APA102_SCK, board.APA102_MOSI, 1, brightness=LED_BRIGHT, auto_write=True
)
pixel[0] = 0xFFFF00  # Initializing (yellow)

# Initialize busy LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT
led.value = True

# Instantiate wifi and sensor classes
corr_wifi = WeatherChimesWiFi(debug=WIFI_DEBUG)

# Instantiate chime synthesizer
audio_output = audiobusio.I2SOut(
    bit_clock=board.D12, word_select=board.D9, data=board.D6
)
mixer = audiomixer.Mixer(
    sample_rate=11020, buffer_size=4096, voice_count=1, channel_count=1
)
audio_output.play(mixer)
mixer.voice[0].level = 0.8
# mixer.voice[1].level = 0.4

chime = Chime(
    mixer.voice[0],
    scale=SCALE_1,
)

"""bells = Chime(
    mixer.voice[1],
    scale=SCALE_2,
    voice=Voice.Bell,
    material=MATERIAL_2,
    striker=STRIKER_2,
)"""

# Sequentially play all the notes in the scale
for index, note in enumerate(chime.scale):
    chime.strike(note, 1)
    # bells.strike(note, 1)
    time.sleep(0.4)
time.sleep(1)

# Define task parameters and set to initial state
TASK_1_TITLE = "display clock"
TASK_1_CYCLE = 1 * 60  # 1-minute cycle (seconds)
TASK_1_OFFSET = 0  # 0 seconds past the hour
task_1_state = State.FIRST_RUN

TASK_3_TITLE = "update clock and weather"
TASK_3_CYCLE = 20 * 60  # 20-minute cycle (seconds)
TASK_3_OFFSET = 12 * 60  # 12 minutes past the hour (seconds)
task_3_state = State.FIRST_RUN

print()
print("=" * 10)
print()

pixel[0] = 0x000000  # Clear for wind speed colors

note_amplitude = map_range(corr_wifi.wind_speed, 0, 100, 0.6, 1.0)

while True:
    current_time = time.time()

    # ### TASK 1 ###
    if current_time % TASK_1_CYCLE == TASK_1_OFFSET or task_1_state == State.FIRST_RUN:
        if task_1_state in (State.IDLE, State.FIRST_RUN):
            # TASK 1 START
            # Display the local time
            print(
                f"Task 1: {TASK_1_TITLE}: {time.localtime()[3]:02.0f}:{time.localtime()[4]:02.0f}"
            )

            # TASK 1 END

            task_1_state = State.DONE
    else:
        task_1_state = State.IDLE

    # ### TASK 3 ###
    if current_time % TASK_3_CYCLE == TASK_3_OFFSET or task_3_state == State.FIRST_RUN:
        if task_3_state in (State.IDLE, State.FIRST_RUN):
            # TASK 3 START
            print(
                f"\nTask 3: {TASK_3_TITLE}: {time.localtime()[3]:02.0f}:{time.localtime()[4]:02.0f}"
            )

            # Read and update the local time
            corr_wifi.update_local_time()
            print(
                f"  Local Time Refresh: {time.localtime()[3]:02.0f}:{time.localtime()[4]:02.0f}"
            )

            # Read and display WEATHER information
            corr_wifi.update_weather()
            print(f"  WEATHER Temperature: {corr_wifi.temperature}ºF")
            print(f"  WEATHER Humidity:    {corr_wifi.humidity}%")
            print(f"  WEATHER Wind Speed:  {corr_wifi.wind_speed}MPH")
            print(f"  WEATHER Wind Direction:  {corr_wifi.wind_direction}")
            print(f"  WEATHER Wind Gusts:  {corr_wifi.wind_gusts}MPH")
            print(f"  WEATHER Description: {corr_wifi.description}")

            for _, color in enumerate(WindColors.NOAA):
                if corr_wifi.wind_speed >= color[0]:
                    wind_speed_color = color[1]
            pixel[0] = wind_speed_color

            # TASK 3 END

            task_3_state = State.DONE
    else:
        task_3_state = State.IDLE

    """Play a randomized chime note sequence in proportion to wind speed.
    It's assumed that the chime tubes are mounted in a circle and that no more
    than half the tubes will sound when the striker moves due to wind. The
    initial chime tube note (chime_index[0]) is selected randomly from
    chime.scale. The initial struck note will be followed by adjacent notes
    either to the right or left as determined by the random direction variable.
    The playable note indices are contained in the chime_index list. Chime note
    amplitude and the delay between note sequences is proportional to
    the wind speed."""

    led.value = True  # Busy playing a note sequence

    """Populate the chime_index list with the initial note then add the
    additional adjacent notes."""
    chime_index = []
    chime_index.append(random.randrange(len(chime.scale)))

    direction = random.choice((-1, 1))
    for count in range(1, len(chime.scale) // 2):
        chime_index.append((chime_index[count-1] + direction) % len(chime.scale))

    """Randomly select the number of notes to play in the sequence."""
    notes_to_play = random.randrange(len(chime_index) + 1)

    """Play the note sequence with a random delay between each."""
    note_amplitude = map_range(corr_wifi.wind_speed, 0, 50, 0.4, 1.0)
    for count in range(notes_to_play):
        chime.strike(chime.scale[chime_index[count]], note_amplitude)
        time.sleep(random.randrange(10, 60) * 0.01)  # random delay of 0.10 to 0.50 seconds

    led.value = False

    """Delay the next note sequence inversely based on wind speed plus a
    random interval."""
    if corr_wifi.wind_speed < 1:
        time.sleep(30)
    else:
        time.sleep(map_range(corr_wifi.wind_speed, 0, 50, 2.0, 0.01) + (random.random()/2))


