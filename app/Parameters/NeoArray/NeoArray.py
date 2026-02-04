"""
Neopixel Parameter for ESP32
"""

from Parameter import Parameter
from floe import FP, make_var
import json
PIN_LIST = str  # this is a json blob list[int]

try:
    import machine
except:
    import fakes.machine as machine
try:
    from neopixel import NeoPixel as NP
except:
    from fakes.neopixel import NeoPixel as NP
try:
    import uasyncio as asyncio
except:
    import asyncio
    
    
    
class NeoArray(Parameter):
    struct = '3B'  # bytearray[3]
    
    def __init__(self, number_of_pixels: int, pins: PIN_LIST, animation: int, animations: list[FP], delay: int, **k):
        super().__init__(**k)
        self.num_pix = int(number_of_pixels)
        self.neos: tuple[NP] = tuple([NP(machine.Pin(pin, machine.Pin.OUT), number_of_pixels) for pin in json.loads(pins)])
        self.animation = make_var(animation)
        self.animations = animations
        self.delay = make_var(delay)
        self.index = 0
        self.off()
        
        self.loop = None

    def __call__(self, color: tuple[int, int, int]):
        if color is not None:
            self.color = color
        self.fill(color)
        super().__call__(color)
    
    def update(self):
        super().update()
        if not isinstance(self.animations, list):
            self.animations = [self.animations]
        self.animations = [self.iris.p[animation.pid] for animation in self.animations]
        self.animation.add_hot(self.change_animation)
    
    async def chk(self):
        while True:
            self.animations[self.animation - 1].animate(self, self.index)
            self.index += 1
            await asyncio.sleep_ms(self.delay.state)
            
    def fill(self, color: tuple[int, int, int]):
        for neo in self.neos:  # fill the strip/ring
            self.fill_strip(neo, color)
    
    def fill_strip(self, strip: NP, color: tuple[int, int, int]):
        for i in range(self.num_pix):
            strip[i] = color
            strip.write()
            
    def off(self):
        self.fill((0,0,0))

    def change_animation(self, animation: int):
        if animation == 0:
            if self.loop:
                self.loop.cancel()
                self.loop = None
            self.off()
        else:
            self.animation = animation
            self.index = 0
            if not self.loop:
                loop = asyncio.get_event_loop()
                self.loop = loop.create_task(self.chk())

            
    