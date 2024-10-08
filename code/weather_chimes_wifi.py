# SPDX-FileCopyrightText: Copyright (c) 2024 JG for Cedar Grove Maker Studios
# SPDX-License-Identifier: MIT
"""
`weather_chimes_wifi`
===============================================================================
A CircuitPython class for the Weather Chimes project's wi-fi connectivity.

* Author(s): JG for Cedar Grove Maker Studios

Implementation Notes
--------------------

**Hardware:**
* ESP-32-S2 Feather

**Software and Dependencies:**
* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads
"""

import gc
import os
import time
import random
import ssl
import rtc
import microcontroller
import socketpool
import wifi
import adafruit_ntp
import adafruit_requests


class WeatherChimesWiFi:
    """Initialize and manage the WiFi network connections and feeds for the
    Weather Chimes project."""

    def __init__(self, debug=False, wifi_mode=True):
        """Establish the network connection and feeds. Set the local time and
        weather conditions."""
        self._debug = debug
        self._wifi_mode = wifi_mode

        if self._wifi_mode:
            try:
                """Connect to WiFi access point."""
                print("Connecting to {}".format(os.getenv("CIRCUITPY_WIFI_SSID")))
                wifi.radio.connect(
                    os.getenv("CIRCUITPY_WIFI_SSID"), os.getenv("CIRCUITPY_WIFI_PASSWORD")
                )
                print("...SUCCESS: connected to WiFi access point")
            except Exception as wifi_access_error:  # pylint: disable=broad-except
                """WiFi connectivity fails without specific errors, so this is broad."""
                print(
                    "FAILED to connect to WiFi. Error:",
                    wifi_access_error,
                    "\nBoard will hard reset in 60 seconds.",
                )
                time.sleep(60)
                microcontroller.reset()

            # Create a socket pool and requests session
            self.pool = socketpool.SocketPool(wifi.radio)
            self.requests = adafruit_requests.Session(
                self.pool, ssl.create_default_context()
            )

            #  Print MAC and IP addresses to REPL
            print(f"MAC: {wifi.radio.mac_address}")
            print(f"IP : {wifi.radio.ipv4_address}")

            # Initialize network time connection and update local time
            self.ntp = adafruit_ntp.NTP(self.pool, tz_offset=-7)
            self.update_local_time()
            self.printd("NTP local time connection initialized; local time updated")

            # Set location and units for weather data and update conditions
            self.UNITS = "imperial"
            LOCATION = os.getenv("location")
            self.printd("Getting weather for {}".format(LOCATION))

            # Set up the URL for fetching weather data
            self.printd("Set up the URL for fetching weather data")
            self.DATA_SOURCE = (
                "http://api.weather.gov/stations/KPSC/observations/latest"
            )
            self.update_weather()

    @property
    def debug(self):
        """The latest debug flag state."""
        return self._debug

    @debug.setter
    def debug(self, new_state=False):
        """Set the debug flag to print verbose status information."""
        if (new_state in (True, False)) and (new_state != self._debug):
            self._debug = new_state

    @property
    def wind_speed(self):
        """The latest outdoor wind speed value."""
        return self._weather_wind_speed

    def printd(self, text=""):
        """Print text if debug is True."""
        if self._debug:
            print(" ... " + text)

    def update_local_time(self):
        """Update the local time from NTP."""
        self.printd("Update Local Time")
        if self._wifi_mode:
            try:
                rtc.RTC().datetime = self.ntp.datetime
                self.printd("SUCCESS: updated local time")
            except Exception as update_time_error:
                print("FAILED: update local time")
                print(str(update_time_error))

    def update_weather(self):
        """Fetch and update the local weather conditions from OpenWeatherMap
        or insert random values if wifi_mode is False."""
        self.printd("Fetch and Update Weather")
        gc.collect()

        if self._wifi_mode:
            # Fetch weather data from OpenWeatherMap API
            self.printd(f"Fetching json from {self.DATA_SOURCE}")
            response = None
            try:
                response = self.requests.get(self.DATA_SOURCE)
                # self.printd(response.json())
                self.printd("SUCCESS: fetch and update local weather")
            except Exception as update_weather_error:
                print("FAILED: fetch and update weather")
                print(str(update_weather_error))

            # Extract temperature and weather condition data from API response
            if response is not None:
                self._weather_wind_speed = round(response.json()["properties"]["windSpeed"]["value"], 0)
                response = None  # Clear the response memory buffer
                gc.collect()
        else:
            self._weather_wind_speed = random.randrange(1, 10)
            self.printd("RANDOM")


        self.printd(f"Weather Wind Speed: {self._weather_wind_speed}mph")

