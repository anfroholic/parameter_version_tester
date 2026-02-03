"""
Analog Input for ESP32
"""

from floe import FP, make_var
from Parameter import Parameter
try:
    import machine
except:
    import fakes.machine as machine
try:
    import uasyncio as asyncio
except:
    import asyncio    

class QrReader(Parameter):
    struct = 'u'  # unint16
    
    def __init__(self, *, buzzer_obj, buzz_on_read, rx, tx, uart, **k):
        super().__init__(**k)
        self.uart = machine.UART(uart, baudrate=115200, tx=tx, rx=rx)
        self.buzzer = make_var(buzzer_obj)
        self.buzz_on_read = make_var(buzz_on_read)
        loop = asyncio.get_event_loop()
        loop.create_task(self.chk())
        
    async def chk(self):
        while True:
            if self.uart.any():
                code = self.uart.readline().decode('utf8').strip('\r')
                self.__call__(code)
                if self.buzz_on_read.state:
                    loop = asyncio.get_event_loop()
                    loop.create_task(self.do_buzz())
            await asyncio.sleep_ms(50)
            
    async def do_buzz(self):
        self.buzzer(True)
        await asyncio.sleep_ms(200)
        self.buzzer(False)
        

    