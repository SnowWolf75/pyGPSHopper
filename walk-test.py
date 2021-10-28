#!/usr/bin/env python3
import re
import os
import subprocess
import geopy.distance
from datetime import datetime
import math


class MyPoint(geopy.Point):
    # def __init__(self, ln, lg):
    #     self.latitude = ln
    #     self.longitude = lg

    def make_mp(self, temp_point):
        return MyPoint(temp_point.latitude, temp_point.longitude)

    def getLat(self):
        # Getter method for a Coordinate object's x coordinate.
        # Getter methods are better practice than just accessing an attribute directly
        return self.latitude

    def getLon(self):
        # Getter method for a Coordinate object's y coordinate
        return self.longitude

    # def __str__(self):
    #     return '<' + str(self.getLat()) + ',' + str(self.getLon()) + '>'
    #
    # def __eq__(self, other):
    #     return self.longitude == other.longitude and self.latitude == other.latitude
    #
    # def __repr__(self):
    #     return "Coordinate(%d, %d)" % (self.latitude, self.longitude)

    def distance_in_km(self, other):
        a = (self.latitude, self.longitude)
        b = (other.latitude, other.longitude)
        return geopy.distance.distance(a, b).km

    def get_bearing(self, other):
        # Calculate the bearing to the destination
        dLon = other.longitude - self.longitude
        y = math.sin(dLon) * math.cos(other.latitude)
        x = math.cos(self.latitude) * math.sin(other.latitude) - math.sin(self.latitude) * math.cos(other.latitude) * math.cos(dLon)
        print("b",x,y,dLon)
        brng = math.atan2(y, x)
        if brng < 0:
            brng += 360
        return brng

    def walk_to_dest(self, other, distance):
        if self.distance_in_km(other) < distance:
            # Distance between A and B is less than the distance to travel,
            # then just return the point for B.
            print(".")
            return other

        bearing = self.get_bearing(other)
        offset = geopy.distance.distance(distance).destination(other, bearing=bearing)
        mp = self.make_mp(offset)

        return mp



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
current = MyPoint(float(lat), float(lon))


def ask_coords():
    check = str(input("New coords to walk to (comma sep) or Enter to exit: ")).lower().strip()
    try:
        if check == '':
            return MyPoint(0, 0), 1

        pair = re.search("([0-9.-]+)[, ]+([0-9.-]+)", check)
        my_lat = float(pair.groups()[0])
        my_lon = float(pair.groups()[1])
        return MyPoint(my_lat, my_lon), 0
    except AttributeError:
        print("Error during catch! ", end='')
        return MyPoint(0, 0), 1


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

    step = current
    i = 0
    while step != future_loc:
        step = current.walk_to_dest(future_loc, distance_per_pulse_km)
        print("Step %d, Coords: %s" % (i, step.format_decimal()))
        i += 1
        current = step

    current = future_loc
