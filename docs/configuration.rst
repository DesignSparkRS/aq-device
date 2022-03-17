Configuration
-------------

There are two options for configuration:

#. Insert the Micro SD card into another computer and use this to edit the config.
#. Insert the Micro SD card into the Raspberry Pi, boot and then edit the config via an SSH connection.

The username and password are set to the Raspberry Pi OS defaults of :code:`pi` and :code:`raspberry`.

.. note::
   The configuration file is located on the :code:`/boot` partition and since this is formatted using the fat32 filesystem, it means that it can be mounted for editing on Windows, Linux and Mac computers.

Using your favourite editor, open the file::

    /boot/aq/aq.toml

Or whatever path the boot partition is mounted to if you took the first option of using another computer.

Basic settings
==============

An example basic configuration::

    [ESDK]
    friendlyname = "abopen"
    location = "workshop"
    tag = "unheated"
    latitude = 53.7130128
    longitude = -1.9391832

.. list-table:: Configuration parameters
   :widths: auto
   :header-rows: 1

   * - Key
     - Description
   * - :code:`friendlyname`
     - A short and informative name for the device
   * - :code:`location`
     - Position within a property or outside
   * - :code:`latitude` & :code:`longitude`
     - Geolocation a.k.a. "GPS position"
   * - :code:`tag`
     - A useful additional tag/label for the device (optional)
   * - :code:`project`
     - Identifier for a collaborative project (only set this when instructed)

Try to pick something unique for the :code:`friendlyname`. This is not essential, but will be helpful in debugging any issues and when it comes to organising collaborative projects.

The :code:`location` should be set to e.g. "kitchen", "livingroom", "attic" etc. A taxonomy has been created and for details, see the Air Quality Project Taxonomy. Please be sure to pick a location from this list, so as to avoid having multiple different labels in use for the same location, which will be important when it comes to interpreting data.

The :code:`latitude` and :code:`longitude` should be set according to the geolocation. While there are no plans to show data from individual sensors at private residences in public dashboards, you may still decide that you are not comfortable with disclosing your precise location. In such cases it is suggested to use the coordinates for the end of the street or perhaps the nearest town. However, it is important that the configured and actual location are not too far apart, otherwise this may compromise the usefulness of the data gathered.

The :code:`tag` parameter is optional. This can be used to help distinguish data when configured to publish to a cloud platform. For example, you might wish to create a visualisation which shows measurements for sensors in heated vs. unheated rooms. If unsure, don't set this and it can always be configured later.

The :code:`project` parameter is used to identify devices which belong to a particular DesignSpark Air Quality collaborative project. This should not be set unless instructed to do so.

If configured, the values for :code:`tag` and :code:`project` will be set as additional labels on measurements, alongside :code:`friendlyname`, :code:`location` and :code:`latitude` + :code:`longitude`, when publishing data to the cloud. 

All the parameters listed above should be located within a section labelled :code:`[ESDK]` as shown in the example.

.. warning::
    The values for friendlyname, location, tag and project may contain letters, numbers and underscores only, and should each be no more than 12 characters in length.

GPS
===

The ESDK Main board contains a GPS receiver, but this is not used by default and instead sensor measurements are labelled with the geolocation set in the configuration file. The GPS receiver can be enabled with the following setting in the :code:`[ESDK]` section of the configuration file::

    gps = true

However, a GPS antenna must be connected and able to see the sky. This is intended for use with future mobile use cases, whereas with static use it is strongly recommended that this be turned off, using a hardcoded latitude + longitude in the configuration file instead. 

CSV logging
===========

Logging comma-seperated values of sensor measurements to a file can be enabled by setting :code:`csv = true` in the :code:`[local]` section of the configuration file. Simply add::

    [local]
    csv = true

CSV files will be saved to :code:`/aq/data/`.

Data can be copied off using :code:`scp` or by inserting the Micro SD card into another Linux computer.

.. note::
   The :code:`/aq` partition is formatted with the ext4 filesystem, since this uses journalling and is more robust than fat32. However, it does mean that the partition cannot be easily read on Windows computers.

MQTT
====

Publishing sensor readings to an MQTT broker can be enabled by adding an :code:`[mqtt]` section with the appropriate configuration::

    [mqtt]
    broker = "localhost"
    basetopic = "airquality"
    username = ""
    password = ""

The above example will configure the application to publish to the Mosquitto broker which is preinstalled, with a base topic of :code:`airquality`. Alternatively, a remote broker may be specified and if required, login details provided.


Cloud integration
=================

*Details to be provided in due course.*

Private dashboards
******************

Public dashboards
*****************
