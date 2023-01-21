# Linux MQTT Monitor

Forked from [Raspberry Pi MQTT Monitor](https://github.com/hjelev/rpi-mqtt-monitor)

# Installation

## Automated Installation
There is an automated bash installation, its working but not extensively tested (recently updated).

Run this command to use the automated installation:

```bash
bash <(curl -s https://raw.githubusercontent.com/czornikk/linux-mqtt-monitor/master/remote_install.sh)
```
Linux MQTT monitor will be intalled in the location where the auto installer is called, inside a folder named linux-mqtt-monitor.

The auto-installer needs the software below and will install it if its not found:
* python (2 or 3)
* python-pip
* git
* paho-mqtt
* psutil

Only python is not automatically installed, the rest of the dependancies should be handeled by the auto installation.
It will also help you configure the host and credentials for the mqtt server in config.py and create the cronjob configuration for you.
