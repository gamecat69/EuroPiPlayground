from europi import *
from time import ticks_diff, ticks_ms, sleep_ms
import uasyncio as asyncio

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
        self.diff = 0
        # Bursts control params
        self.numBursts = 5
        self.burstWaitTimeMs = 25

        @din.handler
        def clockTrigger():
            # Create an async task to output bursts
            el.create_task(self.outputBurst(cv1, self.numBursts, self.burstWaitTimeMs))
            el.create_task(self.outputBurst(cv2, self.numBursts, int(self.burstWaitTimeMs*2)))
            el.create_task(self.outputBurst(cv3, self.numBursts, int(self.burstWaitTimeMs*4)))

            # If we have more than one clock step, push the time diff between steps into self.triggerDiffs
            if self.clockStep > 0:
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

    async def outputBurst(self, cv, num, sleepTimeMs):
        for b in range (0, num):
            cv.voltage(1)
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
        oled.text('BPM: ' + str(self.bpm),0,10,1)
        oled.show()

# Create instance of the class
me = burst()
# Create async event loop
el = asyncio.get_event_loop()
# Add main loop to event loop
el.create_task(me.main())
# Start the event loop
el.run_forever()