Use
###

Basic
*****

Device dashboard
================

Upon powering up there will be a short delay and following which sensor readings will shown on the display. If you have a v1.0 or later Main board (see the silkscreen labelling) the buzzer will also sound upon startup.

If the screensaver is activated, simply touch the screen to wake up.

If you have an NO2 Sensor, Nuclear Radiation Detector or Formaldehyde Sensor, readings for these are accessed via the second screen and use the inner two physical buttons to navigate between screens.

Tap a sensor statistics panel to switch to a plot view and tap again to revert.

The debug screen can be accessed via a long press on the touch screen, following which a short press will switch to the second debug page. Another long press will return to the dashboard.

LAN dashboard
=============

It is also possible to access a web dashboard via the local area network, by pointing a browser at the URL:

http://airquality.local

Plot traces my be toggled on and off by clicking on their legend. This can prove useful with sensors such as PM2, where there are multiple lines which may not be easy to distinguish from each other.

A debug screen may be accessed via the Debug tab.

CSV logging
===========

In addition to being configured via :code:`aq.toml` to start at boot time, CSV logging may be enabled by pressing the top physical button, and disabled again via a second press.

A small flashing icon will be present in the top-right corner of the device screen when CSV logging is enabled.

.. warning:: 
   There may be a delay of a few seconds after a button press before logging is started/stopped, hence avoid repeatedly pressing.

GPS
===

If GPS has been enabled and the ESDK has a fix, a small cross hairs icon will be present in the top-right corner of the device screen.

GPS satellite status and position is available via the debug screen.

Shutting down
=============

The Raspberry Pi should be properly shut down before removing power. This can be done by pressing the bottom of the four black buttons. 

.. warning::
   Failure to shut down before removing power may result in data loss.

Restarting
==========

If the device needs to be restarted, e.g. after making configuration changes, the following procedure should be used:

#. Shut down
#. Remove power
#. Reconnect power

.. warning::
   Soft reboot (without power cycling) will result in the CO2 sensor going offline.

MQTT
****

MQTT functionality can be tested by connecting via SSH and entering at the command prompt::

    mosquitto_sub -h localhost -t '#'

Or Alternatively using an MQTT client on another computer and connecting to host :code:`airquality.local`.

Sensor readings should be printed out every 5 seconds.