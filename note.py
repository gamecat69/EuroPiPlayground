from europi import *

# Overclock the Pico for improved performance.
machine.freq(250_000_000)

v = 2

for cv in cvs:
    cv.voltage(v)