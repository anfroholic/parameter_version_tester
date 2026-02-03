# KiCad

The **`KiCad`** class converts **KiCad PCB placement files** into **pick-and-place machine commands**.  

It connects component name values (like `10k`, `.1uF`, etc.) to feeder definitions, applies a board offset, and generates GRBL commands for picking and placing parts.

---
### Input
str: formatted as csv file

file like object: formatted as csv file

### Output
json lines

---

## Processing Placement Data

```python
placement_data = """ 
Ref,Val,Package,PosX,PosY,Rot,Side
"R101","10k","R_0603_1608Metric",11.200,-51.434,90.000,top
"C101","22uF","C_0805_2012Metric",5.240,-74.674,-90.000,top
"""

# Generate and send commands
kicad(placement_data)
```

---

## Iterating Commands

You can also directly **iterate through commands** without sending them:

```python
# testing
for cmd in kicad.gen(placement_data):
    print(cmd)

# for use with GRBL
grbl.run(kicad.gen(filename='csvfile.csv'))
```

Example output:

```python
# order: move command
{'cmd': 'move', 'x': 10, 'y': 20, 'z': -5, 'a': 0, 'f': 5000}
# order: turn on suction
{"cmd": "eval", "eval": "suck(True)"}
# order: feed feeder (index 4)
{"cmd": "eval", "eval": "GuiPnpFeeder(4)", "comment": "feed: 22uF"}
```


