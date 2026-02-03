# fake neopixel module for pyscripts

class NeoPixel:
    def __init__(self, pin, numpix):
        self.array = [(0,0,0)]*numpix
        
    def write(self):
        pass
    def __getitem__(self, index):
        return self.array[index]
    def __setitem__(self, index, val):
        self.array[index] = val