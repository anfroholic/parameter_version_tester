"""
Neopixel Parameter for ESP32
"""

from Parameter import Parameter
from floe import FP, make_var, Stater
import machine
from neopixel import NeoPixel as NP

try:
    import uasyncio as asyncio
except:
    import asyncio
    
class NeoPixel(Parameter):
    struct = 'e'  # bytearray[3]
    
    def __init__(self, *, number_of_pixels: int, pin: int, animation: int, animations: list[FP], delay: int, **k):
        super().__init__(**k)
        self.num_pix = int(number_of_pixels)
        _pin = machine.Pin(pin, machine.Pin.OUT)
        self.neo = NP(_pin, number_of_pixels)
        
        
        self.animation = make_var(animation)
        self.animations = animations
        self.delay = make_var(delay)
        self.index = 0
        
        self.blinker = False
        self.blink_colors = (b'\x00\x05\x05', b'\x00\x05\x00')
        self.blink_delay = 500
        
        self.loop = None
        # self.off()

    def __call__(self, state: bytearray):
        if state is not None:
            self.state = state
        self.fill(state)
        super().__call__(state)
        
    async def chk(self):
        while True:
            if self.blinker:
                self._blink_animation()
                await asyncio.sleep_ms(self.blink_delay)
            else:
                self.animations[self.animation.state - 1].animate(self, self.index)
                await asyncio.sleep_ms(self.delay.state)
                
            self.index += 1
    
    def update(self):
        super().update()        
        if self.animations is None:
            return
        
        if not isinstance(self.animations, list):
            self.animations = [self.animations]
        self.animations = [self.iris.p[animation.pid] for animation in self.animations]
        self.animation.add_hot(self.change_animation)
        if self.animation.state != 0:
            self.change_animation(self.animation.state)
        else:
            self.fill((0,0,0))
        
    
    def fill(self, color: tuple[int, int, int]):
        for pix in range(self.num_pix):  # fill the strip/ring
            self.neo[pix] = color
            self.neo.write()
            
    def off(self):
        self.fill((0,0,0))
        self.change_animation(0)
    
    def blink_test(self):
        self.start_blinker((b'\x05\x03\x00', b'\x02\x02\x02'), 200)
    # neo_status.blink_test()    
    def start_blinker(self, colors: tuple[bytearray, bytearray], delay: int):
        self.blink_colors = colors
        self.blink_delay = delay
        self.blinker = True
        if not self.loop:
            loop = asyncio.get_event_loop()
            self.loop = loop.create_task(self.chk())
    
    def _blink_animation(self):
        # blinks 2 colors
        if self.index % 2:
            self.fill(self.blink_colors[0])
        else:
            self.fill(self.blink_colors[1])
        
    async def _lightshow(self):
        red = (5,0,0)
        green = (0,5,0)
        blue = (0,0,5)
        self.fill(red)
        await asyncio.sleep(.5)
        self.fill(green)
        await asyncio.sleep(.5)
        self.fill(blue)
        await asyncio.sleep(.5)
        self.loop = None
        self.off()

    def lightshow(self):
        if not self.loop:
            loop = asyncio.get_event_loop()
            self.loop = loop.create_task(self._lightshow())

    def change_animation(self, animation: int): 
        if animation == 0:
            # turn off neo
            if self.loop or self.blinker:
                self.loop.cancel()
                self.loop = None
            self.fill((0,0,0))
            self.animation(0)
        else:
            self.animation.state = animation
            self.index = 0
            if not self.loop:
                loop = asyncio.get_event_loop()
                self.loop = loop.create_task(self.chk())


