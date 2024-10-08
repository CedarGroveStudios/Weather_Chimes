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
                "http://api.openweathermap.org/data/2.5/weather?q="
                + LOCATION
                + "&units="
                + self.UNITS
                + "&mode=json"
                + "&appid="
                + os.getenv("openweather_token")
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
    def temperature(self):
        """The latest outdoor temperature."""
        return self._weather_temp_f

    @property
    def humidity(self):
        """The latest outdoor humidity value."""
        return self._weather_humid

    @property
    def wind_speed(self):
        """The latest outdoor wind speed value."""
        return self._weather_wind_speed

    @property
    def wind_direction(self):
        """The latest outdoor wind direction value."""
        return ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][
            int(((self._weather_wind_direction + 22.5) % 360) / 45)
        ]

    @property
    def wind_gusts(self):
        """The latest outdoor wind gusts value."""
        return self._weather_wind_gusts

    @property
    def description(self):
        """The latest weather description."""
        return self._weather_desc

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
                self._weather_temp_f = round(response.json()["main"]["temp"], 1)
                self._weather_humid = round(response.json()["main"]["humidity"], 1)

                self._weather_wind_speed = round(response.json()["wind"]["speed"], 0)

                try:
                    self._weather_wind_gusts = round(response.json()["wind"]["gust"], 0)
                except:
                    self._weather_wind_gusts = 0  # No wind gust speed data (no gusts?)

                self._weather_wind_direction = round(response.json()["wind"]["deg"], 0)

                self._weather_desc = (
                    response.json()["weather"][0]["main"]
                    + ": "
                    + response.json()["weather"][0]["description"]
                )
        else:
            self.UNITS = "imperial"
            self._weather_temp_f = 72
            self._weather_humid = 50
            self._weather_wind_speed = random.randrange(1, 10)
            self._weather_wind_gusts = random.randrange(1, 10)
            self._weather_wind_direction = random.randrange(0, 359)
            self._weather_desc = "(random)"


        self.printd(f"Weather Temp: {self._weather_temp_f} F ({self.UNITS})")
        self.printd(f"Weather Humidity: {self._weather_humid} %")
        self.printd(f"Weather Wind Speed: {self._weather_wind_speed}mph")
        self.printd(f"Weather Wind Gusts: {self._weather_wind_gusts}mph")
        self.printd(f"Weather Wind Direction: {self._weather_wind_direction}")
        self.printd(f"Weather Description: {self._weather_desc}")
