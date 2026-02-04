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
    
class SwitchPanel(Parameter):
    struct = 'u'  # string
    
    def __init__(self, *, output_pins: int, input_pins, **k):
        super().__init__(**k)
        self.outputs = [Pin(pin, Pin.OUT) for pin in json.loads(output_pins)]
        self.inputs = [Pin(pin, Pin.IN, Pin.PULL_UP) for pin in json.loads(input_pins)]
        self.state = "0000"    
        
        loop = asyncio.get_event_loop()
        loop.create_task(self.chk())

    async def chk(self):
        while True:
            state = []
            for output in self.outputs:
                output.off()
                _state = "0"
                for i_index, input in enumerate(self.inputs):
                    # print('chk', input, output)
                    if not input.value(): # we have a match
                        _state = str(i_index + 1)
                
                state.append(_state)    
                output.on()
            state = "".join(state)
            if self.state != state:
                print(state)
                self.__call__(state)
            await asyncio.sleep_ms(50)


    


    