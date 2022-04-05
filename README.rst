ESDK Air Quality Application (aq-device)
----------------------------------------

.. image:: https://raw.githubusercontent.com/DesignSparkRS/aq-device/main/docs/images/aq-display.jpg
   :alt: Air Quality application local display

DesignSpark Air Quality Project application for the `Environmental Sensor Development Kit (ESDK) hardware <https://www.rs-online.com/designspark/introducing-the-environmental-sensor-development-kit>`_. 

The aq-device application:

* Reads sensors
* Provides a local display
* Optionally:
  
  * Publishes measurements to one or more remote time series databases
  * Logs measurements to a local CSV file

Hardware access is via the :doc:`DesignSpark.ESDK library <esdklib:index>`.

Configuration is via a single TOML file.

Components
==========

================ ================================================
Directory        Description
================ ================================================
dashboard        HTML + JavaScript local UI
docs             RST documentation sources
firmware         Python application
================ ================================================

Documentation
=============

Documentation is available on `docs.designspark.io <https://docs.designspark.io/projects/aq-device>`_.

Licence
=======

The aq-device project is copyright 2021, 2022 RS Components Ltd and licensed under the the Apache License, Version 2.0.
