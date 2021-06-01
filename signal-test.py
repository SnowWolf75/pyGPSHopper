#!/Users/charles.wheeler/git/pyGPSHopper/venv/bin/python
import signal
TIMEOUT = 5 # number of seconds your want for timeout


def interrupted(signum, frame):
    "called when read times out"
    print( 'interrupted!')
    raise IOError


signal.signal(signal.SIGALRM, interrupted)


def wait_message(timeout, unit):
    try:
            print(f'You have ${timeout} ${unit} to wait, or press Enter to jump now')
            foo = input()
            return foo
    except:
            # timeout
            return


# set alarm
signal.alarm(TIMEOUT)
s = wait_input()
# disable the alarm after success
signal.alarm(0)
print('You typed', s)
