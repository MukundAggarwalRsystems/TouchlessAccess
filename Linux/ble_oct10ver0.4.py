"""
1. Takes Input from the user.
2. Scan for bluetooth devices in range
3. Check the distance of the Device
"""
from __future__ import division
import datetime
import time
import pexpect
import subprocess
import sys
import json
import bluetooth
import os

import parameters

class BluetoothctlError(Exception):
    """This exception is raised, when bluetoothctl fails to start."""
    pass


class Bluetoothctl:
    """A wrapper for bluetoothctl utility."""
    global devices_dict, message_record, system_config
    global device_id #, latitude, longitude
    global scan_interval
    global transmission_flag, signature_flag, debug_flag

    def __init__(self):
        out = subprocess.check_output("rfkill unblock bluetooth", shell = True)
        self.child = pexpect.spawn("bluetoothctl", echo = False)
        self.devices_dict = {}
        self.message_record = {}
        self.system_config = {}
        self.distance_thres = 3  #Threshold Distance to open the gate
        self.device_id = ""
        self.scan_interval = 1  #Scan for devices after this time 
        self.gate_flag = 0      #Gate Flag to indicate the status of gate
        self.MPower = -70       #1 meter rssi
        self.en_factor = 2              #Environment factor

    def save_config(self, system_config):
        """Creating record to save and send to Subscriber"""
        config_filename = parameters.system_config_filename
        IoT_device_config = open(config_filename,'w')
        print >> IoT_device_config, system_config
        IoT_device_config.close()


    def read_config(self):
        """ Reading system configuration from the file """
        config = []
        config_filename = parameters.system_config_filename
        IoT_device_config = open(config_filename,'r')
        config = IoT_device_config.readline()
        try:
            config = json.loads(config.replace("\'", '"'))
            self.distance_thres = str(config["distance_thres"])
        except ValueError:
            print "JSON Value Format Error"
        except KeyError:
            print "JSON Key format Error"
        except TypeError:
            print "JSON Type format Error"

        IoT_device_config.close()


    def credential_setup(self):
        self.distance_thres = raw_input("Enter the Distance (to open the gate) : ")
        self.system_config["distance_thres"] = self.distance_thres
        bl.save_config(self.system_config)


    def get_output(self, command, pause = 0):
        """Run a command in bluetoothctl prompt, return output as a list of lines."""
        self.child.send(command + "\n")
        time.sleep(pause)
        start_failed = self.child.expect([pexpect.TIMEOUT, "bluetooth", pexpect.EOF])

        if start_failed != 1:
            raise BluetoothctlError("Bluetoothctl failed after running " + command)

        return self.child.before.split("\r\n")


    def start_scan(self):
        """Start bluetooth scanning process."""
        try:
            out = self.get_output("scan on")
        except BluetoothctlError, e:
            print(e)
            return None

    def stop_scan(self):
        """Stopping bluetooth scanning process."""
        try:
            out = self.get_output("scan off")
        except BluetoothctlError, e:
            print(e)
            return None

    def parse_device_info(self, info_string):
        """Parse a string corresponding to a device."""
        device = {}
        block_list = ["[\x1b[0;", "removed"]
        string_valid = not any(keyword in info_string for keyword in block_list)

        if string_valid:
            try:
                device_position = info_string.index("Device")
            except ValueError:
                pass
            else:
                if device_position > -1:
                    attribute_list = info_string[device_position:].split(" ", 2)
                    device = {
                        "mac_address": attribute_list[1],
                        "name": attribute_list[2]
                    }
        return device


    def get_available_devices(self):
        """Return a list of tuples of paired and discoverable devices."""
        
        available_devices_count = 0
        available_devices = []
        try:
            out = self.get_output("devices")
        except BluetoothctlError, e:
            print(e)
            return None
        else:
            for line in out:
                device = self.parse_device_info(line)
                if device:
                    available_devices.append(device)
                    available_devices_count = available_devices_count + 1;

        self.devices_dict["devices"] = available_devices
        self.devices_dict["available devices"] = available_devices_count
        return self.devices_dict

    def get_device_info(self, mac_address):
        """Get device info by mac address."""
        try:
            out = self.get_output("info " + mac_address)
        except BluetoothctlError, e:
            print(e)
            return None
        else:
            return out

    def display_scan_info(self, devices_count):
        """Display required information of scanned devices on terminal"""
        for i in range(0, devices_count):
            mac_address = devices[i]['mac_address']
            name = devices[i]['name']
            device_info = bl.get_device_info(mac_address)
            #print(device_info)
            if device_info != None:
                device_info_len = len(device_info)
                search = "\tRSSI"
                for j in range(1,device_info_len-1):
                    parameters = {}
                    parameters = device_info[j]
                    value = parameters.split(": ")
                    if value[0] == search :
                        rssi = value[1]
                        print(mac_address + " : " + rssi + "(" + name + ")")


    def subscriber_lookup(self,devices_count):
        """Lookup the subscriber list, which are in range"""
        subscriber = ""
        for i in range(0, devices_count):
            mac_address = devices[i]['mac_address']
            sub_filename = parameters.subscriber_filename
            subscriberlist = open(sub_filename,'r')
            for line in subscriberlist:
                if line.rstrip().lower() == mac_address.lower():
                    subscriber = mac_address
                    break
            if (subscriber != ""):
                subscriberlist.close()
                break
            subscriberlist.close()
        return subscriber

    def search_subscriber(self, devices_count):
        """Transmit the data, if any subscriber is in the range of IoT device"""
        subscriber = bl.subscriber_lookup(devices_count)
        if subscriber == "":
            print "No subscriber in range"
            if bl.gate_flag == 1: #Check the flag
                print "subscriber lost. closing the gate"
                tempfile = open("/home/root/temp.txt","w")
                tempfile.write("close")
                tempfile.close()
                bl.gate_flag = 0
        else:
            print "subscriber in range is :",subscriber
            print "Check the RSSI"
	    device_info = bl.get_device_info(subscriber)
            if device_info != None:
                device_info_len = len(device_info)
                search = "\tRSSI"
                for j in range(1,device_info_len-1):
                    parameters = {}
                    parameters = device_info[j]
                    value = parameters.split(": ")
                    if value[0] == search :
                        rssi = value[1]
                        print(subscriber + " : " + rssi)
	                
                        distance = bl.rssi_to_distance(int(rssi))
                        print "Returned distance : ", distance
                        print "thres distance : ", bl.distance_thres
                        
                        if distance <= float(bl.distance_thres):
			    print "open the door"
                            tempfile = open("/home/root/temp.txt","w")
                            tempfile.write("open")
                            tempfile.close()
                            bl.gate_flag = 1
                        
                        if distance > float(bl.distance_thres):
                            if bl.gate_flag == 1:
			        print "close the door"
                                tempfile = open("/home/root/temp.txt","w")
                                tempfile.write("close")
                                tempfile.close()
                                bl.gate_flag = 0

    def rssi_to_distance(self, RSSI):
        distance = pow(10,(bl.MPower-RSSI)/(10*bl.en_factor))
        return distance

if __name__ == "__main__":

    bl = Bluetoothctl()
    print("Touchless Access")
    config_filename = parameters.system_config_filename
    IoT_device_config = open(config_filename,'r')
    config = IoT_device_config.readline()
    print "Current configuration - ",config
    config_flag = raw_input("Do you want to continue with existing configuration? (Y/N) : ")
    if (config_flag == "N" or config_flag == "n"):
        bl.credential_setup()
    else:
        bl.read_config()
    previous_devices_count = 0
    print "close the door"
    tempfile = open("/home/root/temp.txt","w")
    tempfile.write("close")
    tempfile.close()
    bl.gate_flag = 0

    while 1:
        bl.start_scan()
        print("Scanning for " + str(bl.scan_interval) + " seconds...")
        for i in xrange(0, int(bl.scan_interval)):
            print ("."),
            time.sleep(1)

        print("\n")
        json_array = bl.get_available_devices()
        devices_count = json_array['available devices']
        devices = json_array['devices']
        bl.display_scan_info(devices_count)
        bl.search_subscriber(devices_count)
        bl.stop_scan()

    IoT_device_config.close()

