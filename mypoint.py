import subprocess
import time

from geographiclib.geodesic import Geodesic
import geopy.distance
from datetime import datetime
import math
import numpy
from random import SystemRandom

jitter = SystemRandom()


class MyPoint(geopy.Point):
    # def __init__(self, ln, lg):
    #     self.latitude = ln
    #     self.longitude = lg

    minute = 60
    hour = 3600
    walk_speed_in_kmh = 10.0
    walk_speed_in_kps = walk_speed_in_kmh / hour
    bearing_jitter = 5.0  # degrees +/- to randomly alter the bearing. especially useful for long walks.
    pulse_timing = 3  # seconds between sending commands

    distance_per_pulse = walk_speed_in_kps * pulse_timing

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

    def get_new_bearing(self, other):
        fwd_azimuth = Geodesic.WGS84.Inverse(*self.array(), *other.array())['azi1']

        # Add some jitter to the bearing
        fwd_azimuth += self.bearing_jitter - (jitter.random() * 2 * self.bearing_jitter)
        # print("FSA",fwd_azimuth)
        return fwd_azimuth

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
        # print("Step distance (km): %.4f\tTo target: %.4f" % (walk_distance, km_dist))
        if km_dist < walk_distance:
            # Distance between A and B is less than the distance to travel,
            # then just return the point for B.
            # print(".")
            return other

        bearing = self.get_new_bearing(other)
        next_step = geopy.distance.distance(walk_distance).destination(self, bearing=bearing)
        self.send_step(next_step)
        mp = self.make_mp(next_step)

        return mp, bearing

    def array(self):
        # Return an array of [lat, lon]
        return [self.latitude, self.longitude]


print("Distance per pulse (km): %f" % distance_per_pulse)

