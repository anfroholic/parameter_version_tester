"""

"""
from floe import FP, make_var
from Parameter import Parameter
import json, gc
    
class MakelangeloCompiler(Parameter):
    struct = 'str'  # bool
    
    def __init__(self, *, tool_on, tool_off, **k):
        super().__init__(**k)
        self.tool_on = make_var(tool_on)
        self.tool_off = make_var(tool_off)
        self.feedrate_override = 1400
        self.converts = {}


    def update(self):
        super().update()
        if not self.tool_on.state:
            self.tool_on.state = {'cmd': 'tool.on'}
        if not self.tool_off.state:
            self.tool_off.state = {'cmd': 'tool.off'}
        
        self.converts = {
        'M280 P0 S90 T250': self.tool_off.state,
        'M280 P0 S25 T150': self.tool_on.state   
        }
        
        
    def __call__(self, state) -> None:
        if state is not None:
            self.state = self.makelangelo_compiler(state)
        self.send()


    def makelangelo_compiler(self, ngc_file):
        if isinstance(ngc_file, str):
            ngc_file = ngc_file.split('\n')
        

        def parse_segment(segment) -> dict | None:
            axis = segment[0].lower()
            if axis == 'z':
                return None
            if axis == 'f':
                axis = 'feed'
                if self.feedrate_override:
                    return {axis: self.feedrate_override}
            value = round(float(segment[1:]), 3)
            return {axis: value}
        
        def parse_move(line) -> dict:
            line = line.strip()
            line = line.split(' ')
            if line[0] == 'G0':
                cmd = {'cmd': 'move.rapid'}
            else:
                cmd = {'cmd': 'move.linear'}
            
            for segment in line[1:]:
                seg = parse_segment(segment)
                if seg is not None:
                    cmd.update(seg)
            return cmd

        # parse the file
        output = []
        last_was_tool_off = False
        for line in ngc_file:
            line = line.strip()
            if line == 'M280 P0 S90 T250' and last_was_tool_off == True:
                continue
            elif line == 'M280 P0 S90 T250':
                last_was_tool_off = True
            elif line == ';End of Gcode':
                break
            
            if line in self.converts:
                if isinstance(self.converts[line], list):
                    output.extend(self.converts[line])
                else:
                    output.append(self.converts[line])
                
            elif line[:2] == 'G1' or line[:2] == 'G0':
                last_was_tool_off = False
                output.append(parse_move(line))

        return '\n'.join(json.dumps(line) for line in output)


    
    