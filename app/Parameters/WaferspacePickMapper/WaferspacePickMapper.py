import json

from Parameter import Parameter
from floe import make_var
import json


class WaferspacePickMapper(Parameter):
    struct = 'str'  
    
    def __init__(self, reticle_layout, wafer_map, **k):
        super().__init__(**k)
        self.projects: dict[str, list[float, float, str]] = {}
        # list[list[dict]]
        # [{'code': 'JKU2', 'project': 'gf180mcu-jku-atbs-adc', 'slot_size': '1x0p5'}, ...], ...]
        self.reticle_layout = make_var(reticle_layout)    
        # CSV
        # X,Y,RETICLE_SHOT,COL|ROW
        # -94.276,-12.092,S-4_-1,C8R2
        self.wafer_map = make_var(wafer_map)
        self.state = ""
        self.project_size_map = None

    def __call__(self, order: dict, **k):
        print(order)
        if isinstance(order, str):   
            order = json.loads(order)
        if order['cmd'] == 'generate':
            self.generate()
        elif order['cmd'] == 'send_all':
            self.state = "\n".join(json.dumps(cmd) for cmd in self.create_picklist_by_size())
            self.send()
        elif order['cmd'] == 'do_project':
            self.state = "\n".join(json.dumps(cmd) for cmd in self.create_picklist_by_project(order['project']))
            self.send()
        elif order['cmd'] == 'do_reticle':
            dies = self.group_codes_by_reticle().get(order['reticle'], [])
            cmds = []
            for die in dies:
                project = die[0]
                x = round(float(die[1]), 3)
                y = round(float(die[2]), 3)
                cmds.append(dict(cmd='do_die', location=[x,y], project=project))
            self.state = "\n".join(json.dumps(cmd) for cmd in cmds)
            self.send()


    def add_die_to_projects(self, project_code: str, x, y, reticle):
        if project_code not in self.projects:
            self.projects[project_code] = []
        self.projects[project_code].append([x, y, reticle])
        
    def get_reticle_shot(self, reticle) -> tuple[int, int]:
        # S-4_-1
        x, y = reticle.split('_')
        return (int(x[1:]), int(y))
    
    def get_project_code(self, row_col: str) -> str:
        # C8R2
        col = int(row_col[1:2])
        row = int(row_col[-1])
        return self.reticle_layout.state[row][col]['code']

    def group_codes_by_size(self) -> dict[str, list[str]]:
        size_map = {}
        for row in self.reticle_layout.state:
            for entry in row:
                size = entry['slot_size']
                if size not in size_map:
                    size_map[size] = []
                project_code = entry['code']
                if project_code not in size_map[size]:
                    size_map[size].append(project_code)
        return size_map

    def group_codes_by_reticle(self) -> dict[str, list[str]]:
        reticle_map = {}
        for project, dies in self.projects.items():
            for die in dies:
                reticle = die[2]
                if reticle not in reticle_map:
                    reticle_map[reticle] = []
                reticle_map[reticle].append([project, die[0], die[1]])
        return reticle_map
    
    def create_picklist_by_project(self, project):
        yield dict(cmd='start_project', alert=f'starting project: {project}')
        # yield dict(cmd='do_dies', dies=self.projects[project])
        for die in self.projects[project]:
            x = round(float(die[0]), 3)
            y = round(float(die[1]), 3)
            yield dict(cmd='do_die', location=[x,y])
    
    def create_picklist_by_size(self):
        yield dict(cmd='alert', alert='starting wafermap')
        for size, projects in  self.project_size_map.items():
            yield dict(cmd='start size', size=size)
            for project in projects:
                yield from self.create_picklist_by_project(project)
        
    
    def generate(self):     
        self.project_size_map = self.group_codes_by_size()
          
        wafer_map_lines = self.wafer_map.state.splitlines()
        header = wafer_map_lines[0]
        assert header == "X,Y,RETICLE_SHOT,COL|ROW"
        
        for line in wafer_map_lines[1:]:
            x, y, reticle_shot, col_row = line.split(',')
            project_code = self.get_project_code(col_row)
            reticle = reticle_shot[1:]  # S-4_-1 -> -4_-1
            self.add_die_to_projects(project_code, x, y, reticle)
        
        self.state = "\n".join(json.dumps(cmd) for cmd in self.create_picklist_by_size())
        self.iris.bifrost.send(self.pid, {"cmd": "wafermap", "projects": self.group_codes_by_size(), "reticles": list(self.group_codes_by_reticle().keys())})  
        self.send()
        
    def gui(self):
        return {"name": self.name, "pid": self.pid, "state": self.state, "type": "WaferspacePickMapper"}