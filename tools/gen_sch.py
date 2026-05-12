#!/usr/bin/env python3
"""
Generate ncv7240-driver.kicad_sch — a KiCad 8 schematic with all symbols
embedded inline so it renders correctly in kicanvas.org without external libs.

The schematic is block-diagram style: each IC is a rectangular symbol with
its used pins exposed; interconnects are expressed as KiCad global labels so
the connectivity is unambiguous without exhaustive wire routing.

Run from the repo root:
    python3 tools/gen_sch.py > ncv7240-driver.kicad_sch
"""

import uuid
import sys

# ---------- helpers ---------------------------------------------------------

# Deterministic UUIDs so re-runs produce byte-identical output (nice for git).
_uuid_counter = 0
def u():
    global _uuid_counter
    _uuid_counter += 1
    return f"00000000-0000-0000-0000-{_uuid_counter:012x}"

def eff(size=1.27, justify=None, hide=False):
    parts = [f"(font (size {size} {size}))"]
    if justify:
        parts.append(f"(justify {justify})")
    if hide:
        parts.append("hide")
    return "(effects " + " ".join(parts) + ")"

# ---------- symbol library --------------------------------------------------
# Each entry: ( "Lib:Name", [pins], width, height, ref_prefix )
# pin: (number, name, side, y_offset, etype)   side in L/R/T/B
# etype: input/output/bidirectional/power_in/passive/open_collector/...

def sym(name, ref, value, pins, w, h, power=False, fp=""):
    """Emit a (symbol ...) library entry."""
    out = []
    short = name.split(":", 1)[-1]
    out.append(f'(symbol "{name}"')
    out.append('  (pin_names (offset 0.508))')
    out.append('  (exclude_from_sim no) (in_bom yes) (on_board yes)')
    if power:
        out.append('  (power)')
    out.append(f'  (property "Reference" "{ref}" (at 0 {h/2+2.54:.2f} 0) {eff()})')
    out.append(f'  (property "Value" "{value}" (at 0 {-h/2-2.54:.2f} 0) {eff()})')
    out.append(f'  (property "Footprint" "{fp}" (at 0 0 0) {eff(hide=True)})')
    out.append(f'  (property "Datasheet" "" (at 0 0 0) {eff(hide=True)})')
    out.append(f'  (symbol "{short}_0_1"')
    if not power:
        out.append(f'    (rectangle (start {-w/2:.2f} {h/2:.2f}) (end {w/2:.2f} {-h/2:.2f})')
        out.append('      (stroke (width 0.254) (type default))')
        out.append('      (fill (type background))')
        out.append('    )')
    out.append('  )')
    out.append(f'  (symbol "{short}_1_1"')
    for (num, pname, side, yoff, etype) in pins:
        if side == 'L':
            x, y, rot = -w/2 - 2.54, yoff, 0
        elif side == 'R':
            x, y, rot = w/2 + 2.54, yoff, 180
        elif side == 'T':
            x, y, rot = yoff, h/2 + 2.54, 270
        else:  # B
            x, y, rot = yoff, -h/2 - 2.54, 90
        out.append(f'    (pin {etype} line (at {x:.2f} {y:.2f} {rot}) (length 2.54)')
        out.append(f'      (name "{pname}" {eff()})')
        out.append(f'      (number "{num}" {eff()})')
        out.append('    )')
    out.append('  )')
    out.append(')')
    return "\n".join(out)

# ---- Power symbols (special: invisible body, single pin pointing up) -------
def pwr_sym(name, label):
    short = name.split(":", 1)[-1]
    return f'''(symbol "{name}"
  (power) (pin_names (offset 0)) (in_bom yes) (on_board yes)
  (property "Reference" "#PWR" (at 0 -3.81 0) {eff(hide=True)})
  (property "Value" "{label}" (at 0 3.556 0) {eff()})
  (property "Footprint" "" (at 0 0 0) {eff(hide=True)})
  (property "Datasheet" "" (at 0 0 0) {eff(hide=True)})
  (symbol "{short}_0_1"
    (polyline (pts (xy -1.016 -0.508) (xy 0 0.762) (xy 1.016 -0.508) (xy -1.016 -0.508))
      (stroke (width 0) (type default)) (fill (type none))
    )
  )
  (symbol "{short}_1_1"
    (pin power_in line (at 0 0 90) (length 0)
      (name "{label}" {eff(hide=True)})
      (number "1" {eff(hide=True)})
    )
  )
)'''

# ---- Symbol definitions used in this schematic -----------------------------

LIB = []

# Power flags
LIB.append(pwr_sym("power:+24V",  "+24V"))
LIB.append(pwr_sym("power:+3V3",  "+3V3"))
LIB.append(pwr_sym("power:VBUS",  "VBUS"))
LIB.append(pwr_sym("power:GND",   "GND"))

# Resistor
LIB.append('''(symbol "Device:R"
  (pin_names (offset 0) hide) (exclude_from_sim no) (in_bom yes) (on_board yes)
  (property "Reference" "R" (at 2.032 0 90) ''' + eff() + ''')
  (property "Value" "R" (at 0 0 90) ''' + eff() + ''')
  (property "Footprint" "" (at 0 0 0) ''' + eff(hide=True) + ''')
  (property "Datasheet" "" (at 0 0 0) ''' + eff(hide=True) + ''')
  (symbol "R_0_1"
    (rectangle (start -1.016 -2.54) (end 1.016 2.54)
      (stroke (width 0.254) (type default)) (fill (type none))
    )
  )
  (symbol "R_1_1"
    (pin passive line (at 0  3.81 270) (length 1.27) (name "~" ''' + eff() + ''') (number "1" ''' + eff() + '''))
    (pin passive line (at 0 -3.81 90)  (length 1.27) (name "~" ''' + eff() + ''') (number "2" ''' + eff() + '''))
  )
)''')

# Capacitor
LIB.append('''(symbol "Device:C"
  (pin_names (offset 0.254) hide) (exclude_from_sim no) (in_bom yes) (on_board yes)
  (property "Reference" "C" (at 2.032 0 90) ''' + eff() + ''')
  (property "Value" "C" (at 0 -3.81 0) ''' + eff() + ''')
  (property "Footprint" "" (at 0 0 0) ''' + eff(hide=True) + ''')
  (property "Datasheet" "" (at 0 0 0) ''' + eff(hide=True) + ''')
  (symbol "C_0_1"
    (polyline (pts (xy -2.032 -0.762) (xy 2.032 -0.762)) (stroke (width 0.508) (type default)) (fill (type none)))
    (polyline (pts (xy -2.032  0.762) (xy 2.032  0.762)) (stroke (width 0.508) (type default)) (fill (type none)))
  )
  (symbol "C_1_1"
    (pin passive line (at 0  3.81 270) (length 2.794) (name "~" ''' + eff() + ''') (number "1" ''' + eff() + '''))
    (pin passive line (at 0 -3.81 90)  (length 2.794) (name "~" ''' + eff() + ''') (number "2" ''' + eff() + '''))
  )
)''')

# Inductor
LIB.append('''(symbol "Device:L"
  (pin_names (offset 1.016) hide) (exclude_from_sim no) (in_bom yes) (on_board yes)
  (property "Reference" "L" (at -1.27 0 90) ''' + eff() + ''')
  (property "Value" "L" (at 1.905 0 90) ''' + eff() + ''')
  (property "Footprint" "" (at 0 0 0) ''' + eff(hide=True) + ''')
  (property "Datasheet" "" (at 0 0 0) ''' + eff(hide=True) + ''')
  (symbol "L_0_1"
    (arc (start 0 -2.54) (mid 0.7239 -1.905) (end 0 -1.27) (stroke (width 0) (type default)) (fill (type none)))
    (arc (start 0 -1.27) (mid 0.7239 -0.635) (end 0  0.00) (stroke (width 0) (type default)) (fill (type none)))
    (arc (start 0  0.00) (mid 0.7239  0.635) (end 0  1.27) (stroke (width 0) (type default)) (fill (type none)))
    (arc (start 0  1.27) (mid 0.7239  1.905) (end 0  2.54) (stroke (width 0) (type default)) (fill (type none)))
  )
  (symbol "L_1_1"
    (pin passive line (at 0  3.81 270) (length 1.27) (name "~" ''' + eff() + ''') (number "1" ''' + eff() + '''))
    (pin passive line (at 0 -3.81 90)  (length 1.27) (name "~" ''' + eff() + ''') (number "2" ''' + eff() + '''))
  )
)''')

# Diode (TVS / generic) — pin1=K (left), pin2=A (right)
for _nm in ("Device:D_TVS", "Device:D"):
    _shape_extra = '(polyline (pts (xy -1.27 1.27) (xy -1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))' if _nm == "Device:D" else \
                   '(polyline (pts (xy 1.27 1.27) (xy 1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))'
    LIB.append(f'''(symbol "{_nm}"
  (pin_names (offset 0.254) hide) (exclude_from_sim no) (in_bom yes) (on_board yes)
  (property "Reference" "D" (at 0 2.54 0) {eff()})
  (property "Value" "{_nm.split(":")[1]}" (at 0 -2.54 0) {eff()})
  (property "Footprint" "" (at 0 0 0) {eff(hide=True)})
  (property "Datasheet" "" (at 0 0 0) {eff(hide=True)})
  (symbol "{_nm.split(":")[1]}_0_1"
    (polyline (pts (xy -1.27 1.27) (xy 1.27 0) (xy -1.27 -1.27) (xy -1.27 1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
    {_shape_extra}
  )
  (symbol "{_nm.split(":")[1]}_1_1"
    (pin passive line (at -3.81 0 0)   (length 2.54) (name "K" {eff()}) (number "1" {eff()}))
    (pin passive line (at  3.81 0 180) (length 2.54) (name "A" {eff()}) (number "2" {eff()}))
  )
)''')

# --- IC / block symbols -----------------------------------------------------

# USB-C receptacle (USB 2.0 16-pin)
LIB.append(sym(
    "Connector:USB_C", "J", "USB_C_Receptacle",
    pins=[
        ("A1",  "GND",  'L',  12.7,  "power_in"),
        ("A4",  "VBUS", 'L',  10.16, "power_in"),
        ("A5",  "CC1",  'L',   7.62, "bidirectional"),
        ("A6",  "D+",   'L',   5.08, "bidirectional"),
        ("A7",  "D-",   'L',   2.54, "bidirectional"),
        ("A8",  "SBU1", 'L',   0,    "bidirectional"),
        ("A9",  "VBUS", 'L',  -2.54, "power_in"),
        ("A12", "GND",  'L',  -5.08, "power_in"),
        ("B5",  "CC2",  'L',  -7.62, "bidirectional"),
        ("B8",  "SBU2", 'L', -10.16, "bidirectional"),
        ("SH",  "SHIELD",'L',-12.7,  "passive"),
    ],
    w=22.86, h=33.02, fp="Connector:USB_C_Receptacle_HRO_TYPE-C-31-M-12"
))

# AP33772S — PD EPR sink controller (key pins, simplified)
LIB.append(sym(
    "PMIC:AP33772S", "U", "AP33772S",
    pins=[
        # left
        ("1",  "VBUS",   'L',  10.16, "power_in"),
        ("2",  "CC1",    'L',   7.62, "bidirectional"),
        ("3",  "CC2",    'L',   5.08, "bidirectional"),
        ("4",  "VDD",    'L',   2.54, "power_in"),
        ("5",  "GND",    'L',   0,    "power_in"),
        ("6",  "VPP",    'L',  -2.54, "passive"),
        # right
        ("20", "VOUT",   'R',  10.16, "power_out"),
        ("19", "VOUT_EN",'R',   7.62, "output"),
        ("18", "SDA",    'R',   5.08, "bidirectional"),
        ("17", "SCL",    'R',   2.54, "input"),
        ("16", "INT",    'R',   0,    "output"),
        ("15", "GPIO1",  'R',  -2.54, "bidirectional"),
        ("14", "GPIO2",  'R',  -5.08, "bidirectional"),
    ],
    w=25.4, h=27.94, fp="Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm"
))

# ESP32-S3-WROOM-1 — module (only pins used in this design)
LIB.append(sym(
    "RF_Module:ESP32-S3-WROOM-1", "U", "ESP32-S3-WROOM-1-N8R8",
    pins=[
        # left
        ("2",  "3V3",       'L',  20.32, "power_in"),
        ("3",  "EN",        'L',  17.78, "input"),
        ("27", "GND",       'L',  15.24, "power_in"),
        ("4",  "IO0/BOOT",  'L',  10.16, "bidirectional"),
        ("10", "IO4",       'L',   7.62, "bidirectional"),
        ("18", "IO8",       'L',   5.08, "bidirectional"),
        ("17", "IO9",       'L',   2.54, "bidirectional"),
        ("19", "IO10",      'L',   0,    "bidirectional"),
        ("20", "IO11",      'L',  -2.54, "bidirectional"),
        ("23", "IO12",      'L',  -5.08, "bidirectional"),
        ("24", "IO13",      'L',  -7.62, "bidirectional"),
        ("25", "IO14",      'L', -10.16, "bidirectional"),
        ("26", "IO15",      'L', -12.7,  "bidirectional"),
        # right
        ("28", "IO16",      'R',  20.32, "bidirectional"),
        ("29", "IO17",      'R',  17.78, "bidirectional"),
        ("30", "IO18",      'R',  15.24, "bidirectional"),
        ("13", "IO19/USB_D-", 'R', 12.7, "bidirectional"),
        ("14", "IO20/USB_D+", 'R', 10.16, "bidirectional"),
        ("1",  "GND",       'R',   2.54, "power_in"),
    ],
    w=33.02, h=48.26, fp="RF_Module:ESP32-S3-WROOM-1"
))

# NCV7240 — octal low-side driver, SPI
LIB.append(sym(
    "Driver_Motor:NCV7240", "U", "NCV7240",
    pins=[
        # left: control + power
        ("1",  "VPWR",  'L',  10.16, "power_in"),
        ("2",  "VDD",   'L',   7.62, "power_in"),
        ("3",  "CSB",   'L',   5.08, "input"),
        ("4",  "SCLK",  'L',   2.54, "input"),
        ("5",  "SI",    'L',   0,    "input"),
        ("6",  "SO",    'L',  -2.54, "open_collector"),
        ("7",  "RSTB",  'L',  -5.08, "input"),
        ("8",  "FSOB",  'L',  -7.62, "open_collector"),
        ("12", "GND",   'L', -10.16, "power_in"),
        # right: outputs
        ("13", "OUT0",  'R',  10.16, "open_collector"),
        ("14", "OUT1",  'R',   7.62, "open_collector"),
        ("15", "OUT2",  'R',   5.08, "open_collector"),
        ("16", "OUT3",  'R',   2.54, "open_collector"),
        ("17", "OUT4",  'R',   0,    "open_collector"),
        ("18", "OUT5",  'R',  -2.54, "open_collector"),
        ("19", "OUT6",  'R',  -5.08, "open_collector"),
        ("20", "OUT7",  'R',  -7.62, "open_collector"),
    ],
    w=27.94, h=27.94, fp="Package_SO:SSOP-24_5.3x8.2mm_P0.65mm"
))

# Buck 24V -> 3.3V (generic 6-pin)
LIB.append(sym(
    "Regulator_Switching:BUCK_24_3V3", "U", "MP2451 / TPS62932",
    pins=[
        ("1", "VIN", 'L',  5.08, "power_in"),
        ("2", "EN",  'L',  2.54, "input"),
        ("3", "GND", 'L',  0,    "power_in"),
        ("4", "FB",  'R', -2.54, "input"),
        ("5", "BST", 'R',  2.54, "passive"),
        ("6", "SW",  'R',  5.08, "output"),
    ],
    w=22.86, h=15.24, fp="Package_TO_SOT_SMD:SOT-23-6"
))

# 8-pin output header (screw terminal block)
LIB.append(sym(
    "Connector:Screw_Term_8", "J", "Screw_Terminal_8",
    pins=[
        ("1", "1", 'L',  8.89, "passive"),
        ("2", "2", 'L',  6.35, "passive"),
        ("3", "3", 'L',  3.81, "passive"),
        ("4", "4", 'L',  1.27, "passive"),
        ("5", "5", 'L', -1.27, "passive"),
        ("6", "6", 'L', -3.81, "passive"),
        ("7", "7", 'L', -6.35, "passive"),
        ("8", "8", 'L', -8.89, "passive"),
    ],
    w=12.7, h=22.86, fp="TerminalBlock:TerminalBlock_Phoenix_MKDS-1,5-8_1x08_P5.00mm_Horizontal"
))

# ---------- component instances ---------------------------------------------

INSTANCES = []  # each: (lib_id, ref, value, x, y, rotation, fp, extra_pins_count)
LABELS    = []  # global labels: (text, x, y, rot, shape)
WIRES     = []  # ((x1,y1),(x2,y2))
POWER     = []  # (lib_id, x, y, rot)
TEXTS     = []  # (text, x, y, size)

# Title block coordinates: KiCad A2 sheet is 594 x 420.
SHEET_W, SHEET_H = 594.0, 420.0

def place(lib_id, ref, value, x, y, rot=0, fp=""):
    INSTANCES.append((lib_id, ref, value, x, y, rot, fp))

def gl(text, x, y, rot=0, shape="input"):
    LABELS.append((text, x, y, rot, shape))

def wire(p1, p2):
    WIRES.append((p1, p2))

def pwr(lib_id, x, y, rot=0):
    POWER.append((lib_id, x, y, rot))

def note(text, x, y, size=1.5):
    TEXTS.append((text, x, y, size))

# ---------------- USB-C input + AP33772S ----------------
J1_X, J1_Y = 60, 80
place("Connector:USB_C", "J1", "USB-C EPR", J1_X, J1_Y,
      fp="Connector:USB_C_Receptacle_HRO_TYPE-C-31-M-12")

U1_X, U1_Y = 140, 80
place("PMIC:AP33772S", "U1", "AP33772S", U1_X, U1_Y,
      fp="Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm")

# wire VBUS / CC / GND from USB-C to AP33772S (short stubs + global labels)
# left side of AP33772S is at U1_X - 25.4/2 - 2.54 = 124.83
# right side of USB-C is at J1_X + 22.86/2 + 2.54 = 73.97
# Use global labels for clarity:
for nm, y_j1, y_u1 in [("VBUS",      J1_Y - 10.16, U1_Y - 10.16),
                       ("CC1",       J1_Y - 7.62,  U1_Y - 7.62),
                       ("CC2",       J1_Y + 7.62,  U1_Y - 5.08),
                       ("USB_GND",   J1_Y - 12.7,  None)]:
    # USB-C is on the LEFT, so its pins exit to the LEFT (rot=0 pin facing left)
    # Wait — Connector:USB_C has all pins on side 'L' so they exit to the LEFT of the symbol.
    # That's awkward — but fine, we just place labels to the left of J1.
    pass

# Power symbols on AP33772S
pwr("power:VBUS", U1_X - 25.4/2 - 2.54 - 5.08, U1_Y - 10.16)  # VBUS pin
pwr("power:GND",  U1_X - 25.4/2 - 2.54 - 5.08, U1_Y, rot=180) # GND pin
pwr("power:+3V3", U1_X - 25.4/2 - 2.54 - 5.08, U1_Y + 2.54)   # VDD on AP33772S = 3.3V
pwr("power:+24V", U1_X + 25.4/2 + 2.54 + 5.08, U1_Y - 10.16)  # VOUT = 24V negotiated

# USB-C power
pwr("power:VBUS", J1_X - 22.86/2 - 2.54 - 5.08, J1_Y + 10.16)  # A4 VBUS
pwr("power:VBUS", J1_X - 22.86/2 - 2.54 - 5.08, J1_Y - 2.54)   # A9 VBUS
pwr("power:GND",  J1_X - 22.86/2 - 2.54 - 5.08, J1_Y + 12.7, rot=180)  # A1 GND
pwr("power:GND",  J1_X - 22.86/2 - 2.54 - 5.08, J1_Y - 5.08, rot=180)  # A12 GND
pwr("power:GND",  J1_X - 22.86/2 - 2.54 - 5.08, J1_Y - 12.7, rot=180)  # SHIELD

# CC1 / CC2 labels
gl("CC1", J1_X - 22.86/2 - 2.54 - 5.08, J1_Y + 7.62, rot=180, shape="bidirectional")
gl("CC2", J1_X - 22.86/2 - 2.54 - 5.08, J1_Y - 7.62, rot=180, shape="bidirectional")
gl("CC1", U1_X - 25.4/2 - 2.54 - 5.08,  U1_Y - 7.62, rot=180, shape="bidirectional")
gl("CC2", U1_X - 25.4/2 - 2.54 - 5.08,  U1_Y - 5.08, rot=180, shape="bidirectional")

# AP33772S right-side labels
gl("PD_VOUT_EN", U1_X + 25.4/2 + 2.54 + 5.08, U1_Y - 7.62, rot=0, shape="output")
gl("I2C_SDA",    U1_X + 25.4/2 + 2.54 + 5.08, U1_Y - 5.08, rot=0, shape="bidirectional")
gl("I2C_SCL",    U1_X + 25.4/2 + 2.54 + 5.08, U1_Y - 2.54, rot=0, shape="input")
gl("PD_INT",     U1_X + 25.4/2 + 2.54 + 5.08, U1_Y - 0,    rot=0, shape="output")

# Bulk caps on VBUS_24V (aluminium polymer SMD)
place("Device:C", "C1", "100uF/50V", U1_X + 25.4/2 + 17.78, U1_Y - 5.08, rot=0,
      fp="Capacitor_SMD:CP_Elec_10x10.5")
place("Device:C", "C2", "10uF/50V",  U1_X + 25.4/2 + 25.4,  U1_Y - 5.08, rot=0,
      fp="Capacitor_SMD:C_1210_3225Metric")
pwr("power:+24V", U1_X + 25.4/2 + 17.78, U1_Y - 5.08 - 3.81)
pwr("power:+24V", U1_X + 25.4/2 + 25.4,  U1_Y - 5.08 - 3.81)
pwr("power:GND",  U1_X + 25.4/2 + 17.78, U1_Y - 5.08 + 3.81, rot=180)
pwr("power:GND",  U1_X + 25.4/2 + 25.4,  U1_Y - 5.08 + 3.81, rot=180)

# TVS on VBUS
place("Device:D_TVS", "D1", "SMBJ33A", U1_X + 25.4/2 + 33.02, U1_Y - 5.08, rot=90,
      fp="Diode_SMD:D_SMB")

# AP33772S decoupling note
note("AP33772S: 1uF on VDD, 100nF on VPP\\n(place close to IC pins, not shown here)",
     U1_X - 10, U1_Y + 22, size=1.27)

# ---------------- Buck 24V -> 3.3V ----------------
U7_X, U7_Y = 140, 180
place("Regulator_Switching:BUCK_24_3V3", "U7", "TPS62932", U7_X, U7_Y,
      fp="Package_TO_SOT_SMD:SOT-23-6")
pwr("power:+24V", U7_X - 22.86/2 - 2.54 - 5.08, U7_Y + 5.08)
pwr("power:GND",  U7_X - 22.86/2 - 2.54 - 5.08, U7_Y + 0,    rot=180)
gl("EN_3V3", U7_X - 22.86/2 - 2.54 - 5.08, U7_Y + 2.54, rot=180, shape="input")

# Inductor on SW node
place("Device:L", "L1", "4.7uH/2A", U7_X + 22.86/2 + 7.62, U7_Y + 5.08, rot=90,
      fp="Inductor_SMD:L_Bourns-SRN6045TA")
# Output cap
place("Device:C", "C3", "22uF",  U7_X + 22.86/2 + 17.78, U7_Y + 5.08, rot=0,
      fp="Capacitor_SMD:C_0805_2012Metric")
pwr("power:+3V3", U7_X + 22.86/2 + 17.78, U7_Y + 5.08 - 3.81)
pwr("power:GND",  U7_X + 22.86/2 + 17.78, U7_Y + 5.08 + 3.81, rot=180)
# Feedback resistors
place("Device:R", "R6", "100k",  U7_X + 22.86/2 + 5.08,  U7_Y - 7.62, rot=0,
      fp="Resistor_SMD:R_0603_1608Metric")
place("Device:R", "R7", "20k",   U7_X + 22.86/2 + 5.08,  U7_Y - 15.24, rot=0,
      fp="Resistor_SMD:R_0603_1608Metric")
note("Buck 24V→3.3V, ≥500mA\\nVOUT = 0.6V·(1+R6/R7)",
     U7_X - 12, U7_Y + 15, size=1.27)

# ---------------- ESP32-S3 ----------------
U2_X, U2_Y = 290, 130
place("RF_Module:ESP32-S3-WROOM-1", "U2", "ESP32-S3-WROOM-1-N8R8", U2_X, U2_Y,
      fp="RF_Module:ESP32-S3-WROOM-1")

# Left-side rails
pwr("power:+3V3", U2_X - 33.02/2 - 2.54 - 5.08, U2_Y + 20.32)
gl("RST_BTN",  U2_X - 33.02/2 - 2.54 - 5.08, U2_Y + 17.78, rot=180, shape="input")
pwr("power:GND",  U2_X - 33.02/2 - 2.54 - 5.08, U2_Y + 15.24, rot=180)
gl("BOOT_BTN", U2_X - 33.02/2 - 2.54 - 5.08, U2_Y + 10.16, rot=180, shape="input")

# Left-side signal labels
for nm, y in [
    ("PD_INT",   U2_Y + 7.62),
    ("I2C_SDA",  U2_Y + 5.08),
    ("I2C_SCL",  U2_Y + 2.54),
    ("SPI_CS1",  U2_Y + 0),
    ("SPI_CS2",  U2_Y - 2.54),
    ("SPI_CS3",  U2_Y - 5.08),
    ("SPI_CS4",  U2_Y - 7.62),
    ("SPI_SCK",  U2_Y - 10.16),
    ("SPI_MOSI", U2_Y - 12.7),
]:
    gl(nm, U2_X - 33.02/2 - 2.54 - 5.08, y, rot=180, shape="bidirectional")

# Right side
for nm, y in [
    ("SPI_MISO", U2_Y + 20.32),
    ("NCV_RSTB", U2_Y + 17.78),
    ("NCV_FSOB", U2_Y + 15.24),
    ("USB_D-",   U2_Y + 12.7),
    ("USB_D+",   U2_Y + 10.16),
]:
    gl(nm, U2_X + 33.02/2 + 2.54 + 5.08, y, rot=0, shape="bidirectional")
pwr("power:GND",  U2_X + 33.02/2 + 2.54 + 5.08, U2_Y + 2.54, rot=180)

# Pull-ups (right of ESP32)
PU_X = U2_X + 50
FP_R0603 = "Resistor_SMD:R_0603_1608Metric"
place("Device:R", "R1", "10k",  PU_X,        U2_Y + 22, rot=0, fp=FP_R0603); pwr("power:+3V3", PU_X, U2_Y + 22 - 3.81)
gl("SPI_MISO", PU_X, U2_Y + 22 + 3.81, rot=270, shape="bidirectional")
place("Device:R", "R2", "10k",  PU_X + 7.62, U2_Y + 22, rot=0, fp=FP_R0603); pwr("power:+3V3", PU_X + 7.62, U2_Y + 22 - 3.81)
gl("NCV_RSTB", PU_X + 7.62, U2_Y + 22 + 3.81, rot=270, shape="bidirectional")
place("Device:R", "R3", "10k",  PU_X + 15.24,U2_Y + 22, rot=0, fp=FP_R0603); pwr("power:+3V3", PU_X + 15.24, U2_Y + 22 - 3.81)
gl("NCV_FSOB", PU_X + 15.24, U2_Y + 22 + 3.81, rot=270, shape="bidirectional")
place("Device:R", "R4", "4.7k", PU_X + 22.86,U2_Y + 22, rot=0, fp=FP_R0603); pwr("power:+3V3", PU_X + 22.86, U2_Y + 22 - 3.81)
gl("I2C_SDA",  PU_X + 22.86, U2_Y + 22 + 3.81, rot=270, shape="bidirectional")
place("Device:R", "R5", "4.7k", PU_X + 30.48,U2_Y + 22, rot=0, fp=FP_R0603); pwr("power:+3V3", PU_X + 30.48, U2_Y + 22 - 3.81)
gl("I2C_SCL",  PU_X + 30.48, U2_Y + 22 + 3.81, rot=270, shape="bidirectional")

# 3V3 decoupling
FP_C0603 = "Capacitor_SMD:C_0603_1608Metric"
FP_C0805 = "Capacitor_SMD:C_0805_2012Metric"
place("Device:C", "C4", "10uF",  U2_X - 33.02/2 - 12.7, U2_Y + 25.4, rot=0, fp=FP_C0805)
pwr("power:+3V3", U2_X - 33.02/2 - 12.7, U2_Y + 25.4 - 3.81)
pwr("power:GND",  U2_X - 33.02/2 - 12.7, U2_Y + 25.4 + 3.81, rot=180)
place("Device:C", "C5", "100nF", U2_X - 33.02/2 - 5.08, U2_Y + 25.4, rot=0, fp=FP_C0603)
pwr("power:+3V3", U2_X - 33.02/2 - 5.08, U2_Y + 25.4 - 3.81)
pwr("power:GND",  U2_X - 33.02/2 - 5.08, U2_Y + 25.4 + 3.81, rot=180)

note("Antenna keep-out ≥15mm under module top edge",
     U2_X - 15, U2_Y - 30, size=1.27)

# ---------------- 4 × NCV7240 + output headers ----------------
for i, (ref, ch_start) in enumerate([("U3",1),("U4",9),("U5",17),("U6",25)]):
    NX = 430
    NY = 60 + i*80
    place("Driver_Motor:NCV7240", ref, "NCV7240", NX, NY,
          fp="Package_SO:SSOP-24_5.3x8.2mm_P0.65mm")
    # Power
    pwr("power:+24V", NX - 27.94/2 - 2.54 - 5.08, NY + 10.16)         # VPWR
    pwr("power:+3V3", NX - 27.94/2 - 2.54 - 5.08, NY + 7.62)          # VDD
    pwr("power:GND",  NX - 27.94/2 - 2.54 - 5.08, NY - 10.16, rot=180)# GND
    # Control bus labels (left side)
    gl(f"SPI_CS{i+1}", NX - 27.94/2 - 2.54 - 5.08, NY + 5.08,  rot=180, shape="input")
    gl("SPI_SCK",      NX - 27.94/2 - 2.54 - 5.08, NY + 2.54,  rot=180, shape="input")
    gl("SPI_MOSI",     NX - 27.94/2 - 2.54 - 5.08, NY + 0,     rot=180, shape="input")
    gl("SPI_MISO",     NX - 27.94/2 - 2.54 - 5.08, NY - 2.54,  rot=180, shape="bidirectional")
    gl("NCV_RSTB",     NX - 27.94/2 - 2.54 - 5.08, NY - 5.08,  rot=180, shape="input")
    gl("NCV_FSOB",     NX - 27.94/2 - 2.54 - 5.08, NY - 7.62,  rot=180, shape="bidirectional")
    # Local decoupling caps (one shown per IC, representative)
    place("Device:C", f"C{10+i*2}", "100nF",
          NX - 27.94/2 - 17.78, NY + 10.16, rot=0, fp=FP_C0603)
    pwr("power:+24V", NX - 27.94/2 - 17.78, NY + 10.16 - 3.81)
    pwr("power:GND",  NX - 27.94/2 - 17.78, NY + 10.16 + 3.81, rot=180)
    place("Device:C", f"C{11+i*2}", "10uF/50V",
          NX - 27.94/2 - 25.4, NY + 10.16, rot=0,
          fp="Capacitor_SMD:C_1210_3225Metric")
    pwr("power:+24V", NX - 27.94/2 - 25.4, NY + 10.16 - 3.81)
    pwr("power:GND",  NX - 27.94/2 - 25.4, NY + 10.16 + 3.81, rot=180)
    # Output header
    JX = NX + 50
    JY = NY
    place("Connector:Screw_Term_8", f"J{2+i}", f"OUT{ch_start}..{ch_start+7}", JX, JY,
          fp="TerminalBlock:TerminalBlock_Phoenix_MKDS-1,5-8_1x08_P5.00mm_Horizontal")
    # Wire each NCV7240 output to the header pin via a global label
    for k in range(8):
        ncv_y = NY + 10.16 - k*2.54
        hdr_y = JY + 8.89 - k*2.54
        ch = ch_start + k
        # Place global label between IC right side and header left side
        gl(f"OUT{ch}", NX + 27.94/2 + 2.54 + 5.08, ncv_y, rot=0,  shape="output")
        gl(f"OUT{ch}", JX - 12.7/2  - 2.54 - 5.08, hdr_y, rot=180, shape="input")

# ---------------- Freewheel diode array (32x B260A) ----------------
# Bürkert 0127 valves are inductive (≈3 W @ 24 V ⇒ ~125 mA, several tens of mH).
# Each output gets a B260A Schottky (60 V / 2 A) clamping OUTx → +24V rail.
# Anode → OUTx, Cathode → +24V. Placed in a 4×8 grid below the main section.
FW_X0, FW_Y0 = 60, 340           # top-left of array
FW_DX, FW_DY = 16.0, 10.16       # column / row pitch
note("Freewheel diodes for inductive loads (Bürkert Type 0127 valves)\\n"
     "B260A-13-F  60V / 2A  SMA  —  K→+24V, A→OUTx", FW_X0, FW_Y0 - 8, size=1.5)
fb_idx = 1
for i in range(4):                       # one row per NCV7240
    for k in range(8):                   # 8 channels per IC
        ch = i*8 + k + 1
        dx = FW_X0 + k*FW_DX
        dy = FW_Y0 + i*FW_DY
        place("Device:D", f"D{1+fb_idx}", "B260A-13-F", dx, dy, rot=0,
              fp="Diode_SMD:D_SMA")
        # Cathode (pin1) at left = +24V
        pwr("power:+24V", dx - 3.81 - 2.54, dy, rot=270)
        # Anode (pin2) at right = OUTx
        gl(f"OUT{ch}", dx + 3.81 + 2.54, dy, rot=0, shape="input")
        fb_idx += 1

# Section labels (large text)
note("USB-C PD 3.1 EPR sink — 24V/3A negotiated", 30, 40, size=2.0)
note("ESP32-S3-WROOM-1 (Wi-Fi/BT, USB-OTG)",      245, 95, size=2.0)
note("4× NCV7240 — 32 low-side outputs @ 24V",    405, 25, size=2.0)
note("24V → 3.3V buck",                            110, 165, size=1.5)

# ---------- emit -----------------------------------------------------------

OUT = []
OUT.append('(kicad_sch (version 20231120) (generator "eeschema")')
OUT.append(f'  (uuid "{u()}")')
OUT.append('  (paper "A2")')
OUT.append('  (title_block')
OUT.append('    (title "NCV7240 x4 Low-side Driver Board")')
OUT.append('    (date "2026-05-12")')
OUT.append('    (rev "0.2")')
OUT.append('    (company "")')
OUT.append('    (comment 1 "ESP32-S3 + AP33772S USB-C PD EPR @ 24V driving 32 channels via 4x NCV7240")')
OUT.append('  )')

# lib_symbols
OUT.append('  (lib_symbols')
for s in LIB:
    OUT.append("    " + s.replace("\n", "\n    "))
OUT.append('  )')

# components
for (lib_id, ref, value, x, y, rot, fp) in INSTANCES:
    OUT.append(f'  (symbol (lib_id "{lib_id}") (at {x} {y} {rot}) (unit 1)')
    OUT.append('    (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)')
    OUT.append(f'    (uuid "{u()}")')
    OUT.append(f'    (property "Reference" "{ref}" (at {x+2} {y-12} 0) {eff()})')
    OUT.append(f'    (property "Value" "{value}" (at {x+2} {y+12} 0) {eff()})')
    OUT.append(f'    (property "Footprint" "{fp}" (at {x} {y} 0) {eff(hide=True)})')
    OUT.append(f'    (property "Datasheet" "" (at {x} {y} 0) {eff(hide=True)})')
    OUT.append('  )')

# power flags
for (lib_id, x, y, rot) in POWER:
    OUT.append(f'  (symbol (lib_id "{lib_id}") (at {x} {y} {rot}) (unit 1)')
    OUT.append('    (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)')
    OUT.append(f'    (uuid "{u()}")')
    OUT.append(f'    (property "Reference" "#PWR" (at {x} {y-3.81} 0) {eff(hide=True)})')
    val = lib_id.split(":")[1]
    OUT.append(f'    (property "Value" "{val}" (at {x} {y+3.556} 0) {eff()})')
    OUT.append(f'    (property "Footprint" "" (at {x} {y} 0) {eff(hide=True)})')
    OUT.append(f'    (property "Datasheet" "" (at {x} {y} 0) {eff(hide=True)})')
    OUT.append('  )')

# global labels
for (text, x, y, rot, shape) in LABELS:
    OUT.append(f'  (global_label "{text}" (shape {shape}) (at {x} {y} {rot}) (fields_autoplaced)')
    OUT.append(f'    (effects (font (size 1.27 1.27)) (justify left))')
    OUT.append(f'    (uuid "{u()}")')
    OUT.append('  )')

# text notes
for (text, x, y, size) in TEXTS:
    safe = text.replace('"', "'")
    OUT.append(f'  (text "{safe}" (at {x} {y} 0) (effects (font (size {size} {size})) (justify left)))')

# wires (none in this layout — global-label-based connectivity)
for (p1, p2) in WIRES:
    OUT.append(f'  (wire (pts (xy {p1[0]} {p1[1]}) (xy {p2[0]} {p2[1]})) (stroke (width 0) (type default)) (uuid "{u()}"))')

OUT.append('  (sheet_instances')
OUT.append('    (path "/" (page "1"))')
OUT.append('  )')
OUT.append(')')

sys.stdout.write("\n".join(OUT) + "\n")
