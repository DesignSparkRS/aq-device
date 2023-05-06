Installation
------------

A pre-configured Micro SD card image is provided and presently the supported method of installation.

The latest image is dated: :code:`5th May 2023`

.. note:: 

   This release adds support for the very latest Main board (labelled v1.0) and the NO2, FDH and NRD sensors.
   If you have been provided with any of these and are running an older release, please upgrade.

Start by downloading the image:

https://downloads.designspark.io/projects/aq-device/images/aq-pi-050523.zip

Following which this should be uncompressed and written out to a Micro SD card that is at least 8GB in size. 

.. tip::

   This is just the same as when writing out a regular Raspbian OS image. 
   Those running Linux or Mac OS and familiar with the command line can use :code:`dd`, whereas
   `balenaEtcher <https://www.balena.io/etcher/>`_ is a popular GUI option that is available for Windows, 
   Linux and Mac.

.. warning:: 

   If you are upgrading from an earlier image, don't forget to make a copy of your configuration file and to copy any logged data from the Micro SD card.
