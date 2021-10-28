#!/usr/bin/env python3
import re
import os
import subprocess
import geopy.distance
from datetime import datetime

class Coordinate(object):
    def __init__(self, ln, lg):
        self.lat = ln
        self.lon = lg

    def getLat(self):
        # Getter method for a Coordinate object's x coordinate.
        # Getter methods are better practice than just accessing an attribute directly
        return self.lat

    def getLon(self):
        # Getter method for a Coordinate object's y coordinate
        return self.lon

    def __str__(self):
        return '<' + str(self.getLat()) + ',' + str(self.getLon()) + '>'

    def __eq__(self, other):
        return self.lon == other.lng and self.lat == other.lat

    def __repr__(self):
        return "Coordinate(%d, %d)" % (self.lat, self.lon)

    def distance_in_km(self, other):
        a = (self.lat, self.lon)
        b = (other.lat, other.lon)
        return geopy.distance.distance(a, b).km


# adb shell dumpsys location |grep -A 1 "gps provider"
adb_command = "adb shell am startservice -a theappninjas.gpsjoystick.TELEPORT --ef lat {lat} --ef lng {lng}"
minute = 60
hour = 3600
walk_speed_in_kmh = 10.0
walk_speed_in_mps = (walk_speed_in_kmh * 1000) / hour
pulse_timing = 3  # seconds between sending commands

distance_per_pulse = walk_speed_in_mps * pulse_timing
distance_per_pulse_km = (walk_speed_in_kmh * pulse_timing) / hour

print("Distance per pulse (km): %f" % distance_per_pulse_km)

process = subprocess.Popen('adb shell dumpsys location |grep -A 1 "Last Known Locations:"', shell=True,
                           stdout=subprocess.PIPE)
start_location = str(process.stdout.read())

print("Lines: ", start_location)
start_coords = re.search("\[[\w]* ([0-9.-]+),([0-9.-]+)", start_location)
print(start_coords)
try:
    lat, lon = start_coords.groups()
except AttributeError:
    print("borky bork")
    exit(1)

print("Starting Coords:\n\tLat: %s\tLon: %s" % (lat, lon))
current = Coordinate(ln=lat, lg=lon)


def ask_coords():
    check = str(input("New coords to walk to (comma sep) or Enter to exit: ")).lower().strip()
    try:
        if check == '':
            return Coordinate(0, 0), 1

        pair = re.search("([0-9.-]+)[, ]+([0-9.-]+)", check)
        my_lat = float(pair.groups()[0])
        my_lon = float(pair.groups()[1])
        return Coordinate(ln=my_lat, lg=my_lon), 0
    except AttributeError:
        print("Error during catch! ", end='')
        return Coordinate(0, 0), 1


while 1:
    future_loc, ret_val = ask_coords()
    if ret_val == 1:
        print("Exiting.")
        exit(0)

    walk_distance = current.distance_in_km(future_loc)
    print("Distance in km: %5.4f" % walk_distance)
    pulses = (walk_distance * 1000) / distance_per_pulse
    print("Pulses: %.4f" % pulses)

    base = datetime(2021, 1, 1, 0, 0, 0).timestamp()
    offset = base + (pulses * 3)
    print("Time taken (hms): %s" % datetime.fromtimestamp(offset).strftime("%H:%M:%S"))

    current = future_loc
