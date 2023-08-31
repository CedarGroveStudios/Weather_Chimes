# SPDX-FileCopyrightText: Copyright (c) 2023 JG for Cedar Grove Maker Studios
# SPDX-License-Identifier: MIT

"""
`cedargrove_chime`
===============================================================================
A CircuitPython class for generating wind chime and bell sounds for synthio.

Acknowledgement and thanks to:
Lee Hite, 'Tubular Bell Chimes Design Handbook' for the analysis of tubular
chime physics and overtones.
C. McKenzie, T. Schweisinger, and J. Wagner, 'A Mechanical Engineering
Laboratory Experiment to Investigate the Frequency Analysis of Bells and Chimes
with Assessment' for the analysis of bell overtones.

Special thanks to Liz Clark, 'Circle of Fifths Euclidean Synth with synthio and
CircuitPython' for the waveform and noise methods.
Also, thanks to Jeff Epler for the comprehensive design and implementation of
the amazing CircuitPython synthio module.

* Author(s): JG for Cedar Grove Maker Studios

Implementation Notes
--------------------

**Hardware:**
* ESP-32-S2 Feather

**Software and Dependencies:**
* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads
"""

import synthio
import ulab.numpy as np
from cedargrove_midi_tools import name_to_note


class Voice:
    """The pre-compiled synth voices. Bell is a single-capped tube
    with empirical overtones. Perfect is a dual-capped tube with algorithmically
    generated overtones equal to the length-related harmonics. Tubular is a
    traditional open-ended tube chime with empirical non-harmonic overtones."""

    Bell = "bell"
    Perfect = "perfect"
    Tubular = "tubular"


class Scale:
    """A collection of common wind chime musical note scales from
    Tubular Bell Chimes Design Handbook, Lee Hite."""

    Westminister = ["G#5", "E5", "F#5", "B4"]
    Pentatonic = ["C5", "D5", "E5", "G5", "A5"]
    CNine = ["C5", "E5", "G5", "A#5", "D6"]
    HavaNegila = ["C5", "C#5", "E5", "F5", "G5", "G#5"]
    CorinthianBellsA = ["A4", "B4", "C#5", "E5", "F#5", "A5"]
    CorinthianBellsB = ["B4", "C#5", "D#5", "F5", "G#5", "A#5"]
    CorinthianBellsC = ["C4", "D4", "E4", "G4", "A4", "C5"]
    CorinthianBellsEb = ["D#4", "F4", "G4", "A#4", "C5", "D#5"]
    CorinthianBellsG = ["G4", "A4", "B4", "D5", "E5", "G5"]
    Whittington = ["E5", "F#5", "G5", "A5", "B5", "C#6", "D6"]
    Canterbury = ["D5", "E5", "F#5", "G5", "A5", "B5"]
    Trinity = ["D5", "G5", "A5", "B5", "C6", "D6"]
    Winchester = ["C5", "D5", "E5", "F5", "G5", "A5"]
    StMichaels = ["F5", "G5", "A5", "A#5", "C6", "D6", "E6", "F6"]
    HappyBirthday = ["C5", "D5", "E5", "F5", "G5", "A5", "A#5", "B5", "C6"]

    # Other wind chimes measured in-field
    HarryDavidPear = []  # material = steel, voice = tubular
    CeramicTurtles = []  # material = ceramic, voice = bell
    BiPlane = []  # material = copper, voice = tubular


class Material:
    """The attack time, attack level, and release time for various chime/bell
    materials."""

    SteelEMT = [0.02, 1.0, 2.0]
    Ceramic = [0.10, 1.0, 0.8]  # has different harmonics than SteelEMT
    Wood = [0.15, 1.0, 1.0]  # has different harmonics than SteelEMT
    Copper = [0.02, 1.0, 1.5]  # may have different harmonics than SteelEMT
    Aluminum = [0.02, 0.9, 1.3]
    Brass = [0.02, 1.0, 1.8]


class Striker:
    """The attack time and attack level ratio for various striker materials."""

    Metal = [0.00, 1.0]
    Plexiglas = [0.01, 1.0]
    SoftWood = [0.05, 1.0]
    HardWood = [0.02, 1.0]


class Overtones:
    """The voice overtone frequency and relative amplitude factors of each.
    Root note is Overtones.Chime[0]; for example, the primary overtone is
    Overtones.Chime[1]. To avoid note distortion, the sum of overtone amplitude
    factors should equal 1.0 or less."""

    """Bell overtones were measured empirically but fall close to the
    theoretical single-capped tubular harmonics where overtones are the
    odd harmonics."""
    Bell = [(1.00, 0.8), (1.48, 0.19), (1.35, 0.01), (1.72, 0.0)]

    """Perfect overtones: the theoretical harmonics of a dual-capped tube."""
    Perfect = [
        (1.00, 0.6),
        (2.00, 0.2),
        (3.00, 0.1),
        (4.00, 0.05),
        (5.00, 0.05),
        (6.00, 0.0),
        (7.00, 0.0),
    ]

    """Tubular overtones were measured empirically; they are not equal to
    theoretical dual-capped tubular overtones or harmonics."""
    Tubular = [
        (1.00, 0.6),
        (2.76, 0.2),
        (5.40, 0.1),
        (8.93, 0.1),
        (11.34, 0.0),
        (18.64, 0.0),
        (31.87, 0.0),
    ]


class Chime:
    """Simple sine wave chime or bell sound using synthio."""

    def __init__(
        self,
        audio_out,
        scale=Scale.CNine,
        material=Material.SteelEMT,
        striker=Striker.Metal,
        voice=Voice.Tubular,
        scale_offset=0,
        loudness=0.5,
        debug=False,
    ):
        """Create the oscillator waveform, note envelope, overtones, scale, and
        instantiate the synthesizer."""

        self._debug = debug
        self._voice = voice
        self._material = material
        self._striker = striker
        self._scale_offset = scale_offset  # half-steps
        self._loudness = loudness

        # Set default ADSR envelope settings
        self._note_envelope = synthio.Envelope(
            attack_time=material[0] + striker[0],
            attack_level=material[1] * striker[1],
            decay_time=0.0,
            release_time=material[2],
            sustain_level=1.0,
        )

        # Set default voice overtones
        if self._voice == Voice.Bell:
            self._overtones = Overtones.Bell
        elif self._voice == Voice.Perfect:
            self._overtones = Overtones.Perfect
        else:
            # For Voice.Tubular
            self._overtones = Overtones.Tubular

        # Create scale table
        self._scale = []
        for index, note in enumerate(scale):
            self._scale.append(
                min(max(name_to_note(note) + self._scale_offset, 0), 127)
            )
        if self._debug:
            print(f"scale={scale} self._scale={self._scale} list created")

        """Create a single-cycle (one-lambda) sine waveform table to act as
        the oscillator."""
        wave_size = 128  # 512 recommended by todbot
        wave_rate = 11020  # 22050 recommended by todbot
        wave_max_value = int(self._loudness * 31000)  # 0-32767 (signed 16-bit)

        self._wave_sine = np.array(
            np.sin(np.linspace(0, 2 * np.pi, wave_size, endpoint=False))
            * wave_max_value,
            dtype=np.int16,
        )

        # Instantiate the synthesizer
        self.synth = synthio.Synthesizer(
            sample_rate=wave_rate, waveform=self._wave_sine
        )
        audio_out.play(self.synth)

    @property
    def scale(self):
        """Returns the note scale list."""
        return self._scale

    @property
    def loudness(self):
        """Returns the current loudness value."""
        return self._loudness

    def strike(self, root_note=69, amplitude=0):
        """Strike the chime or bell. The midi root_note integer ranges from 0 to 128.
        The note_amplitude is a floating point value between 0 and 1.0. The note envelope
        and overtone values are determined by the chime/bell and striker materials."""

        root_note_freq = synthio.midi_to_hz(root_note)
        adjusted_amplitude = amplitude * self._loudness

        self._notes = (
            synthio.Note(
                root_note_freq * self._overtones[0][0],
                amplitude=adjusted_amplitude * self._overtones[0][1],
                envelope=self._note_envelope,
            ),
            synthio.Note(
                root_note_freq * self._overtones[1][0],
                amplitude=adjusted_amplitude * self._overtones[1][1],
                envelope=self._note_envelope,
            ),
            synthio.Note(
                root_note_freq * self._overtones[2][0],
                amplitude=adjusted_amplitude * self._overtones[2][1],
                envelope=self._note_envelope,
            ),
            synthio.Note(
                root_note_freq * self._overtones[3][0],
                amplitude=adjusted_amplitude * self._overtones[3][1],
                envelope=self._note_envelope,
            ),
        )

        self.synth.press(self._notes)
        # time.sleep(self._attack_time)  # making certain that note isn't released too soon
        self.synth.release(self._notes)
