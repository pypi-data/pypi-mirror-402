APRSD Plugin for OpenWeatherMap APIs
====================================

|PyPI| |Status| |Python Version| |License|

|Read the Docs| |Tests| |Codecov|

|pre-commit|

.. |PyPI| image:: https://img.shields.io/pypi/v/aprsd-openweathermap-plugin.svg
   :target: https://pypi.org/project/aprsd-openweathermap-plugin/
   :alt: PyPI
.. |Status| image:: https://img.shields.io/pypi/status/aprsd-openweathermap-plugin.svg
   :target: https://pypi.org/project/aprsd-openweathermap-plugin/
   :alt: Status
.. |Python Version| image:: https://img.shields.io/pypi/pyversions/aprsd-openweathermap-plugin
   :target: https://pypi.org/project/aprsd-openweathermap-plugin
   :alt: Python Version
.. |License| image:: https://img.shields.io/pypi/l/aprsd-openweathermap-plugin
   :target: https://opensource.org/licenses/MIT
   :alt: License
.. |Read the Docs| image:: https://img.shields.io/readthedocs/aprsd-openweathermap-plugin/latest.svg?label=Read%20the%20Docs
   :target: https://aprsd-openweathermap-plugin.readthedocs.io/
   :alt: Read the documentation at https://aprsd-openweathermap-plugin.readthedocs.io/
.. |Tests| image:: https://github.com/hemna/aprsd-openweathermap-plugin/workflows/Tests/badge.svg
   :target: https://github.com/hemna/aprsd-openweathermap-plugin/actions?workflow=Tests
   :alt: Tests
.. |Codecov| image:: https://codecov.io/gh/hemna/aprsd-openweathermap-plugin/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/hemna/aprsd-openweathermap-plugin
   :alt: Codecov
.. |pre-commit| image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit


Features
--------

This plugin provides two APRSD plugins that use the OpenWeatherMap API:

* **WeatherPlugin** - Returns current weather conditions based on GPS beacon location
* **TimePlugin** - Returns current time in the timezone of the GPS beacon location

Both plugins use aprs.fi to look up the GPS coordinates of APRS stations, then use OpenWeatherMap
to fetch weather and timezone information.


Requirements
------------

* APRSD server (version 4.2.0 or higher)
* OpenWeatherMap API key (free tier available)
* aprs.fi API key (for location lookup)


Installation
------------

You can install *APRSD Plugin for OpenWeatherMap APIs* via pip_ from PyPI_:

.. code:: console

   $ pip install aprsd-openweathermap-plugin


Configuration
-------------

Getting an OpenWeatherMap API Key
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Visit https://home.openweathermap.org/users/sign_up to create a free account
2. Once logged in, navigate to https://home.openweathermap.org/api_keys
3. Generate a new API key (or use the default one provided)
4. The free tier includes 1,000 API calls per day, which is sufficient for most use cases

Note: It may take a few minutes for a newly created API key to become active.

Configuring the Plugin
~~~~~~~~~~~~~~~~~~~~~~~

Add the following to your APRSD configuration file (typically ``aprsd.conf``):

.. code:: ini

   [aprsd_openweathermap_plugin]
   enabled = True
   apiKey = YOUR_OPENWEATHERMAP_API_KEY_HERE

   [aprs_fi]
   apiKey = YOUR_APRS_FI_API_KEY_HERE

You can get an aprs.fi API key from https://aprs.fi/account/


Usage
-----

Weather Plugin
~~~~~~~~~~~~~~~

The WeatherPlugin provides current weather conditions at the location of an APRS station's GPS beacon.

**Command Format:**
* ``w`` or ``weather`` - Get weather at your own location (based on your callsign's last GPS beacon)
* ``w CALLSIGN`` or ``weather CALLSIGN`` - Get weather at the specified callsign's location

**Example Usage:**

Send a message to your APRSD server:
::

   weather

Response:
::

   clear sky 20.5C/15.2C Wind 10@180 65%

Or query weather for a specific station:
::

   weather N0CALL

Response:
::

   partly cloudy 22.0C/18.0C Wind 15@270G25 70%

The response includes:
* Weather description (e.g., "clear sky", "partly cloudy")
* Temperature and dew point in Celsius or Fahrenheit (based on configured units)
* Wind speed, direction, and optional gust
* Humidity percentage

Time Plugin
~~~~~~~~~~~

The TimePlugin provides the current time in the timezone of an APRS station's GPS beacon location.

**Command Format:**
* ``t`` or ``time`` - Get time at your own location
* ``t CALLSIGN`` or ``time CALLSIGN`` - Get time at the specified callsign's location

**Example Usage:**

Send a message to your APRSD server:
::

   time

Response:
::

   2024-01-15 14:30:00 PST

Or query time for a specific station:
::

   time N0CALL

Response:
::

   2024-01-15 16:30:00 EST

The plugin automatically determines the timezone based on the GPS coordinates and returns
the local time. If OpenWeatherMap API is unavailable, it defaults to UTC time.


How It Works
------------

Both plugins follow a similar workflow:

1. Extract the callsign from the message (or use the sender's callsign if not specified)
2. Query aprs.fi API to get the GPS coordinates (latitude/longitude) of the callsign's last beacon
3. Use the GPS coordinates to query OpenWeatherMap API for:
   * **WeatherPlugin**: Current weather conditions
   * **TimePlugin**: Timezone information
4. Format and return the results

The plugins require both APIs to be functional:
* If aprs.fi lookup fails, the plugin returns "Failed to fetch location"
* If OpenWeatherMap API fails, WeatherPlugin returns "Unable to get weather"
* If OpenWeatherMap API fails, TimePlugin defaults to UTC timezone


Contributing
------------

Contributions are very welcome.
To learn more, see the `Contributor Guide`_.


License
-------

Distributed under the terms of the `MIT license`_,
*APRSD Plugin for OpenWeatherMap APIs* is free and open source software.


Issues
------

If you encounter any problems,
please `file an issue`_ along with a detailed description.


Credits
-------

This project was generated from `@hemna`_'s `APRSD Plugin Python Cookiecutter`_ template.

.. _@hemna: https://github.com/hemna
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _MIT license: https://opensource.org/licenses/MIT
.. _PyPI: https://pypi.org/
.. _APRSD Plugin Python Cookiecutter: https://github.com/hemna/cookiecutter-aprsd-plugin
.. _file an issue: https://github.com/hemna/aprsd-openweathermap-plugin/issues
.. _pip: https://pip.pypa.io/
.. github-only
.. _Contributor Guide: CONTRIBUTING.rst
.. _Usage: https://aprsd-openweathermap-plugin.readthedocs.io/en/latest/usage.html
