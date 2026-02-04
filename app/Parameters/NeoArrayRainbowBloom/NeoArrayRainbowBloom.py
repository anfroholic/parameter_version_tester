"""
Neopixel Rainbow Animation
"""
import math
from NeoArray import NeoArray
from floe import make_var, FP

class NeoArrayRainbowBloom:
    """ rainbow animation for Neo
    """
    rbow = tuple([int((math.sin(math.pi / 18 * i) * 127 + 128) / 10) for i in range(36)])
    
    def __init__(self, *, pid, step=6, spin: bool, invert, invert_spin, iris, **k):
        self.pid = int(pid)
        iris.p[pid] = self
        self.iris = iris
        self.step = make_var(step)
        self.invert = make_var(invert)
        self.spin = make_var(spin)
        self.invert_spin = make_var(invert_spin)
        
    
    def __call__(self, *args, **kwargs):
        pass
    
    def animate(self, array: NeoArray, index):
        color = [(index + num*self.step.state)%36 for num in range(array.num_pix)]
        # color = strip_indexes if not self.invert.state else reversed(strip_indexes)

        for strip_offset, neo in enumerate(array.neos if not self.invert_spin.state else reversed(array.neos)):
            for pixel in range(array.num_pix):
                offset = 0 if not self.spin.state else strip_offset * self.step.state
                _color = color[pixel] if not self.invert.state else color[-pixel]  # rainbow in strip
                
                neo[pixel] = (
                    self.rbow[(_color + offset)%36],
                    self.rbow[(_color + offset + 12)%36],
                    self.rbow[(_color + + offset + 24)%36])
                neo.write()    
        
    def update(self):
        for attr, val in self.__dict__.items():            
            if isinstance(val, FP):
                setattr(self, attr, self.iris.p[val.pid])
                
    def gui(self):
        pass

    