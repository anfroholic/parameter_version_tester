"""
Digital Input for ESP32
"""
from floe import FP, make_var
from Parameter import Parameter
import json
    
class Inkscape(Parameter):
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
        'G21 (All units in mm)': {'cmd': 'set_units', 'data': 'mm'},
        'G00 Z5.000000': self.tool_off.state,
        'G01 Z-0.125000 F100.0(Penetrate)': self.tool_on.state   
        }
        
        
    def __call__(self, state) -> None:
        if state is not None:
            self.state = self.inkscape_compiler(state)
        self.send()

    def inkscape_compiler(self, ngc_file):
        if isinstance(ngc_file, str):
            ngc_file = ngc_file.split('\n')
        

        def parse_segment(segment) -> dict | None:
            axis = segment[0].lower()
            if axis =='z':
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
            if line[0] == 'G00':
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
            if line == 'G00 Z5.000000' and last_was_tool_off == True:
                continue
            elif line == 'G00 Z5.000000':
                last_was_tool_off = True
            elif line == '(Footer)':
                break
            
            if line in self.converts:
                if isinstance(self.converts[line], list):
                    output.extend(self.converts[line])
                else:
                    output.append(self.converts[line])
                
            elif line[:3] == 'G01' or line[:3] == 'G00':
                last_was_tool_off = False
                output.append(parse_move(line))

        print('inkscape success')
        # print(output)
        return '\n'.join(json.dumps(line) for line in output)

    