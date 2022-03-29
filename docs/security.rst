Security
########

User account
************

The preconfigured image is not secure by default and at minimum the password for the :code:`pi` user should be changed!

MQTT
****

The Mosquitto broker may be configured to require a username and password, which may then be set in :code:`aq.toml`. 

Should MQTT not be required at all, Mosquitto could be disabled from starting or uninstalled.

WebSocket API
*************

The WebSocket API used by the display does not implement any sort of security.

