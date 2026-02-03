"""
Cnc Translator
"""
from floe import FP, make_var
from Parameter import Parameter
import math, json

class CncTranslator(Parameter):
    struct = 'string'  # bool
    
    def __init__(self, *, x_offset, y_offset, rotate, initial_x, initial_y, **k):
        super().__init__(**k)
        self.x_offset = make_var(x_offset)
        self.y_offset = make_var(y_offset)
        self.rotate = make_var(rotate)
        self.initial_x = make_var(initial_x)
        self.initial_y = make_var(initial_y)
        self.pos = {}
        
    def update(self):
        super().update()
        print('the translator is updating')
        print(self.rotate)
        self.rotate.add_hot(self.make_radians)
        self.make_radians(self.rotate.state)
        
        
        self.pos = {
            'x': self.initial_x.state,
            'y': self.initial_y.state
            }
        
    def make_radians(self, degrees):
        self.rotate = math.radians(degrees)
        
    def __call__(self, state) -> None:
        if state is not None:
            self.state = self.translate(state)
        self.send()
        
    def rotate_xy(self, x, y) -> tuple[float, float]:
        hyp = (x**2 + y**2) ** .5 # math.hypot(x, y)
        hyp_angle = math.atan2(y, x)
        new_hyp_angle = hyp_angle + self.rotate
        return math.cos(new_hyp_angle) * hyp, math.sin(new_hyp_angle) * hyp

    def translate(self, code:str):
        if isinstance(code, str):
            code = code.split('\n')

        output = []
        for line in code:
            if isinstance(line, str):
                line = json.loads(line)
            if line['cmd'] not in ['move.linear', 'move.rapid']:
                # not a move command, just return
                output.append(line)
                continue
            if 'x' not in line and 'y' not in line:
                # must be z only move
                output.append(line)
                continue
            
            for axis in ['x', 'y']:
                if axis in line:
                    self.pos[axis] = line[axis]
                
            x, y = self.rotate_xy(self.pos['x'], self.pos['y'])
            line['x'] = round(x + self.x_offset.state, 3)
            line['y'] = round(y + self.y_offset.state, 3)
            
            output.append(line)
            
        output = [json.dumps(line) for line in output]
        return '\n'.join(output)
    