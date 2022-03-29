Use
###

Basic
*****

Local display
=============

Upon powering up there will be a short delay and following which sensor readings will shown on the display.

If the screensaver is activated, simply touch the screen to wake up.

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