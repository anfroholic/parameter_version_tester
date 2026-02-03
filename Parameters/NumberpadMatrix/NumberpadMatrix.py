"""
Digital Input for ESP32
"""
from floe import FP, make_var
from Parameter import Parameter
import json
try:
    from machine import Pin
except:
    from fakes.machine import Pin
try:
    import uasyncio as asyncio
except:
    import asyncio
    
class NumberpadMatrix(Parameter):
    struct = 'u'  # utf-8 char 
    
    keys = [
        ['1', '2', '3', 'A'],
        ['4', '5', '6', 'B'],
        ['7', '8', '9', 'C'],
        ['*', '0', '#', 'D'],
        ]
    vals = [  # vals to tell whether button is still pressed
        [False, False, False, False],
        [False, False, False, False],
        [False, False, False, False],
        [False, False, False, False],
        ]
    
    def __init__(self, *, column_pins, row_pins, **k):
        super().__init__(**k)

        self.row = [Pin(pin, Pin.OUT) for pin in json.loads(row_pins)]
        self.column = [Pin(pin, Pin.IN, Pin.PULL_UP) for pin in json.loads(column_pins)]
        
        loop = asyncio.get_event_loop()
        loop.create_task(self.chk())


    async def chk(self):
        while True:
            for i, r in enumerate(self.row):
                r.off()
                for j, col in enumerate(self.column):
                    if not col.value():
                        if self.vals[i][j] == False:
                            self.state = self.keys[i][j]
                            self.vals[i][j] = True
                            self.send()
                    else:
                        self.vals[i][j] = False
                r.on()
            await asyncio.sleep_ms(25)
    
    
    
    