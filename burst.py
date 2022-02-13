from europi import *
from time import ticks_diff, ticks_ms

# Overclock the Pico for improved performance.
machine.freq(250_000_000)

# Enable SMPS mode for greater anologue input accuracy
g23 = Pin(23, Pin.OUT)
g23.value(1)

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

        @din.handler
        def clockTrigger():
            # If we have more than one clock step, push the time diff between steps into self.triggerDiffs
            if self.clockStep > 1:
                diff = ticks_diff(ticks_ms(), self.previousTriggerTime)
                self.triggerDiffs.append(diff)
                # If we have more steps, we can use the average of all values to get a reasonably accurate BPM
                if self.clockStep == 16:
                    
                    self.triggerDiffs.sort()


                    self.averageDiff = sum(self.triggerDiffs) / len(self.triggerDiffs)
                    print('Mean:' + str(self.bpmFromMs(self.averageDiff)))
                    
                    self.averageDiff = self.median(self.triggerDiffs)
                    print('Median:' + str(self.bpmFromMs(self.averageDiff)))

                    self.averageDiff = self.average(self.triggerDiffs)
                    self.bpm = self.bpmFromMs(self.averageDiff)

                    self.clockStep = 0
                    self.triggerDiffs = []

                    #self.bpm = int(1/(self.averageDiff/1000)*15)
            self.previousTriggerTime = ticks_ms()
            self.clockStep += 1

    def median(self, lst):
        n = len(lst)
        s = sorted(lst)
        return (s[n//2-1]/2.0+s[n//2]/2.0, s[n//2])[n % 2] if n else None

    def bpmFromMs(self, ms):
        #return 60 / (ms * 1000)
        return int(1/(ms/1000)*15)

    def average(self, list):
        # median is more accurate at lower BPMs, while mean is more accurate at higher BPMs
        #80  bpm = 181
        #100 bpm =  151
        print(list[5])
        if list[5] <= 330:
            return sum(list) / len(list)
        else:
            return self.median(list)

    def main(self):
        while True:
            self.processAnalogueInput()
            self.updateScreen()

            # If I have been running, then stopped for longer than resetTimeout, reset clockStep to 0
            if self.clockStep != 0 and ticks_diff(ticks_ms(), din.last_triggered()) > self.resetTimeout:
                self.clockStep = 0
                print('resetting clockStep')

    
    def processAnalogueInput(self):
        pass

    def updateScreen(self):
        #oled.clear() - dont use this, it causes the screen to flicker!
        oled.fill(0)
        oled.text('Input: ' + str(self.inputVoltage),0,0,1)
        oled.text('BPM: ' + str(self.bpm),0,10,1)
        oled.show()

me = burst()
me.main()