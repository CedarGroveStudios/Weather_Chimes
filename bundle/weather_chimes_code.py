# SPDX-FileCopyrightText: Copyright (c) 2023 JG for Cedar Grove Maker Studios
# SPDX-License-Identifier: MIT

"""
`weather_chimes_code`
===============================================================================
IOT-connected windless garden chimes for the ESP-32-S2 Feather.

* Author(s): JG for Cedar Grove Maker Studios

Implementation Notes
--------------------

**Hardware:**
* ESP-32-S2 Feather

**Software and Dependencies:**
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
BELLS_DEBUG = False
CHIME_DEBUG = False

LOUDNESS = 0.4
SCALE = Scale.HavaNegila
SCALE_OFFSET_1 = 5
VOICE_1 = Voice.Tubular
MATERIAL_1 = Material.SteelEMT
STRIKER_1 = Striker.Metal

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
mixer.voice[0].level = 1.0
# mixer.voice[1].level = 1.0

chime = Chime(
    mixer.voice[0],
    scale=SCALE,
    voice=VOICE_1,
    material=MATERIAL_1,
    striker=STRIKER_1,
    scale_offset=SCALE_OFFSET_1,
    loudness=LOUDNESS,
    debug=CHIME_DEBUG,
)
# bells = Chime(mixer.voice[1], scale=SCALE, voice=VOICE_2, material=MATERIAL_2, striker=STRIKER_2, scale_offset=SCALE_OFFSET_2, loudness=LOUDNESS, debug=BELLS_DEBUG)

# Sequentially play all the notes in the scale
for index, note in enumerate(chime.scale):
    chime.strike(note, 1)
    # bells.strike(note, 1)
    time.sleep(0.4)
time.sleep(1)

# Define task parameters and set to initial state
TASK_0_TITLE = "heartbeat"
TASK_0_CYCLE = 2  # 2-second cycle (seconds)
TASK_0_OFFSET = 0  # 0 seconds past the hour
task_0_state = State.FIRST_RUN

TASK_1_TITLE = "display clock"
TASK_1_CYCLE = 1 * 60  # 1-minute cycle (seconds)
TASK_1_OFFSET = 0  # 0 seconds past the hour
task_1_state = State.FIRST_RUN

TASK_2_TITLE = "play wind-related chimes"
TASK_2_CYCLE = 3  # 11-second cycle (seconds)
TASK_2_OFFSET = 0  # 0 seconds past the hour
task_2_state = State.FIRST_RUN

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

    # TASK 0 (HEARTBEAT)
    if current_time % TASK_0_CYCLE == TASK_0_OFFSET or task_0_state == State.FIRST_RUN:
        if task_0_state in (State.IDLE, State.FIRST_RUN):
            # ### TASK 0 START
            led.value = True  # Heartbeat: flash LED when idle
            time.sleep(0.1)
            led.value = False
            # ### TASK 0 END

            task_0_state = State.DONE
    else:
        task_0_state = State.IDLE

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

    # ### TASK 2 ###
    if current_time % TASK_2_CYCLE == TASK_2_OFFSET or task_2_state == State.FIRST_RUN:
        if task_2_state in (State.IDLE, State.FIRST_RUN):
            # TASK 2 START
            print(
                f"Task 2: {TASK_2_TITLE}: {time.localtime()[3]:02.0f}:{time.localtime()[4]:02.0f}"
            )

            # Play wind-related chimes
            number_to_play = int(map_range(corr_wifi.wind_speed, 0, 50, 5, 30))
            for count in range(random.randrange(number_to_play)):
                chime.strike(random.choice(chime.scale), note_amplitude)
                time.sleep(
                    random.randrange(1, 3)
                    * map_range(corr_wifi.wind_speed, 0, 50, 0.6, 0)
                )

            # TASK 2 END

            task_2_state = State.DONE
    else:
        task_2_state = State.IDLE

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

            note_amplitude = map_range(corr_wifi.wind_speed, 0, 100, 0.6, 1.0)

            chime.strike(chime.scale[0], note_amplitude)

            # TASK 3 END

            task_3_state = State.DONE
    else:
        task_3_state = State.IDLE
