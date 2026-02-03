from floe import make_var, FP
from Parameter import Parameter

try:
    import uasyncio as asyncio
except:
    import asyncio

import utime, json, struct

# SPDX-FileCopyrightText: 2019 Mike Causer <https://github.com/mcauser>
# SPDX-License-Identifier: MIT

"""
MicroPython PCF8574 8-Bit I2C I/O Expander with Interrupt
https://github.com/mcauser/micropython-pcf8574
"""

__version__ = "1.1.0"


class PCF8574:
    def __init__(self, i2c, address=32, verified=False):
        self._i2c = i2c
        self._address = address
        self._port = bytearray(1)
        self.v = verified

    def check(self):
        if self._i2c.scan().count(self._address) == 0:
            raise OSError(f"PCF8574 not found at I2C address {self._address:#x}")
        return True

    def read_all(self) -> int:
        self._read()
        return self._port[0]

    def set_all(self, value: int) -> None:
        # print(f'setting all ports {value}')
        self._port[0] = value
        self._write()

    def pin(self, pin, value=None, read=True, write=True) -> None:
        pin = self._validate_pin(pin)
        if value is None:
            if read:
                self._read()
            return (self._port[0] >> pin) & 1
        if value:
            self._port[0] |= 1 << (pin)
        else:
            self._port[0] &= ~(1 << (pin))
        if write:
            self._write()

    def toggle(self, pin) -> None:
        pin = self._validate_pin(pin)
        self._port[0] ^= 1 << (pin)
        self._write()

    def _validate_pin(self, pin) -> int:
        # pin valid range 0..7
        if not 0 <= pin <= 7:
            raise ValueError(f"Invalid pin {pin}. Use 0-7.")
        return pin

    def _read(self) -> None:
        if self.v:
            self._i2c.readfrom_into(self._address, self._port)

    def _write(self) -> None:
        if self.v:
            self._i2c.writeto(self._address, self._port)


class Pcf8574(Parameter):    
    struct = 'B'
    def __init__(self, *, 
                 i2c,
                 address,
                 pin0,
                 pin1,
                 pin2,
                 pin3,
                 pin4,
                 pin5,
                 pin6,
                 pin7,
                 pin0_initial_state,
                 pin1_initial_state,
                 pin2_initial_state,
                 pin3_initial_state,
                 pin4_initial_state,
                 pin5_initial_state,
                 pin6_initial_state,
                 pin7_initial_state,
                 sample_rate,
                 interrupt_pin,
                 pin0_event_onchange,
                 pin1_event_onchange,
                 pin2_event_onchange,
                 pin3_event_onchange,
                 pin4_event_onchange,
                 pin5_event_onchange,
                 pin6_event_onchange,
                 pin7_event_onchange,
                 **k):
        self.io = None
        super().__init__(**k)
        
        self.i2c = make_var(i2c)
        
        self._loop = False
        self._address = address
        self.sample_rate = sample_rate
        self.interrupt_pin = interrupt_pin
        
        self._initial_state = 0
        for pin in [
            pin0_initial_state,
            pin1_initial_state,
            pin2_initial_state,
            pin3_initial_state,
            pin4_initial_state,
            pin5_initial_state,
            pin6_initial_state,
            pin7_initial_state
            ]:
            self._initial_state <<= 1
            if pin:
                self._initial_state += 1
            
        for pin in [
            pin0_event_onchange,
            pin1_event_onchange,
            pin2_event_onchange,
            pin3_event_onchange,
            pin4_event_onchange,
            pin5_event_onchange,
            pin6_event_onchange,
            pin7_event_onchange
            ]:
            
            if pin: 
                self.loop = True
        
        self.pins = [
            pin0,
            pin1,
            pin2,
            pin3,
            pin4,
            pin5,
            pin6,
            pin7,
            ]
                
        self.funcs = {
            'set_pin': self.set_pin,
            'set_all': self.set_all,
        }
        self.test = []
        
    def update(self):
        super().update()
        verified = self.i2c.verify_address(self._address) # check that device exists on bus
        
        self.io = PCF8574(self.i2c.i2c, self._address, verified)
        
        for i in range(len(self.pins)):
            if self.pins[i]:            
                # get actual pin object
                sub = self.iris.p[self.pins[i].pid]
                self.pins[i] = sub
                
                # add callbacks
                self.pins[i].add_hot(getattr(self, f'_pin{i}'))
                
                # sync pin with subscription
                self.io.pin(pin=i, value=sub.state, write=False)
                
        self.io._write()
        
        # loop = asyncio.get_event_loop()
        # self.loop = loop.create_task(self.chk())
    
    def _pin0(self, value) -> None:
        self._dopin(0, value)
        
    def _pin1(self, value) -> None:
        self._dopin(1, value)
        
    def _pin2(self, value) -> None:
        self._dopin(2, value)
        
    def _pin3(self, value) -> None:
        self._dopin(3, value)
        
    def _pin4(self, value) -> None:
        self._dopin(4, value)
    
    def _pin5(self, value) -> None:
        self._dopin(5, value)
        
    def _pin6(self, value) -> None:
        self._dopin(6, value)
    
    def _pin7(self, value) -> None:
        self._dopin(7, value)
        
    def _dopin(self, pin, value) -> None:
        self.set_pin(pin=pin, value=value)
        self.send()
    
    @property
    def state(self):
        return self.io._port[0]
    
    @state.setter
    def state(self, value):
        if self.io:
            self.io._port[0] = value
    
    def set_all(self, value: int) -> None:
        self.io.set_all(value)
        
    def read_all(self) -> int:
        return self.io.read_all()
    
    def set_pin(self, pin: int, value: bool) -> None:
        self.io.pin(pin, value)
    
    def get_pin(self, pin: int, read=True) -> bool:
        return self.io.pin(pin=pin, read=read)
    
    def state_as_list(self) -> list[bool]:
        return [(self.state >> i) & 1 == 1 for i in range(8)]            
    
    def __call__(self, state, gui=False):
        # example: {'cmd': function, 'data': argument} 
        if isinstance(state, bytes):
            state = state.decode('utf-8')
        if isinstance(state, str):
            state = json.loads(state)
        cmd = state.pop('cmd')
        if state != {}:
            self.funcs[cmd](state)
        else:
            self.funcs[cmd]()
        self.send()

