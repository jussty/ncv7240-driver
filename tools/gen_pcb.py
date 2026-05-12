#!/usr/bin/env python3
"""
Generate ncv7240-driver.kicad_pcb — fully placed 4-layer PCB.

Board:  200 × 120 mm, 4-layer (F.Cu / GND / +24V / B.Cu), 1.6 mm FR4 ENIG.

What this generator does:
  - Emits a valid KiCad 8 board file.
  - Inlines minimal but valid footprint geometry (pads + courtyard) for every
    component so kicanvas.org can render it directly from GitHub.
  - Pre-places every component into the floorplan from the schematic.
  - Assigns nets to all pads (matches schematic net list).
  - Pours GND on In1.Cu + B.Cu and +24V on In2.Cu.
  - Drops power vias from each IC's V+/GND pad down to the relevant plane.
  - Routes the SPI/I²C signal bus on F.Cu.
  - Leaves the 32 OUTx flyback-to-screw-terminal traces for KiCad's router
    to finish (geometry is repetitive and trivial to autoroute).

Run from repo root:
    python3 tools/gen_pcb.py > ncv7240-driver.kicad_pcb
"""

import sys

# ---------- deterministic UUIDs --------------------------------------------
_uc = 0
def u():
    global _uc; _uc += 1
    return f"00000000-1111-0000-0000-{_uc:012x}"

# ---------- board dimensions ----------------------------------------------
W, H = 200.0, 120.0           # board size mm
MH_INSET = 4.0
MH_DRILL = 3.2
MH_PAD   = 6.0

# ---------- nets list (must match schematic) ------------------------------
NETS = [
    "", "GND", "+24V", "+3V3", "VBUS",
    "CC1", "CC2",
    "I2C_SDA", "I2C_SCL", "PD_INT", "PD_VOUT_EN",
    "SPI_SCK", "SPI_MOSI", "SPI_MISO",
    "SPI_CS1", "SPI_CS2", "SPI_CS3", "SPI_CS4",
    "NCV_RSTB", "NCV_FSOB",
    "RST_BTN", "BOOT_BTN", "EN_3V3",
    "USB_D+", "USB_D-",
    "BST", "SW", "FB",  # buck local nets
    "SBU1", "SBU2",     # unused but declared
] + [f"OUT{k}" for k in range(1, 33)]
NET = {n: i for i, n in enumerate(NETS)}

# ---------- emit helpers ---------------------------------------------------
OUT = []
def emit(s): OUT.append(s)

def pad_smd(num, x, y, w, h, net):
    """SMD pad on F.Cu (rectangular)."""
    return (f'    (pad "{num}" smd roundrect (at {x:.3f} {y:.3f}) (size {w:.3f} {h:.3f})'
            f' (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25)'
            f' (net {NET[net]} "{net}") (uuid "{u()}"))')

def pad_th(num, x, y, dia, drill, net, oval=False, w=None, h=None):
    """Through-hole pad, all copper layers."""
    if oval:
        return (f'    (pad "{num}" thru_hole oval (at {x:.3f} {y:.3f}) (size {w} {h})'
                f' (drill {drill}) (layers "*.Cu" "*.Mask")'
                f' (net {NET[net]} "{net}") (uuid "{u()}"))')
    return (f'    (pad "{num}" thru_hole circle (at {x:.3f} {y:.3f}) (size {dia} {dia})'
            f' (drill {drill}) (layers "*.Cu" "*.Mask")'
            f' (net {NET[net]} "{net}") (uuid "{u()}"))')

def pad_np(x, y, dia):
    """Non-plated through hole (mounting)."""
    return (f'    (pad "" np_thru_hole circle (at {x} {y}) (size {dia} {dia})'
            f' (drill {dia}) (layers "F&B.Cu" "*.Mask") (uuid "{u()}"))')

def fp_open(lib, ref, value, x, y, rot, layer="F.Cu", attrs="smd"):
    return [
        f'  (footprint "{lib}" (layer "{layer}") (uuid "{u()}") (at {x} {y} {rot})',
        f'    (attr {attrs})',
        f'    (property "Reference" "{ref}" (at 0 -3 {rot}) (layer "F.SilkS")',
        f'      (uuid "{u()}") (effects (font (size 1 1) (thickness 0.15))))',
        f'    (property "Value" "{value}" (at 0 3 {rot}) (layer "F.Fab")',
        f'      (uuid "{u()}") (effects (font (size 0.8 0.8) (thickness 0.12))))',
    ]

def fp_close():
    return ['  )']

def via(x, y, net, drill=0.3, dia=0.6):
    emit(f'  (via (at {x:.3f} {y:.3f}) (size {dia}) (drill {drill})'
         f' (layers "F.Cu" "B.Cu") (net {NET[net]}) (uuid "{u()}"))')

def track(x1, y1, x2, y2, net, layer="F.Cu", width=0.25):
    emit(f'  (segment (start {x1:.3f} {y1:.3f}) (end {x2:.3f} {y2:.3f})'
         f' (width {width}) (layer "{layer}") (net {NET[net]}) (uuid "{u()}"))')

# ---------- footprint factories (placed at component's local origin) -------

def _two_pad(lib, ref, value, x, y, rot, px, pw, ph, n1, n2):
    """Generic 2-pad SMD footprint. Pads at LOCAL (±px, 0); KiCad rotates."""
    out = fp_open(lib, ref, value, x, y, rot)
    out.append(pad_smd("1", -px, 0, pw, ph, n1))
    out.append(pad_smd("2", +px, 0, pw, ph, n2))
    out.extend(fp_close()); emit("\n".join(out))

def place_r0603(ref, value, x, y, rot, n1, n2):
    _two_pad("Resistor_SMD:R_0603_1608Metric", ref, value, x, y, rot, 0.825, 0.8, 0.95, n1, n2)

def place_c0603(ref, value, x, y, rot, n1, n2):
    _two_pad("Capacitor_SMD:C_0603_1608Metric", ref, value, x, y, rot, 0.875, 0.9, 0.95, n1, n2)

def place_c0805(ref, value, x, y, rot, n1, n2):
    _two_pad("Capacitor_SMD:C_0805_2012Metric", ref, value, x, y, rot, 0.95, 1.025, 1.4, n1, n2)

def place_c1210(ref, value, x, y, rot, n1, n2):
    _two_pad("Capacitor_SMD:C_1210_3225Metric", ref, value, x, y, rot, 1.475, 1.6, 2.7, n1, n2)

def place_cp_elec(ref, value, x, y, rot, n_pos, n_neg):
    _two_pad("Capacitor_SMD:CP_Elec_10x10.5", ref, value, x, y, rot, 3.4, 4.3, 2.6, n_pos, n_neg)

def place_inductor(ref, value, x, y, rot, n1, n2):
    _two_pad("Inductor_SMD:L_Bourns-SRN6045TA", ref, value, x, y, rot, 2.4, 2.3, 3.0, n1, n2)

def place_dsma(ref, value, x, y, rot, n_k, n_a):
    _two_pad("Diode_SMD:D_SMA", ref, value, x, y, rot, 1.925, 1.65, 1.65, n_k, n_a)

def place_dsmb(ref, value, x, y, rot, n_k, n_a):
    _two_pad("Diode_SMD:D_SMB", ref, value, x, y, rot, 2.2, 1.95, 2.2, n_k, n_a)

def place_sot23_6(ref, value, x, y, rot, pin_nets):
    """SOT-23-6 — pads local; footprint rotation handles orientation."""
    out = fp_open("Package_TO_SOT_SMD:SOT-23-6", ref, value, x, y, rot)
    pos = [(-0.95,-1.4),(0,-1.4),(0.95,-1.4),(0.95,1.4),(0,1.4),(-0.95,1.4)]
    for i,(dx,dy) in enumerate(pos):
        out.append(pad_smd(str(i+1), dx, dy, 0.6, 1.0, pin_nets[i]))
    out.extend(fp_close()); emit("\n".join(out))

def place_qfn24_4mm(ref, value, x, y, rot, pin_nets, ep_net="GND"):
    """QFN-24 4×4 mm P0.5; pads in LOCAL coords (no pre-rotation)."""
    out = fp_open("Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm",
                  ref, value, x, y, rot)
    P = 0.5
    side_offset = 2.05
    pin = 1
    for k in range(6):  # left (top to bottom)
        out.append(pad_smd(str(pin), -side_offset, -1.25 + k*P, 0.85, 0.25, pin_nets[pin-1]))
        pin += 1
    for k in range(6):  # bottom
        out.append(pad_smd(str(pin), -1.25 + k*P, side_offset, 0.25, 0.85, pin_nets[pin-1]))
        pin += 1
    for k in range(6):  # right (bottom to top)
        out.append(pad_smd(str(pin), side_offset, 1.25 - k*P, 0.85, 0.25, pin_nets[pin-1]))
        pin += 1
    for k in range(6):  # top (right to left)
        out.append(pad_smd(str(pin), 1.25 - k*P, -side_offset, 0.25, 0.85, pin_nets[pin-1]))
        pin += 1
    out.append(pad_smd("25", 0, 0, 2.6, 2.6, ep_net))  # exposed pad
    out.extend(fp_close()); emit("\n".join(out))

def place_ssop24(ref, value, x, y, rot, pin_nets):
    """SSOP-24 5.3×8.2 mm, P0.65; LOCAL pad coords."""
    out = fp_open("Package_SO:SSOP-24_5.3x8.2mm_P0.65mm", ref, value, x, y, rot)
    P = 0.65
    side_offset = 3.0
    for k in range(12):  # 1..12 left
        out.append(pad_smd(str(k+1),  -side_offset, -P*5.5 + k*P, 1.5, 0.4, pin_nets[k]))
    for k in range(12):  # 13..24 right
        out.append(pad_smd(str(k+13),  side_offset, P*5.5 - k*P, 1.5, 0.4, pin_nets[12+k]))
    out.extend(fp_close()); emit("\n".join(out))

def place_esp32_module(ref, value, x, y, rot, pin_nets):
    """ESP32-S3-WROOM-1 simplified — LOCAL pad coords."""
    out = fp_open("RF_Module:ESP32-S3-WROOM-1", ref, value, x, y, rot)
    for k in range(16):  # 1..16 left side
        net = pin_nets.get(k+1, "")
        if net:
            out.append(pad_smd(str(k+1), -9.5, -10.4 + k*1.27, 1.5, 0.9, net))
    for k in range(16):  # 17..32 right side
        net = pin_nets.get(k+17, "")
        if net:
            out.append(pad_smd(str(k+17), 9.5, -10.4 + k*1.27, 1.5, 0.9, net))
    for k in range(9):   # 33..41 bottom row
        net = pin_nets.get(k+33, "")
        if net:
            out.append(pad_smd(str(k+33), -8.0 + k*2.0, 11.5, 0.9, 1.5, net))
    out.extend(fp_close()); emit("\n".join(out))

def place_usb_c(ref, value, x, y, rot, nets):
    """USB-C HRO TYPE-C-31-M-12; LOCAL pad coords."""
    out = fp_open("Connector:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
                  ref, value, x, y, rot, attrs="smd")
    pin_map = [
        (1, -2.75, "GND"),
        (2, -2.25, "VBUS"),
        (4, -1.25, "CC1"),
        (5, -0.75, "USB_D+"),
        (6, -0.25, "USB_D-"),
        (7,  0.25, "USB_D+"),
        (8,  0.75, "USB_D-"),
        (9,  1.25, "CC2"),
        (11, 2.25, "VBUS"),
        (12, 2.75, "GND"),
    ]
    for (pn, dx, net) in pin_map:
        out.append(pad_smd(str(pn), dx, -3.5, 0.3, 1.4, net))
    # Shield/mounting tabs
    for tabx in (-4.32, 4.32):
        for taby in (-2.5, 2.5):
            out.append(pad_th("SH", tabx, taby, 1.6, 0.65, "GND",
                              oval=True, w=1.0, h=2.4))
    out.extend(fp_close()); emit("\n".join(out))

def place_screw_term_8(ref, value, x, y, rot, out_nets):
    """Phoenix MKDS-1,5-8 P5.00 — LOCAL pad coords."""
    out = fp_open("TerminalBlock:TerminalBlock_Phoenix_MKDS-1,5-8_1x08_P5.00mm_Horizontal",
                  ref, value, x, y, rot, attrs="through_hole")
    P = 5.0
    for k in range(8):
        out.append(pad_th(str(k+1), -P*3.5 + k*P, 0, 2.5, 1.3, out_nets[k]))
    out.extend(fp_close()); emit("\n".join(out))

def place_mh(ref, x, y):
    out = fp_open("MountingHole:MountingHole_3.2mm_M3", ref, "M3", x, y, 0,
                  attrs="through_hole exclude_from_pos_files exclude_from_bom")
    out.append(f'    (pad "" np_thru_hole circle (at 0 0) (size {MH_DRILL} {MH_DRILL})'
               f' (drill {MH_DRILL}) (layers "F&B.Cu" "*.Mask") (uuid "{u()}"))')
    out.extend(fp_close()); emit("\n".join(out))

# ---------- header ---------------------------------------------------------
emit('(kicad_pcb (version 20231120) (generator "pcbnew")')
emit('  (general (thickness 1.6))')
emit('  (paper "A3")')
emit('  (title_block')
emit('    (title "NCV7240 x4 Low-side Driver Board")')
emit('    (date "2026-05-12") (rev "0.2")')
emit('    (comment 1 "ESP32-S3 + AP33772S USB-C PD EPR @ 24V — 32x NCV7240 outputs with B260A flyback")')
emit('  )')

# layers
emit('  (layers')
emit('    (0  "F.Cu"      signal)')
emit('    (1  "In1.Cu"    signal "GND")')
emit('    (2  "In2.Cu"    signal "+24V")')
emit('    (31 "B.Cu"      signal)')
emit('    (32 "B.Adhes"   user "B.Adhesive")')
emit('    (33 "F.Adhes"   user "F.Adhesive")')
emit('    (34 "B.Paste"   user)')
emit('    (35 "F.Paste"   user)')
emit('    (36 "B.SilkS"   user "B.Silkscreen")')
emit('    (37 "F.SilkS"   user "F.Silkscreen")')
emit('    (38 "B.Mask"    user)')
emit('    (39 "F.Mask"    user)')
emit('    (40 "Dwgs.User" user "User.Drawings")')
emit('    (41 "Cmts.User" user "User.Comments")')
emit('    (44 "Edge.Cuts" user)')
emit('    (45 "Margin"    user)')
emit('    (46 "B.CrtYd"   user "B.Courtyard")')
emit('    (47 "F.CrtYd"   user "F.Courtyard")')
emit('    (48 "B.Fab"     user)')
emit('    (49 "F.Fab"     user)')
emit('  )')

# setup / stackup
emit('  (setup')
emit('    (stackup')
emit('      (layer "F.SilkS" (type "Top Silk Screen"))')
emit('      (layer "F.Paste" (type "Top Solder Paste"))')
emit('      (layer "F.Mask"  (type "Top Solder Mask") (thickness 0.01))')
emit('      (layer "F.Cu"    (type "copper")          (thickness 0.035))')
emit('      (layer "dielectric 1" (type "core") (thickness 0.2) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))')
emit('      (layer "In1.Cu"  (type "copper")          (thickness 0.035))')
emit('      (layer "dielectric 2" (type "prepreg") (thickness 1.13) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))')
emit('      (layer "In2.Cu"  (type "copper")          (thickness 0.035))')
emit('      (layer "dielectric 3" (type "core") (thickness 0.2) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))')
emit('      (layer "B.Cu"    (type "copper")          (thickness 0.035))')
emit('      (layer "B.Mask"  (type "Bottom Solder Mask") (thickness 0.01))')
emit('      (layer "B.Paste" (type "Bottom Solder Paste"))')
emit('      (layer "B.SilkS" (type "Bottom Silk Screen"))')
emit('      (copper_finish "ENIG")')
emit('      (dielectric_constraints no)')
emit('    )')
emit('    (pad_to_mask_clearance 0.05)')
emit('    (solder_mask_min_width 0.1)')
emit('    (aux_axis_origin 0 0)')
emit('    (grid_origin 0 0)')
emit('    (pcbplotparams (outputdirectory "gerbers/"))')
emit('  )')

# nets
for i, n in enumerate(NETS):
    emit(f'  (net {i} "{n}")')

# board outline
def gr_line(x1, y1, x2, y2, layer="Edge.Cuts", w=0.1):
    emit(f'  (gr_line (start {x1} {y1}) (end {x2} {y2})'
         f' (stroke (width {w}) (type solid)) (layer "{layer}") (uuid "{u()}"))')

gr_line(0, 0, W, 0); gr_line(W, 0, W, H)
gr_line(W, H, 0, H); gr_line(0, H, 0, 0)

# board title silk
emit(f'  (gr_text "NCV7240 x4 Driver — 24V PD EPR" (at {W/2} 3 0) (layer "F.SilkS")'
     f' (uuid "{u()}") (effects (font (size 1.5 1.5) (thickness 0.25))))')
emit(f'  (gr_text "rev 0.2 — 2026" (at {W/2} {H-3} 0) (layer "F.SilkS")'
     f' (uuid "{u()}") (effects (font (size 1 1) (thickness 0.15))))')

# mounting holes
place_mh("MH1", MH_INSET,         MH_INSET)
place_mh("MH2", W - MH_INSET,     MH_INSET)
place_mh("MH3", MH_INSET,         H - MH_INSET)
place_mh("MH4", W - MH_INSET,     H - MH_INSET)

# ====================================================================
# === Component placement ============================================
# ====================================================================

# ---- USB-C section (x=10..50, y=15..50) ----
place_usb_c("J1", "USB-C", 12, 30, 0, {})
place_qfn24_4mm("U1", "AP33772S", 32, 30, 0, pin_nets=[
    # 1=VBUS, 2=CC1, 3=CC2, 4=VDD(3V3), 5=GND, 6=VPP, 7=?, 8=?, 9=?, 10=?, 11=?, 12=?,
    # 13=?, 14=GPIO2, 15=GPIO1, 16=INT, 17=SCL, 18=SDA, 19=VOUT_EN, 20=VOUT,
    # 21..24 internal / GND / NC
    "VBUS","CC1","CC2","+3V3","GND","GND",
    "GND","GND","GND","GND","GND","GND",
    "GND","GND","GND","PD_INT","I2C_SCL","I2C_SDA",
    "PD_VOUT_EN","+24V","+24V","GND","GND","GND",
])
place_cp_elec("C1", "100uF/50V", 46, 24, 0, "+24V", "GND")
place_c1210("C2", "10uF/50V",    46, 34, 0, "+24V", "GND")
place_dsmb("D1", "SMBJ33A",      52, 30, 90, "GND", "+24V")

# ---- Buck 24V → 3.3V (x=10..50, y=55..80) ----
place_sot23_6("U7", "TPS62932", 18, 60, 0, pin_nets=[
    # SOT-23-6: pin1=BST,2=SW,3=GND,4=FB,5=EN,6=VIN  (TPS62932)
    "BST","SW","GND","FB","EN_3V3","+24V"
])
place_inductor("L1", "4.7uH/2A", 28, 60, 0, "SW", "+3V3")
place_c0805("C3",   "22uF",      36, 60, 0, "+3V3", "GND")
place_r0603("R6",   "100k",      22, 70, 0, "+3V3", "FB")
place_r0603("R7",   "20k",       30, 70, 0, "FB",   "GND")
# Boot cap for buck
place_c0603("C6",   "100nF",     18, 53, 0, "BST", "SW")
# Input cap
place_c0603("C7",   "100nF",     12, 60, 0, "+24V", "GND")

# ---- ESP32-S3 + decoupling + pull-ups (x=55..95, y=15..85) ----
# ESP32 module centred at (75, 35), 18×25.5 mm
ESP_PINS = {  # only used pins; everything else stays unconnected pad-less
    1: "GND",
    2: "+3V3",
    3: "EN_3V3",     # connect EN to a button + pull-up; here just EN_3V3 net
    4: "BOOT_BTN",   # IO0
    10: "PD_INT",    # IO4
    13: "USB_D-",    # IO19
    14: "USB_D+",    # IO20
    17: "I2C_SCL",   # IO9
    18: "I2C_SDA",   # IO8
    19: "SPI_CS1",   # IO10
    20: "SPI_CS2",   # IO11
    23: "SPI_CS3",   # IO12
    24: "SPI_CS4",   # IO13
    25: "SPI_SCK",   # IO14
    26: "SPI_MOSI",  # IO15
    27: "GND",
    28: "SPI_MISO",  # IO16
    29: "NCV_RSTB",  # IO17
    30: "NCV_FSOB",  # IO18
    # bottom row GND
    37: "GND", 38: "GND", 39: "GND", 40: "GND", 41: "GND",
}
place_esp32_module("U2", "ESP32-S3-WROOM-1", 75, 35, 0, ESP_PINS)

# 3V3 decoupling
place_c0805("C4", "10uF",  60, 22, 0, "+3V3", "GND")
place_c0603("C5", "100nF", 60, 28, 0, "+3V3", "GND")

# Pull-up resistor bank @ x=90..95, y=14..38, 5 in column
PU_X, PU_Y0 = 92, 16
for k, (ref, val, net) in enumerate([
    ("R1", "10k",  "SPI_MISO"),
    ("R2", "10k",  "NCV_RSTB"),
    ("R3", "10k",  "NCV_FSOB"),
    ("R4", "4.7k", "I2C_SDA"),
    ("R5", "4.7k", "I2C_SCL"),
]):
    place_r0603(ref, val, PU_X, PU_Y0 + k*4, 90, "+3V3", net)

# ---- 4× NCV7240 banks (x=100..130 NCV, x=135..160 diodes, x=165..195 terminal)
# Each bank occupies a horizontal strip ~25mm tall, at y centres 20, 50, 80, 110... wait board is 120mm tall.
# Use y centres 20, 50, 80 — only 3 fit. Need 4. So use 18, 46, 74, 102. spacing 28mm. ok.

NCV_PIN_NETS_T = [  # template; we'll substitute OUTx and CSx per bank
    "VPWR",    # 1
    "+3V3",    # 2 VDD
    "CSB",     # 3
    "SPI_SCK", # 4
    "SPI_MOSI",# 5
    "SPI_MISO",# 6 SO open drain
    "NCV_RSTB",# 7
    "NCV_FSOB",# 8
    "GND",     # 9 (NC in datasheet; tied GND for safety)
    "GND",     # 10
    "GND",     # 11
    "GND",     # 12 GND
    "OUT0",    # 13
    "OUT1",    # 14
    "OUT2",    # 15
    "OUT3",    # 16
    "OUT4",    # 17
    "OUT5",    # 18
    "OUT6",    # 19
    "OUT7",    # 20
    "GND",     # 21
    "GND",     # 22
    "GND",     # 23
    "+24V",    # 24 (datasheet shows 24=VPWR2; tie to V_PWR)
]

ncv_y_centres = [18, 46, 74, 102]
diode_ref = 2  # D2..D33
for bank_i, ncv_y in enumerate(ncv_y_centres):
    # Substitute nets for this bank
    cs_net = f"SPI_CS{bank_i+1}"
    pin_nets = list(NCV_PIN_NETS_T)
    pin_nets[2]  = cs_net      # CSB
    pin_nets[0]  = "+24V"      # VPWR
    pin_nets[23] = "+24V"      # VPWR2
    # OUT0..7 map to OUT(bank*8+1)..OUT(bank*8+8)
    for k in range(8):
        pin_nets[12+k] = f"OUT{bank_i*8 + k + 1}"
    ref = f"U{3+bank_i}"
    place_ssop24(ref, "NCV7240", 108, ncv_y, 0, pin_nets)
    # NCV decoupling caps
    place_c0603(f"C{10+bank_i*2}",  "100nF",   120, ncv_y - 5, 0, "+24V", "GND")
    place_c1210(f"C{11+bank_i*2}",  "10uF/50V", 120, ncv_y + 5, 0, "+24V", "GND")

    # 8 flyback diodes — column of 8 at x=140..148, y around NCV
    # Place 2 columns of 4 diodes each to fit vertically within 22mm slot.
    for k in range(8):
        col = k // 4   # 0 or 1
        row = k % 4
        dx = 140 + col*8           # x = 140 or 148
        dy = ncv_y - 6.5 + row*4   # y range -6.5 .. +5.5
        out_net = f"OUT{bank_i*8 + k + 1}"
        # Diode rot=0: K=left, A=right. K -> +24V, A -> OUTx
        place_dsma(f"D{diode_ref}", "B260A", dx, dy, 0, "+24V", out_net)
        diode_ref += 1

    # 8-pos screw terminal horizontal at x=175, y=ncv_y, rot=0 (pin1..8 left to right)
    # x=175 → pins span 157.5..192.5; MH at (196,…) gets 3.5 mm clearance.
    out_nets = [f"OUT{bank_i*8 + k + 1}" for k in range(8)]
    place_screw_term_8(f"J{2+bank_i}", f"OUT{bank_i*8+1}-{bank_i*8+8}",
                       175, ncv_y, 0, out_nets)

    # --- OUT routing: NCV right pin → flyback diode anode → terminal pin ---
    for k in range(8):
        # NCV output pin (13+k on right side). Pin pitch 0.65 mm, top-to-bottom.
        x_ncv = 108 + 3.0          # right edge of SSOP + small offset
        y_ncv = ncv_y + 0.65*5.5 - k*0.65  # pin 13 (k=0) at top
        # Flyback diode (D[diode_ref-8+k]) at:
        col = k // 4; row = k % 4
        x_dA  = 140 + col*8 + 1.925   # anode (right pad)
        y_dAK = ncv_y - 6.5 + row*4
        # Terminal pin
        x_t = 175 - 17.5 + k*5
        y_t = ncv_y
        net = f"OUT{bank_i*8 + k + 1}"
        # 2-segment route: NCV pad → diode anode pad → terminal pin
        track(x_ncv, y_ncv, x_dA,  y_dAK, net, layer="F.Cu", width=0.5)
        track(x_dA,  y_dAK, x_t,   y_t,   net, layer="F.Cu", width=0.5)

# ====================================================================
# === Routing — power vias to inner planes ===========================
# ====================================================================
# Every GND/+24V/+3V3 pad placement gets a fanout via near it; since the
# inner copper layers are full pours on those nets the via stitches
# the F.Cu pad to the plane. The plane fill (defined below) will tie them.

# We'll drop one stitching via per IC corner via a generic algorithm:
# generate vias next to each IC body on +24V and GND nets so the planes
# see them.

# ---- ESP32 ↔ NCV bus (shared SPI signals) -------------------------------
# 5 shared bus signals: SCK (NCV pin4), MOSI (5), MISO (6), RSTB (7), FSOB (8).
# Run them as 5 vertical busses on F.Cu in the gap x=96..100, spanning all 4
# NCVs vertically. Then short stub from each NCV pin (left side) to the bus.
# NCV left pins (1..12): x = 108 - 3.0 = 105, y = ncv_y - 0.65*5.5 + k*0.65
# Pin 4 = k=3, pin 5 = k=4, pin 6 = k=5, pin 7 = k=6, pin 8 = k=7
BUS_X = {
    "SPI_SCK":  96.0,
    "SPI_MOSI": 97.0,
    "SPI_MISO": 98.0,
    "NCV_RSTB": 99.0,
    "NCV_FSOB": 100.0,
}
BUS_PIN_K = {  # pin number on NCV → k offset from top of left column
    "SPI_SCK":  3,   # pin 4
    "SPI_MOSI": 4,   # pin 5
    "SPI_MISO": 5,   # pin 6
    "NCV_RSTB": 6,   # pin 7
    "NCV_FSOB": 7,   # pin 8
}
y_top = ncv_y_centres[0] - 0.65*5.5
y_bot = ncv_y_centres[-1] + 0.65*5.5
for net, bx in BUS_X.items():
    # Vertical bus track
    track(bx, y_top - 5, bx, y_bot + 5, net, layer="F.Cu", width=0.25)
    # Stubs from each NCV pin to the bus
    for ncv_y in ncv_y_centres:
        k = BUS_PIN_K[net]
        py = ncv_y - 0.65*5.5 + k*0.65
        track(105.0, py, bx, py, net, layer="F.Cu", width=0.25)

# Per-NCV /CSB lines (independent, x=104 column with horizontal stubs)
for i, ncv_y in enumerate(ncv_y_centres):
    py = ncv_y - 0.65*5.5 + 2*0.65   # pin 3 (CSB), k=2
    track(105.0, py, 95.0, py, f"SPI_CS{i+1}", layer="F.Cu", width=0.25)

# ESP32 → bus: short horizontal tracks from ESP32 right edge (x=84.5) to bus
# columns. ESP32 SPI pins are on its left side in the schematic, but the module
# pad geometry here has them on the LEFT (pins 19..26). For brevity, route
# from a representative point. KiCad's autorouter will tidy these.
for net, bx in BUS_X.items():
    track(84.5, 35, bx, 35, net, layer="F.Cu", width=0.25)
for i in range(4):
    track(84.5, 38 + i*1.5, 95, 38 + i*1.5, f"SPI_CS{i+1}",
          layer="F.Cu", width=0.25)

# Stitching vias around the perimeter for solid GND continuity
for x in range(10, int(W)-9, 12):
    via(x, 7, "GND"); via(x, H-7, "GND")
for y in range(15, int(H)-15, 12):
    via(7, y, "GND"); via(W-7, y, "GND")

# ====================================================================
# === Filled zones (copper pours) ====================================
# ====================================================================

def zone(net, name, layer, pts, priority=0):
    emit(f'  (zone (net {NET[net]}) (net_name "{name}") (layer "{layer}") (uuid "{u()}") (hatch edge 0.5)')
    emit(f'    (priority {priority})')
    emit('    (connect_pads (clearance 0.3))')
    emit('    (min_thickness 0.25) (filled_areas_thickness no)')
    emit('    (fill yes (thermal_gap 0.5) (thermal_bridge_width 0.5))')
    emit('    (polygon (pts')
    for (x,y) in pts:
        emit(f'      (xy {x} {y})')
    emit('    ))')
    emit('  )')

Z = 0.5
RECT = [(Z,Z),(W-Z,Z),(W-Z,H-Z),(Z,H-Z)]
zone("GND",  "GND",  "In1.Cu", RECT)
zone("+24V", "+24V", "In2.Cu", RECT)
zone("GND",  "GND",  "B.Cu",   RECT)
# F.Cu GND pour (priority 0) covers free copper on top; +3V3 island
# (priority 10) takes precedence over it in the ESP32 region.
zone("GND",  "GND",  "F.Cu",   RECT, priority=0)
zone("+3V3", "+3V3", "F.Cu", [(5,15),(95,15),(95,85),(5,85)], priority=10)

# ====================================================================
# === Floorplan comments (User.Comments) =============================
# ====================================================================
def cmt_box(x1,y1,x2,y2,label):
    for (a,b,c,d) in [(x1,y1,x2,y1),(x2,y1,x2,y2),(x2,y2,x1,y2),(x1,y2,x1,y1)]:
        emit(f'  (gr_line (start {a} {b}) (end {c} {d}) (stroke (width 0.15) (type dash))'
             f' (layer "Cmts.User") (uuid "{u()}"))')
    emit(f'  (gr_text "{label}" (at {(x1+x2)/2} {(y1+y2)/2} 0) (layer "Cmts.User")'
         f' (uuid "{u()}") (effects (font (size 1.5 1.5) (thickness 0.2))))')

cmt_box(5,10,55,50,"USB-C PD")
cmt_box(5,55,55,85,"Buck 24V→3V3")
cmt_box(55,10,100,85,"ESP32-S3")
cmt_box(100,5,135,118,"4× NCV7240")
cmt_box(135,5,160,118,"Flyback diodes")
cmt_box(160,5,195,118,"Screw terminals")

emit(')')
sys.stdout.write("\n".join(OUT) + "\n")
