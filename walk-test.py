#!/usr/bin/env python3
import re
import os
import subprocess
import geopy.distance
from datetime import datetime
import math
import numpy


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
        y = math.cos(math.radians(other.latitude)) * math.sin(math.radians(dLon))
        x = math.cos(math.radians(self.latitude)) * math.sin(math.radians(other.latitude)) \
            - math.cos(math.radians(other.latitude)) * math.sin(math.radians(self.latitude)) \
            * math.cos(math.radians(dLon))
        brng = numpy.arctan2(x, y)
        brng = numpy.degrees(brng)

        if brng < 0:
            brng += 360
        # print("b", x, y, dLon, brng)
        return brng

    def walk_to_dest(self, other, walk_distance):
        km_dist = self.distance_in_km(other)
        #print("Step distance (km): %.4f\tTo target: %.4f" % (walk_distance, km_dist))
        if km_dist < walk_distance:
            # Distance between A and B is less than the distance to travel,
            # then just return the point for B.
            # print(".")
            return other

        bearing = self.get_bearing(other)
        next_step = geopy.distance.distance(walk_distance).destination(self, bearing=bearing)
        mp = self.make_mp(next_step)

        return mp

    def array(self):
        # Return an array of [lat, lon]
        return [self.latitude, self.longitude]


class TablePrint():
    def __init__(self, headers, formats):
        if type(headers) != type([]):
            print("Need to initialize headers with an array.")
            exit(1)

        if type(formats) != type([]):
            print("Need to initialize formats with an array.")
            exit(1)

        if len(headers) != len(formats):
            print("Length of headers and formats need to be equal.")
            exit(1)

        self.headers = headers
        self.formats = formats
        self.counter = 0
        self.first_line = True
        self.interval = 30
        self.table_format = ""
        self.break_format = ""
        self.header_format = ""

        self.make_formats()

    def make_formats(self):
        header_len = len(self.headers)
        header_format = ""
        table_format = ""
        break_format = ""
        for i in range(header_len):
            format_len = 0
            try:
                format_len = int(re.search(r'([0-9]+)(?:\.[0-9]+|)[fds]', self.formats[i]).groups()[0])
            except:
                print("Unable to parse format rules.")
                exit(1)

            break_format += "-" + "-"*format_len + "-"
            header_format += " " + re.sub(r'(?:\.[0-9]+|)[fd]', 's', self.formats[i]) + " "
            table_format += " " + self.formats[i] + " "
            if i != header_len-1:
                table_format += "|"
                header_format += "|"
                break_format += "+"

        self.table_format = table_format
        self.header_format = header_format
        self.break_format = break_format

    def print_headers(self):
        print(self.header_format.format(*self.headers))
        print(self.break_format)

    def print_break(self):
        print(self.break_format)
        self.print_headers()

    def p(self, values):
        if self.first_line:
            self.print_headers()
            self.first_line = False
        elif self.counter % self.interval == 0:
            self.print_break()

        print(self.table_format.format(*values))
        self.counter += 1


# adb shell dumpsys location |grep -A 1 "gps provider"
adb_command = "adb shell am startservice -a theappninjas.gpsjoystick.TELEPORT --ef lat {lat} --ef lng {lng}"
minute = 60
hour = 3600
walk_speed_in_kmh = 10.0
walk_speed_in_kps = walk_speed_in_kmh / hour
pulse_timing = 3  # seconds between sending commands

distance_per_pulse = walk_speed_in_kps * pulse_timing

print("Distance per pulse (km): %f" % distance_per_pulse)

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


pt = TablePrint(["Step", "Cur Lat", "Cur Lon", "distance", "Next lat", "Next lon"],
                ["{:^4d}", "{:^10.5f}", "{:^10.5f}", "{:^8.5f}", "{:^10.5f}", "{:^10.5f}"])

print(pt.header_format)
print(pt.headers)
print(pt.table_format)


while 1:
    future_loc, ret_val = ask_coords()
    if ret_val == 1:
        print("Exiting.")
        exit(0)

    walk_distance = current.distance_in_km(future_loc)
    print("Distance in km: %5.4f" % walk_distance)
    pulses = walk_distance / distance_per_pulse
    print("Pulses: %.4f" % pulses)

    base = datetime(2021, 1, 1, 0, 0, 0).timestamp()
    offset = base + (pulses * 3)
    print("Time taken (hms): %s" % datetime.fromtimestamp(offset).strftime("%H:%M:%S"))

    step = current
    i = 1
    print("Starting point: %s" % step.format_decimal())
    print("Ending point  : %s" % future_loc.format_decimal())

    pt.print_headers()

    while i <= pulses:
        step = current.walk_to_dest(future_loc, distance_per_pulse)
        rem_distance = step.distance_in_km(future_loc)
        pt.p([i, *current.array(), rem_distance, *step.array()])
        i += 1
        current = step

    current = future_loc
