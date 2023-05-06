Configuration
#############

Editing
*******

There are two options for editing the configuration:

#. Insert the Micro SD card into another computer and use this to edit the config.
#. Insert the Micro SD card into the Raspberry Pi, boot and then edit the config via an SSH connection.

The hostname is set to :code:`airquality` and since mDNS is configured, it should be possible to connect via SSH using :code:`airquality.local`.

The username and password are set to the Raspberry Pi OS defaults of :code:`pi` and :code:`raspberry`.

.. note::
   The configuration file is located on the :code:`/boot` partition and since this is formatted using the fat32 filesystem, it means that it can be mounted for editing on Windows, Linux and Mac computers.

Using your favourite editor, create a new file::

    /boot/aq/aq.toml

Or if you went with option 1 and are using another computer, whatever path the boot partition is mounted to.

The configuration is broken up into sections each with a heading. Values that are strings are quoted, whereas numbers and boolean values are not.

Base config 
***********

Basic device configation is located within the :code:`[ESDK]` section. 

Mandatory
=========

Example config::

    [ESDK]
    friendlyname = "acmecorp"
    location = "workshop"
    latitude = 53.7130128
    longitude = -1.9391832
    debug = false

.. list-table:: Mandatory parameters
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
   * - :code:`debug`
     - Logging level (set to false unless experiencing issues)

Try to pick something unique for the :code:`friendlyname`. This is not
essential, but will be helpful in debugging any issues and when it comes to
organising collaborative projects.

.. warning::
   The :code:`friendlyname` must not be changed without good reason, as this is used as the key for constructing visualisations and whenever this is changed, series data and hence plots etc. will become non-contigious.   

The :code:`location` should be set to e.g. "kitchen", "livingroom" or "outdoor" 
etc. A taxonomy has been created and for details, see the :doc:`Air Quality Project
Taxonomy <dsdocs:aq/taxonomy>`. Please be sure to pick a location from this list, 
so as to avoid having multiple different labels in use for the same location, 
which will be important when it comes to interpreting data.

.. warning::
    The :code:`location` must be set to "mixed" if using the Cabled Range Extender boards and there are sensor chains in two different locations.

The :code:`latitude` and :code:`longitude` should be set according to the
geolocation. While there are no plans to show data from individual sensors at
private residences in public dashboards, you may still decide that you are not
comfortable with disclosing your precise location. In which case it is suggested
to use the coordinates for the end of the street or perhaps the nearest town.
However, it is important that the configured and actual location are not too far
apart, otherwise this may compromise the usefulness of data gathered.

.. warning::
    The values for friendlyname and location may contain letters, numbers and underscores only and should be no more than 12 characters in length.

Optional
========

Example config for optional parameters::

    tag = "unheated"
    project = "makerspace"

.. list-table:: Optional parameters
   :widths: auto
   :header-rows: 1

   * - Key
     - Description
   * - :code:`tag`
     - A useful additional tag/label for the device
   * - :code:`project`
     - Identifier for a collaborative project

The :code:`tag` parameter can be used to help distinguish data published to a
cloud platform. For example, you may wish to create a visualisation which groups
measurements for sensors in heated vs. unheated rooms. If unsure, don't set this
and it can always be configured later.

The :code:`project` parameter is used to identify devices which belong to a
particular DesignSpark Air Quality collaborative project. **This should not be
set unless instructed to do so.**

If configured, the values for :code:`tag` and :code:`project` will be set as
additional labels on measurements, alongside :code:`friendlyname`,
:code:`location`, :code:`latitude` and :code:`longitude`, when publishing data
to the cloud. 

.. warning::
    The values for tag and project may contain letters, numbers and underscores only, and should be no more than 12 characters in length.

Sensor config
*************

Most sensors don't require any configuration, but some may have optional or mandatory config parameters.

NO2
===

NO2 sensor configation is located within the :code:`[NO2]` section. 

The NO2 module uses an electrochemical sensor and its sensitivity must be configured, otherwise the application will ignore it.
The sensitivity is printed on a label underneath the sensor element, which is the small square board plugged into the top of the 3-board stack.
The sensitivity value may also have been provided to you along with the module.

Example config::

    [NO2]
    sensitivity = -21.08

.. list-table:: Mandatory parameters
   :widths: auto
   :header-rows: 1

   * - Key
     - Description
   * - :code:`sensitivity`
     - Value

GPS
***

The ESDK Main board contains a GPS receiver, but this is not used by default and instead sensor measurements are labelled with the geolocation set in the configuration file. The GPS receiver can be enabled with the following setting in the :code:`[ESDK]` section::

    gps = true

However, a GPS antenna must be connected and able to see the sky. This is intended for use with future mobile use cases, whereas with static use it is strongly recommended that this be turned off, using a hardcoded latitude + longitude in the configuration file instead. 

CSV logging
***********

Logging comma-seperated values of sensor measurements to a file can be enabled by setting :code:`csv = true` in the :code:`[local]` section of the configuration file. Simply add to aq.toml::

    [local]
    csv = true

CSV files will be saved to :code:`/aq/data/`.

Data can be copied off using :code:`scp` or by inserting the Micro SD card into another Linux computer.

.. note::
   The :code:`/aq` partition is formatted with the ext4 filesystem, since this uses journalling and is more robust than fat32. However, it does mean that the partition cannot be easily read on Windows computers.

MQTT
****

Publishing sensor readings to an MQTT broker can be enabled by adding an :code:`[mqtt]` section with the appropriate configuration::

    [mqtt]
    broker = "localhost"
    basetopic = "airquality"
    username = ""
    password = ""

The above example will configure the application to publish to the Mosquitto broker which is preinstalled, with a base topic of :code:`airquality`. Alternatively, a remote broker may be specified and if required, login details provided.

Cloud integration
*****************

The :doc:`DesignSpark Cloud <dsdocs:cloud/index>` platform uses the Prometheus time series database and the application may be configured to publish to one or more API endpoints, which are configured via :code:`[prometheus.*]` sections.

Typically there will be a :code:`[prometheus.private]` section for private dashboards and a :code:`[prometheus.aqpublic]` section for collaborative dashboards.

The configuration for private vs. public dashboards is subtly different and **due care must be exercised when configuring**.

.. note:: 
   You will only be able to complete this configuration if you have been provisioned on DesignSpark Cloud and enrolled with a username and password etc.

Private dashboards
==================

Each DesignSpark Cloud user is provisioned with a dedicated Prometheus database instance. Publishing to this may be configured with::

    [prometheus.private]
    instance = "<INSTANCE>"
    key = "<SECRET_KEY>"
    url = "https://prometheus-prod-01-eu-west-0.grafana.net/api/prom/push"
    interval = 120

Using the instance ID and publisher key that were provided to you by support.

The :code:`interval` parameter specifies the publishing period in seconds, the minimum value for which is 120 (2 minutes).

Public dashboards
=================

Users may also be invited to contribute data to public dashboards, which may be configured with::

    [prometheus.aqpublic]
    instance = "<EMAIL>"
    key = "<PASSWORD>"
    url = "https://aq-prom.designspark.io/prometheus"
    interval = 300

The configuration used here is slightly different and must be set as follows:

* :code:`instance` value is the login (e-mail) address used to register with DesignSpark Cloud.
* :code:`key` value is the password that you set when you activated your DesignSpark Cloud account.
  
.. warning::
   Your RS Components or DesignSpark website username and password will not work here!

.. warning::
   If you enter the wrong password it may cause your DesignSpark Cloud account to become locked-out. If you need to change this password, you should first take your device offline, change the password and then update this in your device config before powering it up again.

The :code:`interval` parameter specifies the publishing period in seconds, the minimum value for which is 300 (5 minutes).

Complete example
****************

A configuration example that uses all the available parameters::

    [ESDK]
    friendlyname = "acmecorp"
    project = "collabproject"
    location = "workshop"
    tag = "unheated"
    latitude = 53.7130128
    longitude = -1.9391832
    debug = false
    gps = true

    [NO2]
    sensitivity = -21.08

    [local]
    csv = true

    [mqtt]
    broker = "localhost"
    basetopic = "airquality"
    username = ""
    password = ""

    [prometheus.private]
    instance = "1234567890"
    key = "mkfjjknikohihfi8hfihueftue7efbjbwjfef8ywefhewhfi8eyf89wefhwefh89efu89e8fh89gdw67"
    url = "https://prometheus-prod-01-eu-west-0.grafana.net/api/prom/push"
    interval = 120

    [prometheus.aqpublic]
    instance = "username@domain.com"
    key = "mySecretPassword"
    url = "https://aq-prom.designspark.io/prometheus"
    interval = 300

.. warning::
   Don't simply cut and paste this into your aq.toml file! Read the above guidance and configure appropriately.