"""
ESP32 DMX Driver
"""

from Parameter import Parameter
from array import array
from machine import Pin, UART
import uasyncio as asyncio
import time

class DMX(Parameter):
    def __init__(self, *, devices, rx_pin: int, rx_en_pin: int, tx_pin: int, tx_en_pin: int, bus: int, delay: float, **k):
        super().__init__(**k)
        self.devices = devices
        self.tx = tx_pin
        self.tx_en = Pin(tx_en_pin, Pin.OUT, value=0)
        self.rx = rx_pin
        self.rx_en = rx_en_pin
        self.bus = bus
        self.delay = delay
        self.msg = array('B', [0, 50, 100, 150, 200])

    def update(self):
        super().update()
        loop = asyncio.get_event_loop()
        loop.create_task(self.chk())
        
    def update_msg(self):
        # someday this will go through devices and create frame
        pass
    
    async def write_frame(self):
        self.tx_en.on()
        tx = Pin(self.tx, Pin.OUT)
        tx.off()
        time.sleep_us(74)
        tx.on()
        tx = UART(self.bus, tx=self.tx, rx=self.rx, baudrate=250000)
        swriter = asyncio.StreamWriter(tx, {})
        swriter.write(self.msg)
        await swriter.drain()
        self.tx_en.off()
        
        
    def __call__(self, msg: bytes) -> None:
        pass

    async def chk(self):
        while True:
            self.update_msg()
            await self.write_frame()
            await asyncio.sleep_ms(self.delay)
        
    