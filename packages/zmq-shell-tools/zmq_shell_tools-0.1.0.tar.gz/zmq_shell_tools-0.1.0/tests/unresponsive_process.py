import sys
from signal import SIGINT, SIGTERM, signal
from time import sleep

# don't handle ending signals at all
for sig in (SIGINT, SIGTERM):
    signal(sig, lambda num, stack: None)

# notify that new signal handlers are set up
sys.stdout.write("ready\n")
sys.stdout.flush()

# run indefinitely
while True:
    sleep(1)
