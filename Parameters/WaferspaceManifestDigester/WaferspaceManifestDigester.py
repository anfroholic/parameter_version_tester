import json
from collections import defaultdict


from Parameter import Parameter
from floe import make_var
import json


def load_slot_map(MANIFEST):
    """Return dict: CODE -> SLOT_SIZE"""
    slot_map = {}
    
    lines = MANIFEST.split("\n")
    headers = lines[0].split(",")
    for line in lines[1:]:
        if not line:
            continue
        values = line.split(",")
        row = dict(zip(headers, values))
        code = row["CODE"]
        slot_map[code] = {"SLOT_SIZE": row["SLOT_SIZE"], "PROJECT": row["PROJECT"]}
    return slot_map


def load_grid(TILEMAP):
    """Return grid as list[list[str]]"""
    return [line.strip().split(",") for line in TILEMAP.split("\n") if line.strip()]


def build_layout(grid, slot_map):
    """Return layout as list[list[str]] with SLOT_SIZE values"""
    layout = []
    visited = set()
    tall = False
    for row in grid:
        if tall:
            tall = False
            continue
        layout_row = []
        double_wide = False
        for code in row:
            if double_wide:
                double_wide = False
                continue
            slot_size = slot_map.get(code, "UNKNOWN")["SLOT_SIZE"]
            if slot_size[0] == "1":
                double_wide = True
            data = dict(
                code=code, 
                slot_size=slot_size,
                project=slot_map.get(code, "UNKNOWN")["PROJECT"]
            )
            layout_row.append(data)
            if slot_size[-1] == "1":
                tall = True
        layout.append(layout_row)
    return layout

def rename_duplicates(layout):
    """Rename duplicate codes in layout by appending _1, _2, etc."""
    code_count = defaultdict(int)
    for row in layout:
        for slot in row:
            code = slot['code']
            code_count[code] += 1

    code_index = defaultdict(int)
    for row in layout:
        for slot in row:
            code = slot['code']
            if code_count[code] > 1:
                code_index[code] += 1
                slot['code'] = f"{code}_{code_index[code]}"
    return layout

class WaferspaceManifestDigester(Parameter):
    struct = 'H'  # unint16
    
    def __init__(self, manifest, tilemap, **k):
        super().__init__(**k)
        self.manifest = make_var(manifest)
        self.tilemap = make_var(tilemap)

    def __call__(self, order: dict, **k):
        print(order)
        if isinstance(order, str):   
            order = json.loads(order)
        if order['cmd'] == 'generate':
            self.generate()

    def generate(self):
        # Placeholder for generate logic
        print("Generating waferspace manifest...")

        slot_map = load_slot_map(self.manifest.state)
        grid = load_grid(self.tilemap.state)
        layout = build_layout(grid, slot_map)

        layout = rename_duplicates(layout)
        
        self.state = layout
        self.send()
        cmd = {
            "cmd": "update_layout",
            "layout": layout
        }
        self.iris.bifrost.send(self.pid, cmd)
        print("Generation complete.")
    
    def gui(self):
        return {"name": self.name, "pid": self.pid, "state": self.state, "type": "WaferspaceManifestDigester"}
    