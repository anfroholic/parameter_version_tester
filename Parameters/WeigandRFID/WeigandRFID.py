"""
Analog Input for ESP32
"""

from floe import FP, make_var
from Parameter import Parameter

import machine
try:
    import uasyncio as asyncio
except:
    import asyncio    



"""
weigand.py - read card IDs from a wiegand card reader

(C) 2017, 2022 Paul Jimenez - released under LGPLv3+
"""

from machine import Pin
import utime

CARD_MASK = 0b11111111111111110 # 16 ones
FACILITY_MASK = 0b1111111100000000000000000 # 8 ones

# Max pulse interval: 2ms
# pulse width: 50us

class Wiegand:
    def __init__(self, pin0, pin1, callback, timer_id=0):
        """
        pin0 - the GPIO that goes high when a zero is sent by the reader
        pin1 - the GPIO that goes high when a one is sent by the reader
        timer_id - the Timer ID to use for periodic callbacks
        callback - the function called (with two args: card ID and cardcount)
                   when a card is detected.  Note that micropython interrupt
                   implementation limitations apply to the callback!
        """
        self.pin0 = Pin(pin0, Pin.IN)
        self.pin1 = Pin(pin1, Pin.IN)
        self.callback = callback
        self.last_card = None
        self.next_card = 0
        self._bits = 0
        self.pin0.irq(trigger=Pin.IRQ_FALLING, handler=self._on_pin0)
        self.pin1.irq(trigger=Pin.IRQ_FALLING, handler=self._on_pin1)
        self.last_bit_read = None
        self.timer = machine.Timer(timer_id)
        self.timer.init(period=111, mode=machine.Timer.PERIODIC, callback=self._cardcheck)

    def _on_pin0(self, newstate):
        self._on_pin(0, newstate)
    def _on_pin1(self, newstate):
        self._on_pin(1, newstate)

    def _on_pin(self, is_one, newstate):
        now = utime.ticks_ms()
        if self.last_bit_read is not None and now - self.last_bit_read < 1:
            # too fast
            return

        self.last_bit_read = now
        self.next_card <<= 1
        if is_one: self.next_card |= 1
        self._bits += 1

    def get_card(self):
        if self.last_card is None:
            return None
        return ( self.last_card & CARD_MASK ) >> 1

    def get_facility_code(self):
        if self.last_card is None:
            return None
        # Specific to standard 26bit wiegand
        return ( self.last_card & FACILITY_MASK ) >> 17

    def _cardcheck(self, t):
        if self.last_bit_read is None: return
        now = utime.ticks_ms()
        if utime.ticks_diff(now, self.last_bit_read) > 50:
            # too slow -> new start!
            self.last_bit_read = None
            self.last_card = self.next_card
            self.next_card = 0
            self.callback(self.last_card, self._bits)
            self._bits = 0

class WeigandRFID(Parameter):
    struct = 'i' 
    
    def __init__(self, *, pin0, pin1, verify_checksum=False, **k):
        super().__init__(**k)
        self.rfid = Wiegand(pin0=pin0, pin1=pin1, callback=self.on_card)
        self.dirty = False  # flag to see if we should send
        self.v_chk = verify_checksum
        loop = asyncio.get_event_loop()
        loop.create_task(self.chk())
        
    def on_card(self, raw_id, _bits):
        # print(raw_id)
        
        if self.v_chk:
            return
        
        if _bits > 32:
            _id = (raw_id >> 1) & 4294967295  # strip checksum 
        
        elif _bits >= 26:        
            _id = (raw_id >> 1) & 16777215 # strip checksum
            
        else:
            print('TODO: update for button presses 4 and 8 bit mode')
            return 
       
        self.state = _id
        self.dirty = True
        
    async def chk(self):
        while True:
            if self.dirty:
                self.dirty = False
                self.send()                
            await asyncio.sleep_ms(50)
