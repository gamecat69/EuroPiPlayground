from europi import *
from time import ticks_diff, ticks_ms, sleep_ms
import uasyncio as asyncio
from random import randint

# Overclock the Pico for improved performance.
machine.freq(250_000_000)

# Enable SMPS mode for greater anologue input accuracy
#g23 = Pin(23, Pin.OUT)
#g23.value(1)

class burst:
    def __init__(self):
        self.noteDivisions = [0, 0.08333333333, 0.1666666667, 0.25, 0.3333333333, 0.4166666667, 0.5, 0.5833333333, 0.6666666667, 0.75, 0.8333333333, 0.9166666667]
        self.previousInput = 0
        self.inputVoltage = 0
        self.bpm = 0
        self.clockStep = 0
        self.resetTimeout = 500
        self.previousTriggerTime = 0
        self.triggerDiffs = []
        self.calculateBpm = False
        self.analogInputMode = 1
        self.probability = 0
        self.minAnalogInputVoltage = 0.9
        
        self.diff = 0
        # Bursts control params
        self.numBursts = 3
        self.burstWaitTimeMs = 33

        @din.handler
        def clockTrigger():
            if randint(0,99) < self.probability:
                # Create async tasks to output bursts
                el.create_task(self.outputBurst(cv1, self.numBursts, self.burstWaitTimeMs, False))
                el.create_task(self.outputBurst(cv2, self.numBursts, int(self.burstWaitTimeMs*2), False))
                el.create_task(self.outputBurst(cv3, self.numBursts, int(self.burstWaitTimeMs*4), True))

            # If we have more than one clock step, push the time diff between steps into self.triggerDiffs
            if self.clockStep > 0 and self.calculateBpm:
                # Get the time difference between the previous and current clock triggers
                self.diff = ticks_diff(ticks_ms(), self.previousTriggerTime)
                # Add the time difference to the array of differences
                # The time difference drifts, so push the values to an array to later calculate the average to smooth out the value
                self.triggerDiffs.append(self.diff)

                if self.clockStep == 16:
                    # If we have more steps, we can use the average of all values to get a reasonably accurate BPM                    
                    self.bpm = self.calculateBpm(self.triggerDiffs)#

                    # Set the clock count back to zero and empty the array of trigger time diffs
                    self.clockStep = 0
                    self.triggerDiffs = []

            self.previousTriggerTime = ticks_ms()
            self.clockStep += 1

        #@din.handler_falling
        #def clockTriggerEnd():
        #    pass

    async def outputBurst(self, cv, num, sleepTimeMs, dropOff):
        for b in range (0, num):
            cv.voltage(1)
            if dropOff:
                sleepTimeMs += int(sleepTimeMs/1.67)
            await asyncio.sleep_ms(sleepTimeMs)
            cv.off()

    def calculateBpm(self, list):
        list.sort()
        self.averageDiff = self.average(self.triggerDiffs)
        return self.bpmFromMs(self.averageDiff)

    def median(self, lst):
        n = len(lst)
        s = sorted(lst)
        return (s[n//2-1]/2.0+s[n//2]/2.0, s[n//2])[n % 2] if n else None

    def bpmFromMs(self, ms):
        return int(1/(ms/1000)*15)

    def average(self, list):
        # median is more accurate at lower BPMs, while mean is more accurate at higher BPMs
        if list[5] <= 330:
            return sum(list) / len(list)
        else:
            return self.median(list)

    async def main(self):
        while True:
            self.processAnalogueInput()
            self.getProbability()
            #self.getTimeBetweenBursts()
            self.getNumBursts()
            self.updateScreen()

            # If I have been running, then stopped for longer than resetTimeout, reset clockStep to 0
            if self.clockStep != 0 and ticks_diff(ticks_ms(), din.last_triggered()) > self.resetTimeout:
                self.clockStep = 0
            await asyncio.sleep_ms(10)

    
    def processAnalogueInput(self):
        pass

    def updateScreen(self):
        #oled.clear() - dont use this, it causes the screen to flicker!
        oled.fill(0)
        oled.text('Input: ' + str(self.inputVoltage),0,0,1)
        if self.calculateBpm:
            oled.text('BPM: ' + str(self.bpm),0,10,1)
        # Show probability
        oled.text('P' + str(int(self.probability)), 40, 25, 1)
        # Show Time between bursts
        #oled.text('T' + str(self.burstWaitTimeMs), 76, 25, 1)
        oled.text('B' + str(self.numBursts), 76, 25, 1)
        oled.show()

    def getProbability(self):
        # If mode 1 and there is CV on the analogue input use it, if not use the knob position
        val = 100 * ain.percent()
        if self.analogInputMode == 2 and val > self.minAnalogInputVoltage:
            self.probability = val
        else:
            self.probability = k1.read_position()

    def getTimeBetweenBursts(self):
        # If mode 1 and there is CV on the analogue input use it, if not use the knob position
        val = 100 * ain.percent()
        if self.analogInputMode == 3 and val > self.minAnalogInputVoltage:
            self.burstWaitTimeMs = val * 3
        else:
            self.burstWaitTimeMs = k2.read_position() * 3

    def getNumBursts(self):
        # If mode 1 and there is CV on the analogue input use it, if not use the knob position
        val = 100 * ain.percent()
        if self.analogInputMode == 1 and val > self.minAnalogInputVoltage:
            #self.CvPattern = int((len(self.random4) / 100) * CvpVal)
            self.numBursts = int((6/100)*val)
        else:
            self.numBursts = k2.choice([1,2,3,4,5,6])

# Create instance of the class
me = burst()
# Create async event loop
el = asyncio.get_event_loop()
# Add main loop to event loop
el.create_task(me.main())
# Start the event loop
el.run_forever()