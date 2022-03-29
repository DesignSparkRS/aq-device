Debugging
#########

Status
******

To check the status of the application, connect via SSH and at the command prompt enter::

    systemctl status aq

The output will show whether the application is running or has exited, along with recent log messages.

More extensive logs can be found in the :code:`/aq/log` directory.

Debug mode
**********

Debug mode can be enabled by setting the following line in the :code:`[ESDK]` section of the config file::

    debug = true

Then restarting. Following which there should be more verbose output in the log files.

.. warning::
   Soft reboot (without power cycling) will result in the CO2 sensor going offline. 

Typical problems
****************

The most common problems are likely to be:

* **Missing readings:**
    * Sensor chain not properly connected.
    * Faulty/damaged sensor module.
* **Application won't start:**
    * Micro SD card full (delete CSV logs and/or application log files).
    * Configuration file errors (check for typos and correct use of quotes etc.)
* **Crashes, hangs, unreliability:**
    * Bad power supply. It is strongly recommended to use the provided official Raspberry Pi PSU!