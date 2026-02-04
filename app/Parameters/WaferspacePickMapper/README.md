# WaferspacePickMapper

Takes reticle layout data and wafer_map with die positions and generates picklists grouped by various parameters.

## Example Usage

### wafer map

```
X,Y,RETICLE_SHOT,COL|ROW
-75.78,-52.802,S-3_-3,C4R4
-71.876,-56.628,S-3_-3,C5R3
-71.876,-52.802,S-3_-3,C5R4
-67.972,-61.722,S-3_-3,C6R2
-67.972,-56.628,S-3_-3,C6R3
```
### reticle layout

```
[
    [
        {'code': 'JKU2', 'project': 'gf180mcu-jku-atbs-adc', 'slot_size': '1x0p5'},
        {'code': 'OCD2_1', 'project': 'ocd_sram_test', 'slot_size': '1x0p5'}, 
        {'code': 'OCD2_2', 'project': 'ocd_sram_test', 'slot_size': '1x0p5'},     
    ],
    [
        {'code': 'GD04_1', 'project': 'Racquet Wide 1x0.5', 'slot_size': '1x0p5'}, 
        {'code': 'TQVC_1', 'project': 'TinyQV - Risc-V SoC', 'slot_size': '1x0p5'},
        {'code': 'HZ80', 'project': 'FOSSi replacement for Z80', 'slot_size': '0p5x1'}
    ]
]
```