"""
ESP32 pwm driver    
"""
from floe import FP, make_var, Stater
from Parameter import Parameter
try:
    import machine
except:
    import fakes.machine as machine
try:
    import utime
except:
    import fakes.utime as utime
try:
    import uasyncio as asyncio
except:
    import asyncio

class SimpleFeeder(Parameter):
    struct = '?'  # bool
    
    def __init__(self, *, 
                 servo_pin, 
                 button_pin, 
                 button_pullup,  
                 freq,
                 len_part: int=1,
                 duty_feed: float, 
                 duty_retract: float, 
                 **k):
        
        super().__init__(**k)
        self.state = False
        if button_pullup == 'pullup':
            self.button_pin = machine.Pin(button_pin, mode=machine.Pin.IN, pull=machine.Pin.PULL_UP)
        elif button_pullup == 'pulldown':
            self.button_pin = machine.Pin(button_pin, mode=machine.Pin.IN, pull=machine.Pin.PULL_DOWN)
        else:
            self.button_pin = machine.Pin(button_pin, mode=machine.Pin.IN)

        self.servo_pin = servo_pin
        self.freq = freq

        self.len_part = make_var(len_part)
        self.duty_feed = make_var(duty_feed)
        self.duty_retract = make_var(duty_retract)
        self.pwm = None
        
        loop = asyncio.get_event_loop()
        loop.create_task(self.chk())

    def __call__(self, state: bool, **k):
        do_feed = False
        if state is True and self.state is False:
            do_feed = True
        super().__call__(state)
        if do_feed:
            loop = asyncio.get_event_loop()
            loop.create_task(self.do_feed())
            
    def update(self):
        super().update()
        self.pwm = machine.PWM(machine.Pin(self.servo_pin), freq=self.freq, duty=0)
        utime.sleep(.02)
        # self.pwm.deinit()
                  
    async def do_feed(self):
        # self.pwm.init(freq=self.freq, duty=0)
        await asyncio.sleep(.02)
        for _ in range(self.len_part.state):
            self.pwm.duty(self.duty_retract.state)
            await asyncio.sleep(.6)
            dif = int((self.duty_feed.state - self.duty_retract.state)/2)
            for i in range(dif):
                duty = self.duty_retract.state + (i*2)
                self.pwm.duty(duty)
                await asyncio.sleep(.02)
            self.pwm.duty(self.duty_feed.state)
            await asyncio.sleep(.05)
                
        self.pwm.duty(0)
        await asyncio.sleep(.01)
        # self.pwm.deinit()
        self.__call__(False)
        
    async def chk(self):
        while True:
            if not self.button_pin.value() and not self.state:
                self.__call__(True)
            await asyncio.sleep(.1)



    
