# -*- coding: utf-8 -*-
# Python script (runs on 2 and 3) to check cpu usage, cpu temperature and free space etc.
# on a Linux computer and publish the data to a MQTT server.
# RUN pip install paho-mqtt
# RUN sudo apt-get install python-pip

from __future__ import division
import subprocess
import time
import socket
import paho.mqtt.client as paho
import json
import config
import os
import psutil

# get device host name - used in mqtt topic
hostname = socket.gethostname()

def check_disk_usage(path):
    st = os.statvfs(path)
    free_space = st.f_bavail * st.f_frsize
    total_space = st.f_blocks * st.f_frsize
    disk_usage = int(100 - ((free_space / total_space) * 100))
    return disk_usage


def check_cpu_usage():
    return psutil.cpu_percent(interval=1)

def check_swap_usage():
    full_cmd = "free -t |grep -i swap | awk 'NR == 1 { if( $2 != 0 ) {print $3/$2*100} else {print 0} }'"
    swap_usage = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE).communicate()[0]
    swap_usage = round(float(swap_usage.decode("utf-8").replace(",", ".")), 1)
    return swap_usage


def check_memory_usage():
    full_cmd = "free -t | awk 'NR == 2 {print $3/$2*100}'"
    memory_usage = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE).communicate()[0]
    memory_usage = round(float(memory_usage.decode("utf-8").replace(",", ".")))
    return memory_usage


def check_cpu_temp():
    full_cmd = "cat /sys/class/thermal/thermal_zone*/temp 2> /dev/null | sed 's/\(.\)..$//' | tail -n 1"
    try:
        p = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE).communicate()[0]
        cpu_temp = p.decode("utf-8").replace('\n', ' ').replace('\r', '')
    except Exception:
        cpu_temp = 0
    return cpu_temp

def check_uptime():
    full_cmd = "awk '{print int($1/3600/24)}' /proc/uptime"
    return int(subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE).communicate()[0])


def check_model_name():
   full_cmd = "cat /sys/firmware/devicetree/base/model"
   model_name = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0].decode("utf-8")
   if model_name == '':
        full_cmd = "cat /proc/cpuinfo  | grep 'name'| uniq"
        model_name = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0].decode("utf-8")
        model_name = model_name.split(':')[1]
   return model_name


def get_os():
    full_cmd = 'cat /etc/os-release | grep -i pretty_name'
    pretty_name = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0].decode("utf-8")
    pretty_name = pretty_name.split('=')[1].replace('"', '')
    return(pretty_name)


def get_manufacturer():
    if 'Raspberry' not in check_model_name():
        full_cmd = "cat /proc/cpuinfo  | grep 'vendor'| uniq"
        pretty_name = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0].decode("utf-8")
        pretty_name = pretty_name.split(':')[1]
    else:
        pretty_name = 'Raspberry Pi'
    return(pretty_name)


def config_json(what_config):
    model_name = check_model_name()
    manufacturer = get_manufacturer()
    os = get_os()
    data = {
        "state_topic": "",
        "icon": "",
        "name": "",
        "unique_id": "",
        "unit_of_measurement": "",
	"device": {
	    "identifiers": [hostname],
	    "manufacturer": manufacturer,
	    "model": model_name,
	    "name": hostname,
        "sw_version": os
	}
    }

    data["state_topic"] = config.mqtt_topic_prefix + "/" + hostname + "/" + what_config
    data["unique_id"] = hostname + "_" + what_config
    if what_config == "cpu_usage":
        data["icon"] = "mdi:speedometer"
        data["name"] = hostname + " CPU Usage"
        data["unit_of_measurement"] = "%"
    elif what_config == "cpu_temp":
        data["icon"] = "hass:thermometer"
        data["name"] = hostname + " CPU Temperature"
        data["unit_of_measurement"] = "°C"
    elif what_config == "disk_usage":
        data["icon"] = "mdi:harddisk"
        data["name"] = hostname + " Disk Usage"
        data["unit_of_measurement"] = "%"
    elif what_config == "swap_usage":
        data["icon"] = "mdi:harddisk"
        data["name"] = hostname + " Disk Swap"
        data["unit_of_measurement"] = "%"
    elif what_config == "memory_usage":
        data["icon"] = "mdi:memory"
        data["name"] = hostname + " Memory Usage"
        data["unit_of_measurement"] = "%"
    elif what_config == "uptime_days":
        data["icon"] = "mdi:calendar"
        data["name"] = hostname + " Uptime"
        data["unit_of_measurement"] = "days"
    else:
        return ""
    # Return our built discovery config
    return json.dumps(data)


def publish_to_mqtt(cpu_usage=0, cpu_temp=0, disk_usage=0, swap_usage=0, memory_usage=0,
                    uptime_days=0):
    # connect to mqtt server
    client = paho.Client()
    client.username_pw_set(config.mqtt_user, config.mqtt_password)
    client.connect(config.mqtt_host, int(config.mqtt_port))

    # publish monitored values to MQTT
    if config.cpu_usage:
        if config.discovery_messages:
            client.publish("homeassistant/sensor/" + config.mqtt_topic_prefix + "/" + hostname + "_cpu_usage/config",
                           config_json('cpu_usage'), qos=0)
            time.sleep(config.sleep_time)
        client.publish(config.mqtt_topic_prefix + "/" + hostname + "/cpu_usage", cpu_usage, qos=1)
        time.sleep(config.sleep_time)
    if config.cpu_temp:
        if config.discovery_messages:
            client.publish("homeassistant/sensor/" + config.mqtt_topic_prefix + "/" + hostname + "_cpu_temp/config",
                           config_json('cpu_temp'), qos=0)
            time.sleep(config.sleep_time)
        client.publish(config.mqtt_topic_prefix + "/" + hostname + "/cpu_temp", cpu_temp, qos=1)
        time.sleep(config.sleep_time)
    if config.disk_usage:
        if config.discovery_messages:
            client.publish("homeassistant/sensor/" + config.mqtt_topic_prefix + "/" + hostname + "_disk_usage/config",
                           config_json('disk_usage'), qos=0)
            time.sleep(config.sleep_time)
        client.publish(config.mqtt_topic_prefix + "/" + hostname + "/disk_usage", disk_usage, qos=1)
        time.sleep(config.sleep_time)
    if config.swap_usage:
        if config.discovery_messages:
            client.publish("homeassistant/sensor/" + config.mqtt_topic_prefix + "/" + hostname + "_swap_usage/config",
                           config_json('swap_usage'), qos=0)
            time.sleep(config.sleep_time)
        client.publish(config.mqtt_topic_prefix + "/" + hostname + "/swap_usage", swap_usage, qos=1)
        time.sleep(config.sleep_time)
    if config.memory_usage:
        if config.discovery_messages:
            client.publish("homeassistant/sensor/" + config.mqtt_topic_prefix + "/" + hostname + "_memory_usage/config",
                           config_json('memory_usage'), qos=0)
            time.sleep(config.sleep_time)
        client.publish(config.mqtt_topic_prefix + "/" + hostname + "/memory_usage", memory_usage, qos=1)
        time.sleep(config.sleep_time)
    if config.uptime:
        if config.discovery_messages:
            client.publish("homeassistant/sensor/" + config.mqtt_topic_prefix + "/" + hostname + "_uptime_days/config",
                           config_json('uptime_days'), qos=0)
            time.sleep(config.sleep_time)
        client.publish(config.mqtt_topic_prefix + "/" + hostname + "/uptime_days", uptime_days, qos=1)
        time.sleep(config.sleep_time)

    # disconnect from mqtt server
    client.disconnect()


def bulk_publish_to_mqtt(cpu_usage=0, cpu_temp=0, disk_usage=0, swap_usage=0, memory_usage=0,
                         uptime_days=0):
    # compose the CSV message containing the measured values

    values = cpu_usage, float(cpu_temp), disk_usage, swap_usage, memory_usage, uptime_days
    values = str(values)[1:-1]

    # connect to mqtt server
    client = paho.Client()
    client.username_pw_set(config.mqtt_user, config.mqtt_password)
    client.connect(config.mqtt_host, int(config.mqtt_port))

    # publish monitored values to MQTT
    client.publish(config.mqtt_topic_prefix + "/" + hostname, values, qos=1)

    # disconnect from mqtt server
    client.disconnect()


if __name__ == '__main__':
    # set all monitored values to False in case they are turned off in the config
    cpu_usage = cpu_temp = disk_usage = swap_usage = memory_usage = uptime_days =  False

    # delay the execution of the script
    time.sleep(config.random_delay)

    # collect the monitored values
    if config.cpu_usage:
        cpu_usage = check_cpu_usage()
    if config.cpu_temp:
        cpu_temp = check_cpu_temp()
    if config.disk_usage:
        disk_usage = check_disk_usage('/')
    if config.swap_usage:
        swap_usage = check_swap_usage()
    if config.memory_usage:
        memory_usage = check_memory_usage()
    if config.uptime:
        uptime_days = check_uptime()
    # Publish messages to MQTT
    if config.group_messages:
        bulk_publish_to_mqtt(cpu_usage, cpu_temp, disk_usage, swap_usage, memory_usage, uptime_days)
    else:
        publish_to_mqtt(cpu_usage, cpu_temp, disk_usage, swap_usage, memory_usage, uptime_days)
