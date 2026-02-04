from floe import FP, make_var
from Parameter import Parameter
from I2C import I2C
import os
import utime

esp32 = False
try:
    import uasyncio as asyncio
    esp32 = True
except:
    import asyncio

class AS5048BEncoder(Parameter):
    struct = 'f'
    """
    AS5048B magnetic encoder
    https://ams.com/documents/20143/36005/AS5048_DS000298_4-00.pdf
    """
    resolution = 16384  # 14 bits
    half = int(16384 / 2)
    angle_register = int(0xFE)
    auto_gain_control_reg = int(0xFA)
    diagnostics_reg = int(0xFB)
    zero_reg = int(0x16)

    def __init__(self, *, address: int, invert: bool, offset: int, i2c: FP, **k):
        super().__init__(**k)
        self.address = address
        self.ring_size = 3
        self.ring = [0] * self.ring_size
        self._index = 0
        self.invert = invert
        self.offset = offset
        self.i2c: I2C = i2c
        self.offset_dif = 0  # this is for dealing with low side overflow
        
    def update(self):
        self.i2c = self.iris.p[self.i2c.pid]
        save_data = self._load_save_data()
        print('loading data', save_data)
        if save_data:
            self.offset = save_data['offset']
            self.invert = save_data['invert']
        self.offset_dif = self.resolution - self.offset
        
        if esp32 and self.active:
            if self.i2c.verify_address(self.address):    
                self.i2c = self.i2c.i2c
                loop = asyncio.get_event_loop()
                loop.create_task(self.chk())    

    async def chk(self) -> None:
        while True:    
            high, low = list(self.i2c.readfrom_mem(self.address, self.angle_register, 2))  # read from device
            self._index = (self._index + 1) % self.ring_size  # count around ring averager

            raw_ang = (high << 6) + low
            ang = raw_ang - self.offset
            if ang < -self.half:  # check for low side overflow
                ang = -raw_ang - self.offset_dif
            elif ang > self.half:
                ang = ang - self.resolution
            self.ring[self._index] = ang  # add new value to ring
            
            if self._index == 0:
                self.__call__(self.angle)
                # print(f"angle: {self.angle}, raw: {self.raw}")
            await asyncio.sleep_ms(100)

    def _raw(self) -> int:
        if self.invert:
            return -int(sum(self.ring) / self.ring_size)  # average ring buffer and invert
        return int(sum(self.ring) / self.ring_size)

    @property
    def raw(self) -> int:
        high, low = list(self.i2c.readfrom_mem(self.address, self.angle_register, 2))  # read from device
        ang = (high << 6) + low
        return ang
        
    
    @property
    def angle(self) -> float:
        return self._raw() / self.resolution * 360.0

    def get_gain(self):
        """ 255 is low field 0 is high field """
        return self.i2c.readfrom_mem(self.address, self.auto_gain_control_reg, 1)[0]

    def get_diag(self) -> dict[str, bool]:
        raw = self.i2c.readfrom_mem(self.address, self.diagnostics_reg, 1)[0]
        return {'mag too low': bool(raw & 8),
                'mag too high': bool(raw & 4),
                'CORDIC Overflow': bool(raw & 2),
                'Offset Compensation finished': bool(raw & 1)
                }

    def save(self):
        data = {
            'offset': self.offset,
            'invert': self.invert,
        }
        self._save(data)
        
    def set_zero(self):
        self.offset = self.raw
        self.offset_dif = self.resolution - self.offset
        self.save()
                
        # pos = self.i2c.readfrom_mem(self.address, self.angle_register, 2)
        # utime.sleep_ms(10)
        # self.i2c.writeto_mem(self.address, self.zero_reg, pos)




