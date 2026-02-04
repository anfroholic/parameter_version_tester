
# `GRBL` Parameter Documentation

## Overview

The `GRBL` parameter is a high-level Python interface for controlling GRBL-based CNC machines. It handles serial communication, motion planning, homing, tool/work offset management, and integration with a scripting engine (`Gene`) and communication layer (`Iris`).

---


## Attributes

- `axes`: Ordered mapping of GRBL standard axis labels (`x, y, z, a, b, c`) to axis objects.
- `positions`: Current machine positions.
- `work_offsets`: Named offsets relative to machine coordinates.
- `tool_offsets`: Named offsets for tools.
- `buffer`: Handles sending G-code with GRBL’s serial planner limitations.
- `state`: Machine state (`idle`, `alarm`, etc.).
- `funcs`: Command dictionary for remote invocation (RPC-style).
- `scripts`: Named Gene scripts.
- `bifrost`: Boolean or messaging interface for web integration.

---

## Public Methods

### Motion Control

#### `move(*, x, y, z, a, b, c, f)`
Creates and executes a move command.

examples:
```python
grbl.move(x=10, f=1000)  # G1 X10 F1000 equivalent
grbl.move(x=-10, y=25)  # G1 X-10 Y25 equivalent
```

---

#### `home(axis)`
Homes a single axis. 

Example:
```python
grbl.home('x')  # homes x axis
grbl.home('y')  # homes y axis
```

---

#### `get_pos(*, kinematics='cartesian') -> dict`
Returns current machine coordinates for each axis.

If other kinematics from child classes are available they may be requested

These positions are the ones from the grbl machine.

---

#### `run(script)`

Runs a script or named script via the Gene engine.

    Args: script (str | list | dict): The script to load and run.

---

#### `jog_button(order)`
Jog one axis incrementally:

(Not yet Implemented)
```python
{
  "val": 1.0,
  "dir": true,
  "axis": "x"
}
```

---
### Work Offsets 

#### `set_work_offset(name: str, vals: dict[str:float])`
Defines a new work offset configuration.

Example:
```python
grbl.set_work_offset(
      'this offset',
      {'x': 0, 'y': 0, 'x': 0, 'a': 0, 'b': 0, 'c': 0}  # only use available axes
      )
```
---


#### `change_work_offset(name: str)`
Switches to a different work offset.

Example:
```python
grbl.change_work_offset('machine')  # changes work offset to default 'machine'
```

---
### Tool Offsets

#### `set_tool_offset(name: str, vals: dict[str:float])`
Defines a new tool offset configuration.
grbl.set_work_offset(
      'this offset',
      {'x': 0, 'y': 0, 'x': 0, 'a': 0, 'b': 0, 'c': 0}  # only use available axes
      )
---

#### `change_tool_offset(name: str)`
Switches to a different tool offset.

Example:
```python
grbl.change_tool_offset('default')  # changes tool offset to default tool
```
---

#### `feed_hold()`
Pauses the CNC movement using GRBL feed hold.

Example:
```python
grbl.feed_hold()
```

---

#### `resume()`
Resumes movement after a feed hold.

Example:
```python
grbl.resume()
```
---

#### `machine(raw_cmd: dict)`
Send GRBL setup parameters directly. 

Example:
```python
{
  "cmd": "machine",
  "action": "set", # "get" will send grbl value to gui
  "command": "$/axes/x/acceleration_mm_per_sec2", 
  "value": 250.0
}
```

---

#### `jog(axis, dir)`
Sends a jog command to an axis (not yet implemented).

---

#### `send_g(cmd)`
Send a G-code or GRBL command via the buffered UART.

---

#### `send_bf(msg: str, post=False)`
Send a message to the web dashboard via Bifrost.

Example:
```python
grbl.send_bf('hello grbl', post=True)  # this will send 'hello grbl' to main terminal
```
