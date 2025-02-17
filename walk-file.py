import time

from ppadb.client import Client as AdbClient
from pykml import parser as kmlparser
import re
import argparse
import os
from pykml.factory import nsmap

client = AdbClient(host="127.0.0.1", port=5037)
devices = client.devices()

parser = argparse.ArgumentParser()
parser.add_argument("file", help="The name of the file to parse")
parser.add_argument("-s", "--serial", help="Serial of the device to connect to")

args = parser.parse_args()

if [].__eq__(devices):
    print("No devices connected, or unable to contact ADB server.")
    exit(1)
elif devices.__sizeof__() > 1:
    size = len(devices)
    print(f"Too many devices (found {size}) connected.")

    if os.environ.__contains__("ANDROID_SERIAL"):
        serial = os.environ["ANDROID_SERIAL"]
        print(f"Found Android Serial - {serial}")
        device = client.device(serial)
    elif args.serial is not None:
        device = client.device(args.serial)
    else:
        print(" Num | Serial")
        print("-----+------------------")
        c = 1
        for d in devices:
            print(" {:^3d} | {:<16s}".format(c, d.serial))
            c += 1

        device_id = input("Choose device to connect to: ")
        device = devices[int(device_id) - 1]

    if device.get_battery_level():
        print(f"Device accessible. Battery level: {device.get_battery_level()}")
    else:
        print("Device inaccessbile")
        exit(1)

adb_command = "am startservice -a theappninjas.gpsjoystick.TELEPORT --ef lat {lat} --ef lng {lng}"
pulse_timing = 3

with open(args.file) as file:
    kml = kmlparser.parse(file).getroot().Document

points = []
linestrings = []
namespace = {"ns": nsmap[None]}

for p in kml.findall(".//ns:Point", namespaces=namespace):
    try:
        points.append(p)
    except AttributeError:
        pass

for l in kml.findall(".//ns:LineString", namespaces=namespace):
    try:
        linestrings.append(l)
    except AttributeError:
        pass

print("KML contents")
print("  Points: ", len(points))
print("  Lines: ", len(linestrings))

coord_list = linestrings[0].coordinates.text.splitlines()
coord_list = [re.sub(r"^ +", "", re.sub(r",0$", "", c)) for c in coord_list][1:]
# print(coord_list)
# coord_string = re.sub(r"(?:,0|)\\n +", "^", linestrings[0].coordinates.text)
# print("List:",len(coord_string))
# print(coord_string)
# coord_list = coord_string.split("^")[1:]
print("List:",len(coord_list))

coord_obj = []
for c in coord_list:
    try:
        s = c.split(",")
        coord_obj.append({"lat": s[1], "lon": s[0]})
    except IndexError:
        pass


def pulse(coord):
    response = device.shell(adb_command.format(lat=coord["lat"], lng=coord["lon"]))
    time.sleep(pulse_timing)
    return response


ret = ""
for spot in coord_obj:
    print(".", end='')
    ret = pulse(spot)
    if ret.__contains__("Error"):
        print("!! Found error in traffic")
        break

