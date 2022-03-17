Use
===

Basic
-----

Local display
*************

Upon powering up there will be a short delay and following which sensor readings will shown on the display.

If the screensaver is activated, simply touch the screen to wake up.

Shutting down
*************

The Raspberry Pi should be properly shut down before removing power. This can be done by pressing the bottom of the four black buttons. 

.. warning::
   Failure to shut down before removing power may result in data loss.

Restarting
**********

If the device needs to be restarted, e.g. after making configuration changes, the follow procedure should be followed:

#. Shut down
#. Remove power
#. Reconnect power

.. warning::
   Soft reboot (without power cycling) will result in the CO2 sensor going offline.

MQTT
----

MQTT functionality can be tested by connecting via SSH and entering at the command prompt::

    mosquitto_sub -h localhost -t '#'

Sensor readings should be printed out every 5 seconds.

Fault finding
-------------

To check the status of the application, connect via SSH and at the command prompt enter::

    systemctl status aq

The output will show whether the application is running or has exited, along with recent log messages.

More extensive logs can be found in the :code:`/aq/log` directory.

Debug mode
**********

Debug mode can be enabled by adding the following line to the :code:`[ESDK]` section of the config file::

    debug = true

Then restarting. Following which there should be more verbose output in the log files.

Typical problems
****************

The most common problems are likely to be:

* **Missing readings:**
    * Sensor chain not properly connected.
* **Application won't start:**
    * Micro SD card full (delete CSV logs and/or application log files).
    * Configuration file errors (check for typos and correct use of quotes etc.)
* **Crashes / poor reliability:**
    * Bad power supply. 