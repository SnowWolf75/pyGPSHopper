#!/Users/charles.wheeler/git/pyGPSHopper/venv/bin/python
# This is a sample Python script.

import argparse
import platform
import re
import sys


def is_windows(a=None, b=None):
    win_test = platform.system() == "Windows"
    if a is None:
        return win_test
    else:
        return a if win_test else b


def gps_jump(newlat, newlon):
    print(f"Mock: {newlat}, {newlon}")
    return


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
    parser.add_argument(dest='dest_file', nargs='?', type=argparse.FileType('r', encoding='latin-1'))
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
        waypoints = open(args.dest_file).readlines()

    if len(waypoints) < 1:
        print("-- No waypoints entered. We're done.")
        exit(0)
    else:
        print("// After each jump, press Enter to execute the next jump.")
        print("** No safety for timeouts/distance traveled. That's all on you!")

    print("DD: waypoints length: %d" % len(waypoints))
    for pair in waypoints:
        try:
            print(f"DDD: {pair}")
            (lat, lon) = re.match(r'^\W*([0-9.-]+)[,/ ]([0-9.-]+)', pair).groups()
            print(f"-- Jumping to {lat}, {lon}")
            gps_jump(lat, lon)
            input()
        except IndexError:
            pass

    print("!! Done with waypoints.  !!")
    pass


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
