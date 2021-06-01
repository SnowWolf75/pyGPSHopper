#!/Users/charles.wheeler/git/pyGPSHopper/venv/bin/python
# This is a sample Python script.

import argparse
import platform
import re
import sys
import os
import math
import signal


adb_command = "adb shell am startservice -a theappninjas.gpsjoystick.TELEPORT --ef lat {lat} --ef lng {lng}"
minute = 60
hour = 3600
cooldown_dict = {}


# Since Windows is the odd-man-out (relating to file extensions and other things), I only test for it.
def is_windows(a=None, b=None):
    win_test = platform.system() == "Windows"
    if a is None:
        return win_test
    else:
        return a if win_test else b


def interruption(signum, frame):
    "called when read times out"
    print( 'interrupted!')
    raise IOError


def gps_jump(newcorrd):
    (newlat, newlon) = newcorrd
    print(f"Mock: {newlat}, {newlon}")
    this_adb = adb_command.format(lat=newlat, lng=newlon)
    os.system(this_adb)
    return


def build_cooldown():
    cooldown_string = """Distance| Cooldown time
2km     | 1min
4km     | 2.5min
7km     | 5min
10km    | 7min
12km    | 8min
18km    | 10min
30km    | 15min
65km    | 22min
81km    | 25min
250km   | 45min
350km   | 51min
500km   | 62min
700km   | 77min 
1000km  | 98min
1350km  | 120min
9999km  | 120min"""
    cooldown_re = re.findall(r'([0-9]+)km[^0-9]+([\.0-9]+)min', cooldown_string, re.MULTILINE)
    return {float(k) * 1000: float(v) * minute for (k, v) in cooldown_re}


def cooldown_find(distance):
    matches = {k:v for k,v in cooldown_dict.items() if k>=distance}
    return min(matches.values())


def haversine(coord1, coord2):
    R = 6372800  # Earth radius in meters
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2

    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def wait_message(timeout, message, unit):
    try:
        print('You have %0.2f %s to wait, or press Enter to jump now' % (message, unit))
        foo = input()
        return foo
    except IOError:
        # timeout
        return


def wait_if_needed(past, future):
    if not args.wait:
        # No wait needed
        return

    dist_in_meters = haversine(past, future)
    print(f"Distance: {dist_in_meters}")
    cool_in_secs = cooldown_find(dist_in_meters)
    if cool_in_secs >= hour:
        cool_adjusted = cool_in_secs / hour
        unit = "hour(s)"
    elif cool_in_secs >= minute:
        cool_adjusted = cool_in_secs / minute
        unit = "minute(s)"
    else:
        cool_adjusted = cool_in_secs
        unit = "seconds"

    signal.alarm(int(cool_in_secs))
    _ = wait_message(cool_in_secs, cool_adjusted, unit)


def print_intro():
    print("/"*73)
    print("//  No filename supplied at the prompt. Entering copy-and-paste mode.  //")
    print("//  Copy all the coordinate pairs into here that you want to queue up, //")
    print("//   then press %s to finalize. %s//"
          % (is_windows("CTRL+Z", "CTRL+D"), " "*35))
    print("/"*73, "\n")
    return


def ask_user():
    check = str(input("Parse more coordinates? (Y/N): ")).lower().strip()
    try:
        if check[0] == 'y':
            return True
        elif check[0] == 'n':
            return False
        else:
            return False
    except Exception as error:
        print("Please enter valid inputs")
        print(error)
        return ask_user()


def main():
    parser = argparse.ArgumentParser(
        description="Jump from place to place, using a list of coordinates.", allow_abbrev=True
    )
    parser.add_argument('-s', '--simulate', help="Simulate movement (no adb command sent)",
                        action="store_true", default=False)
    parser.add_argument('-w', '--wait', help="Do distance calculations and wait for cooldown.",
                        action="store_true", default=True)
    parser.add_argument('-n', '--no-wait', dest='wait', action='store_false',
                        help="Bypass the wait for cooldown")
    parser.add_argument(dest='dest_file', nargs='?', type=argparse.FileType('r', encoding='latin-1'))
    global args
    args = parser.parse_args()
    num_args = len(vars(args))
    print("args passed: %d" % len(vars(args)))

    if num_args <= 1:
        print_intro()
        waypoints = []
        line = None
        while line != "\n":
            line = sys.stdin.readline()
            waypoints.append(line)
    else:
        waypoints = args.dest_file.readlines()

    if len(waypoints) < 1:
        print("-- No waypoints entered. We're done.")
        exit(0)
    else:
        print("// After each jump, press Enter to execute the next jump.")
        print("** No safety for timeouts/distance traveled. That's all on you!")

    print("DD: waypoints length: %d" % len(waypoints))
    previous = (0.0, 0.0)
    for pair in waypoints:
        try:
            print(f"DDD: {pair}")
            current = re.match(r'^[\w\s]*([0-9.-]+)[,/ ]([0-9.-]+)', pair).groups()
            current = tuple(float(n) for n in current)
            print("-- Jumping to %.5f, %.5f" % current)
            if previous != (0.0, 0.0):
                wait_if_needed(previous, current)
            gps_jump(current)
            previous = current
        except (IndexError, AttributeError) as e:
            pass

    print("!! Done with waypoints.  !!")
    pass


# Press the green button in the gutter to run the script.
signal.signal(signal.SIGALRM, interruption)
if __name__ == '__main__':
    cooldown_dict = build_cooldown()
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

# Metric	Imperial	Time
# 1 km	    0.6 mi	    30 sec
# 5 km	    3.1 mi	    2 min
# 10 km	    6.2 mi	    6 min
# 25 km	    15.5 mi	    11 min
# 30 km	    18.6 mi	    14 min
# 65 km	    40.4 mi	    22 min
# 81 km	    50.3 mi	    25 min
# 100 km	62.1 mi	    35 min
# 250 km	155.3 mi	45 min
# 500 km	310.7 mi	1 hr
# 750 km	446 mi	    1.3 hr
# 1,000 km	621.4 mi	1.5 hr
# 1,500 km	932 mi	    2 hr
