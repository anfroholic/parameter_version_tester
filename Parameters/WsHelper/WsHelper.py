import math, json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle


from Parameter import Parameter
from floe import make_var
import json


# --- New Die Slicing Scheme ---
# Units are in mm. columns correspond to die widths, rows to die heights.
DIE_WIDTHS: list[float] = [3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 3.88, 1.88, 1.88]
DIE_HEIGHTS: list[float] = list(reversed([1.88, 2.535, 5.070, 5.070, 5.070, 5.070]))
KERF: float = 0.024 # Saw kerf in mm
WAFER_SIZE: float = 200 # Wafer size in mm
EXLUSION_ZONE: float = 3.0 # Exclusion zone from wafer edge in mm

IGNORE_FIRST_DIE_COL = False
IGNORE_LAST_DIE_COL = True
IGNORE_FIRST_DIE_ROW = False
IGNORE_LAST_DIE_ROW = True

def die_yield_advanced(
    die_widths: list[float],
    die_heights: list[float],
    kerf: float,
    wafer_size: float = 200,
    exclusion_zone: float = 3.0,
    plot: bool = False,
    heatmap: bool = False,
    filename: str = None
) -> tuple[int, list[tuple[float, float, str]], np.ndarray]:
    """
    Compute usable die yield with unique shot (reticle) identifiers and SVG output.
    
    Returns:
        total_dies: Total count
        die_data: list of (x_center, y_center, full_label)
        reticle_yield_counts: 2D array of yield per reticle position
    """
    
    wafer_r = wafer_size / 2.0 - exclusion_zone
    reticle_cols = len(die_widths)
    reticle_rows = len(die_heights)

    px_list = [dw + kerf for dw in die_widths]
    py_list = [dh + kerf for dh in die_heights]
    
    ret_w = sum(px_list) - kerf
    ret_h = sum(py_list) - kerf

    n_rx = int(math.ceil((wafer_r + ret_w/2) / ret_w))
    n_ry = int(math.ceil((wafer_r + ret_h/2) / ret_h))

    die_data = [] 
    reticle_yield_counts = np.zeros((reticle_rows, reticle_cols), dtype=int)
    total_dies = 0
    reticle_boundaries = []

    # Iterate through reticle grid
    for ix in range(-n_rx, n_rx):
        for iy in range(-n_ry, n_ry):
            ox = ix * ret_w
            oy = iy * ret_h
            reticle_boundaries.append((ox, oy))
            
            # Shot ID based on grid position
            shot_id = f"S{ix}_{iy}"

            for c in range(reticle_cols):
                x_start_rel = sum(px_list[:c])
                die_w = die_widths[c]
                hx = die_w / 2.0
                
                for r in range(reticle_rows):
                    y_start_rel = sum(py_list[:r])
                    die_h = die_heights[r]
                    hy = die_h / 2.0

                    cx, cy = ox + x_start_rel + hx, oy + y_start_rel + hy
                    
                    corners = [
                        (cx - hx, cy - hy), (cx + hx, cy - hy),
                        (cx + hx, cy + hy), (cx - hx, cy + hy)
                    ]
                    
                    if all(x*x + y*y <= wafer_r**2 for x, y in corners):
                        # Combined Label: Shot ID + Die Position
                        full_label = f"{shot_id},C{c}R{r}"
                        if c == 0 and IGNORE_FIRST_DIE_COL:
                            continue
                        if c == reticle_cols-1 and IGNORE_LAST_DIE_COL:
                            continue
                        if r == 0 and IGNORE_FIRST_DIE_ROW:
                            continue
                        if r == reticle_rows-1 and IGNORE_LAST_DIE_ROW:
                            continue
                        die_data.append((cx, cy, full_label))
                        total_dies += 1
                        reticle_yield_counts[r, c] += 1

    if plot or filename:
        fig, ax = plt.subplots(figsize=(14, 14))
        wafer = Circle((0,0), wafer_size / 2.0, edgecolor='black', facecolor='none', lw=2)
        ax.add_patch(wafer)

        # Plot usable dies
        for cx, cy, label in die_data:
            # Parse label to get dimensions for drawing
            # Label format: "S[ix,iy]-CcRr"
            pos_part = label.split(',')[1]
            c_idx = int(pos_part.split('R')[0][1:])
            r_idx = int(pos_part.split('R')[1])
            w, h = die_widths[c_idx], die_heights[r_idx]
            
            # Use a consistent color based on die position (column, row)
            color_idx = (c_idx * len(die_heights) + r_idx) % 10
            colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
            rect = Rectangle((cx - w/2, cy - h/2), w, h, edgecolor='black', facecolor=colors[color_idx], lw=0.4, alpha=.5)
            
            # if not (c_idx == reticle_cols-1 or r_idx == reticle_rows-1):
            ax.add_patch(rect)
            
            # Red dot at center
            ax.plot(cx, cy, 'ro', markersize=1.5)
            
            # Label text
            ax.text(cx, cy, label, fontsize=2.5, ha='center', va='center', color='darkgreen', rotation=45)

        # Plot reticle boundaries
        for ox, oy in reticle_boundaries:
            rect = Rectangle((ox, oy), ret_w, ret_h, edgecolor='blue', facecolor='none', lw=0.8, linestyle='--', alpha=0.4)
            ax.add_patch(rect)

        ax.set_aspect('equal')
        ax.set_xlim(-wafer_r-10, wafer_r+10)
        ax.set_ylim(-wafer_r-10, wafer_r+10)
        ax.set_title(f"Wafer Map: {total_dies} usable dies\nLabel Format: ShotID-ColumnRow")
        
        
        if plot:
            if filename:
                plt.savefig(f"{filename}.svg", format='svg', bbox_inches='tight')
        
            # plt.show()
        else:
            plt.close()
            
    # Reticle yield heatmap
    if heatmap and plot:
        fig, ax = plt.subplots(figsize=(6,5))
        im = ax.imshow(reticle_yield_counts, cmap="viridis", origin="lower")
        for r in range(reticle_yield_counts.shape[0]):
            for c in range(reticle_yield_counts.shape[1]):
                ax.text(c, r, str(reticle_yield_counts[r,c]), ha="center", va="center", color='white', fontsize=8)
        ax.set_title("Reticle Position Yield (usable dies)")
        ax.set_xlabel("Column index")
        ax.set_ylabel("Row index")
        fig.colorbar(im, ax=ax, label="Usable dies")
        
       
        plt.savefig(f"{filename}_heatmap.svg", format='svg', bbox_inches='tight')
        
        # plt.show()
        
        
    with open(f"{filename}.csv", 'w') as f:
        # save CSV file for pnp
        f.write("X,Y,RETICLE_SHOT,COL|ROW\n")
        for die in die_data:
            f.write(f"{round(die[0], 3)},{round(die[1], 3)},{die[2]}\n")
            
    return total_dies, die_data, reticle_yield_counts

class WsHelper(Parameter):
    struct = 'H'  # unint16
    
    def __init__(self, **k):
        super().__init__(**k)
    
    def __call__(self, state, **k):
        print(state)
        if isinstance(state, str):
            state = json.loads(state)
        if state['cmd'] == "plot_wafer":
            self.compute_die_yield(
                plot=True,
                heatmap=True,
            )

    def compute_die_yield(self, plot: bool = True, heatmap: bool = True, filename: str = "waferspace_run1"):
        total_dies, die_data, reticle_yield_counts = die_yield_advanced(
            die_widths=DIE_WIDTHS,
            die_heights=DIE_HEIGHTS,
            kerf=KERF,
            wafer_size=WAFER_SIZE,
            exclusion_zone=EXLUSION_ZONE,
            plot=plot,
            heatmap=heatmap,
            filename=filename
        )
        with open(f"{filename}.svg", 'r') as f:
            svg_die = f.read()
        cmd = {"cmd": "die", "data": svg_die}
        self.iris.bifrost.send(self.pid, cmd)

        with open(f"{filename}_heatmap.svg", 'r') as f:
            svg_heatmap = f.read()
        cmd = {"cmd": "heatmap", "data": svg_heatmap}
        self.iris.bifrost.send(self.pid, cmd)

        with open(f"{filename}.csv", 'r') as f:
            csv_data = f.read()
        self.state = csv_data
        self.send()
        
        return total_dies, die_data, reticle_yield_counts
    
    def gui(self):
        return {"name": self.name, "pid": self.pid, "state": self.state, "type": "WsHelper"}
    