from floe import FP, make_var
from Parameter import Parameter
import json
from GRBL import GRBL, move
    
Ref = 0
Val = 1
Package = 2
PosX = 3
PosY = 4
Rot = 5
Side = 6

class KiCad(Parameter):
    """
    A Parameter subclass that converts KiCad PCB placement data
    into GRBL motion instructions for a pick-and-place system.

    This class parses component placement lines, matches them against
    configured feeders, and generates sequences of moves for picking
    and placing parts. It integrates with the `iris` messaging system
    for coordination and logging.

    Public API:
        - __init__: Configure feeders, offsets, and motion controller
        - update: Refresh references to other parameters
        - __call__: Process placement data and send results
        - gen: Generate motion command sequences
    """
    
    struct = 'str'  # bool
    
    def __init__(self, *, feeders, iris, board_offset = None, grbl=None, **k):
        super().__init__(iris=iris, **k)
        self.feeders = make_var(feeders)        
        self.work_offset = {}
        
        self.z_clear = 0
        
        if grbl is None:
            self.grbl = GRBL(iris=iris)
        self.board_offset = make_var(board_offset)
        self.skipped = set()
        self.count = 0
        
        
    def update(self):
        super().update()
        # if self.board_offset:
        #     self.grbl.set_work_offset('board_offset', self.board_offset.state)
        
    def __call__(self, state) -> None:
        """
        Process placement data and convert it into motion instructions.

        Args:
            state (str | Parameter): Placement data, typically as a
                newline-separated CSV/JSON-lines string.

        Side Effects:
            - Updates `self.state` with a string of motion commands.
            - Calls `.send()` to broadcast results.
        """
        
        if state is not None:
            l = (json.dumps(line) for line in self.gen(state))
            self.state = '\n'.join(l)
        self.send()
        
    def _create_gen(self, string, jsonlines=True, filename=False):
        # we have gotten a string that composed like JSON lines
        def _open(filename):
            with open(string, 'r') as f:
                for line in f:
                    yield line
        
        

        def kicad_gen(iterable):
            self.count = 0
            self.skipped = set()
            yield dict(cmd='move', z=self.z_clear, f=2500)
            parts = self._get_next_pickable_part(iterable)
            this_part = next(parts)
            yield from self.feed_part(this_part)  # feed the first part
            yield {'cmd': 'sleep', 'seconds': 3}
            for next_part in parts:
                # print(next_part)
                yield from self._do_pick_place(this_part, next_part)
                this_part = next_part.copy()
            yield from self._do_pick_place(this_part, None)  # do the last part
            self.iris.bifrost.post(f"{self.count} components placed")
            self.iris.bifrost.post(f"skipped components: {self.skipped}")
        
        if jsonlines and not filename: 
            string = string.split('\n')  # create iterable
            g = kicad_gen(string)
            # next(g) # move past first line of csv
            return g
        elif filename:
            g = kicad_gen(_open(string))
            return g  
    
    def _get_next_pickable_part(self, iterable):
        for line in iterable:
            line = self._get_valid_line(line)
            if line:
                if line[Val] == 'Val':
                    continue
                
                elif line[Val] in self.feeders.state and line[Val] != 'Val':
                    self.count += 1
                    yield line
                
                else:
                    self.iris.bifrost.post(f'skipping: {line[Ref]}, {line[Val]}') 
                    self.skipped.add(line[Val])

    def gen(self, *object, filename:str=""):
        """
        Generate motion command sequences from placement data.

        Args:
            *object (Parameter | str, optional):
                - If a Parameter, uses its `.state`.
                - If a string, treats it as raw placement data.
            filename (str, default=""):
                If there is no object and filename is populated it will open that file

        Yields:
            dict: Motion command dictionaries (e.g., {"cmd": "move", "x": 10}).

        Example:
            >>> for cmd in kicad.gen(placement_data):
            ...     print(cmd)
            
            or if we have a grbl object:
            >>> grbl.run(kicad.gen(filename='file.csv'))
        """

        if object:
            object = object[0]
            if isinstance(object, Parameter):
                return self._create_gen(object.state)
                
            elif isinstance(object, str) and not filename:
                print('got string')
                return self._create_gen(object)
        
        if filename:
            name = filename
            return self._create_gen(name, filename=True)        
        
        
    def _get_valid_line(self, line) -> list[str]:
        line = line.replace('"', "")
        if line:
            line = line.split(',')
            return line

    def feed_part(self, line): 
        yield dict(cmd='eval', eval=f'GuiPnpFeeder({self.feeders.state[line[Val]]["id"]})', comment=line[Val], count=self.count)
        
    def _do_pick_place(self, this_line, next_line=None):
        yield from self._pick(this_line)
        if next_line:
            yield from self.feed_part(next_line)
        yield from self._place(this_line)

    def _pick(self, component):
        yield {'cmd': 'comment', 'data': f"picking: {component[Ref]}, {component[Val]}"}
        self.work_offset = {}
        comp = self.feeders.state[component[Val]]
        yield dict(cmd='move', x=comp['x'], y=comp['y'], a=comp['a'], f=10000)
        yield {'cmd': 'sleep', 'seconds': .1}
        yield dict(cmd='move', z=comp['z'], f=4500)
        yield {'cmd': 'eval', 'eval': 'suck(True)'}
        yield {'cmd': 'sleep', 'seconds': .5}
        yield dict(cmd='move', z=self.z_clear, f=12500)

    def _place(self, component):        
        pos = dict(cmd='move', x=float(component[PosX]), y=float(component[PosY]), a=float(component[Rot]), f=10000)
        yield self._apply_offset(pos)
        thickness = self.feeders.state[component[Val]]['t']
        yield dict(cmd='move', z=self.work_offset['z']+thickness, f=4500)
        yield {'cmd': 'eval', 'eval': 'suck(False)'}
        yield {'cmd': 'sleep', 'seconds': .75}
        # yield dict(cmd='set_work_offset', offset='clear_offsets')
        yield dict(cmd='move', z=self.z_clear, f=12500, comment='part placed moving z')

    def _apply_offset(self, pos):  # TODO: change this out for CNCTranslator object
        self.work_offset = self.board_offset.state
        for axis, val in self.work_offset.items():
            if axis in pos:
                pos[axis] += val
        return pos
    