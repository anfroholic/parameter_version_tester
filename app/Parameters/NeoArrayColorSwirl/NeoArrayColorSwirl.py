"""
Neopixel Rainbow Animation
"""

from NeoArray import NeoArray
from floe import make_var, FP

class NeoArrayColorSwirl:
    """ color swirl for NeoArray """
    
    def __init__(self, *, pid, invert=False, colors=None, iris, **k):
        self.pid = pid
        self.iris = iris
        iris.p[pid] = self
        self.invert = make_var(invert)
        if colors == None:
            self.colors = ((6,0,0),(3,3,0),(0,6,0),(0,3,3),(0,0,6),(3,0,3))
        else:
            self.colors = colors
        
    def __call__(self, *args, **kwargs):
        pass
    
    def animate(self, array: NeoArray, index):
        if not self.invert.state:
            for i, neo in enumerate(array.neos):
                array.fill_strip(neo, self.colors[(i + index) % len(self.colors)])
        else:
            for i, neo in enumerate(reversed(array.neos)):
                array.fill_strip(neo, self.colors[(i + index) % len(self.colors)])
       
    def update(self):
        if isinstance(self.invert, FP):
            self.invert = self.iris.p[self.invert.pid]

    def gui(self):
        pass
    