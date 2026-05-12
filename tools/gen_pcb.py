#!/usr/bin/env python3
"""
Generate ncv7240-driver.kicad_pcb — skeleton 4-layer PCB:
  - 160 x 100 mm board outline on Edge.Cuts
  - 4-layer stackup:  F.Cu  /  GND  /  +24V  /  B.Cu  (1.6 mm FR4)
  - 4 x M3 mounting holes in the corners
  - Floorplan annotations on User.Comments showing intended zones
  - Pre-declared nets and net classes matching the schematic
  - Empty of footprints — run `Tools → Update PCB from Schematic`
    in KiCad to import them from the project's schematic.

Run from the repo root:
    python3 tools/gen_pcb.py > ncv7240-driver.kicad_pcb
"""

import uuid, sys

_uuid_counter = 0
def u():
    global _uuid_counter
    _uuid_counter += 1
    return f"00000000-1111-0000-0000-{_uuid_counter:012x}"

W, H = 160.0, 100.0           # board outline (mm)
MARGIN = 4.0                  # mounting-hole inset from edge
HOLE_DRILL = 3.2              # M3 clearance hole
HOLE_PAD   = 6.0              # mounting pad diameter (annular ring)

OUT = []
OUT.append('(kicad_pcb (version 20231120) (generator "pcbnew")')
OUT.append('  (general (thickness 1.6))')
OUT.append('  (paper "A3")')
OUT.append('  (title_block')
OUT.append('    (title "NCV7240 x4 Low-side Driver Board")')
OUT.append('    (date "2026-05-12") (rev "0.1")')
OUT.append('    (comment 1 "ESP32-S3 + AP33772S USB-C PD EPR @ 24V driving 32 channels")')
OUT.append('  )')

# --- Layers (4-layer signal) ----------------------------------------------
OUT.append('  (layers')
OUT.append('    (0  "F.Cu"      signal)')
OUT.append('    (1  "In1.Cu"    signal "GND")')
OUT.append('    (2  "In2.Cu"    signal "+24V")')
OUT.append('    (31 "B.Cu"      signal)')
OUT.append('    (32 "B.Adhes"   user "B.Adhesive")')
OUT.append('    (33 "F.Adhes"   user "F.Adhesive")')
OUT.append('    (34 "B.Paste"   user)')
OUT.append('    (35 "F.Paste"   user)')
OUT.append('    (36 "B.SilkS"   user "B.Silkscreen")')
OUT.append('    (37 "F.SilkS"   user "F.Silkscreen")')
OUT.append('    (38 "B.Mask"    user)')
OUT.append('    (39 "F.Mask"    user)')
OUT.append('    (40 "Dwgs.User" user "User.Drawings")')
OUT.append('    (41 "Cmts.User" user "User.Comments")')
OUT.append('    (42 "Eco1.User" user "User.Eco1")')
OUT.append('    (43 "Eco2.User" user "User.Eco2")')
OUT.append('    (44 "Edge.Cuts" user)')
OUT.append('    (45 "Margin"    user)')
OUT.append('    (46 "B.CrtYd"   user "B.Courtyard")')
OUT.append('    (47 "F.CrtYd"   user "F.Courtyard")')
OUT.append('    (48 "B.Fab"     user)')
OUT.append('    (49 "F.Fab"     user)')
OUT.append('  )')

# --- Setup / stackup ------------------------------------------------------
OUT.append('  (setup')
OUT.append('    (stackup')
OUT.append('      (layer "F.SilkS"  (type "Top Silk Screen"))')
OUT.append('      (layer "F.Paste"  (type "Top Solder Paste"))')
OUT.append('      (layer "F.Mask"   (type "Top Solder Mask")    (thickness 0.01))')
OUT.append('      (layer "F.Cu"     (type "copper")              (thickness 0.035))')
OUT.append('      (layer "dielectric 1" (type "core")    (thickness 0.2)  (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))')
OUT.append('      (layer "In1.Cu"   (type "copper")              (thickness 0.035))')
OUT.append('      (layer "dielectric 2" (type "prepreg") (thickness 1.13) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))')
OUT.append('      (layer "In2.Cu"   (type "copper")              (thickness 0.035))')
OUT.append('      (layer "dielectric 3" (type "core")    (thickness 0.2)  (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))')
OUT.append('      (layer "B.Cu"     (type "copper")              (thickness 0.035))')
OUT.append('      (layer "B.Mask"   (type "Bottom Solder Mask") (thickness 0.01))')
OUT.append('      (layer "B.Paste"  (type "Bottom Solder Paste"))')
OUT.append('      (layer "B.SilkS"  (type "Bottom Silk Screen"))')
OUT.append('      (copper_finish "ENIG")')
OUT.append('      (dielectric_constraints no)')
OUT.append('    )')
OUT.append('    (pad_to_mask_clearance 0.05)')
OUT.append('    (solder_mask_min_width 0.1)')
OUT.append('    (aux_axis_origin 0 0)')
OUT.append('    (grid_origin 0 0)')
OUT.append('    (pcbplotparams')
OUT.append('      (layerselection 0x00010fc_ffffffff)')
OUT.append('      (plot_on_all_layers_selection 0x0000000_00000000)')
OUT.append('      (disableapertmacros false)')
OUT.append('      (usegerberextensions false) (usegerberattributes true)')
OUT.append('      (usegerberadvancedattributes true) (creategerberjobfile true)')
OUT.append('      (dashed_line_dash_ratio 12.0) (dashed_line_gap_ratio 3.0)')
OUT.append('      (svgprecision 4) (plotframeref false) (viasonmask false)')
OUT.append('      (mode 1) (useauxorigin false) (hpglpennumber 1)')
OUT.append('      (hpglpenspeed 20) (hpglpendiameter 15.0) (dxfpolygonmode true)')
OUT.append('      (dxfimperialunits true) (dxfusepcbnewfont true) (psnegative false)')
OUT.append('      (psa4output false) (plotreference true) (plotvalue true)')
OUT.append('      (plotinvisibletext false) (sketchpadsonfab false)')
OUT.append('      (subtractmaskfromsilk false) (outputformat 1) (mirror false)')
OUT.append('      (drillshape 1) (scaleselection 1) (outputdirectory "gerbers/")')
OUT.append('    )')
OUT.append('  )')

# --- Nets (placeholders; the real net list comes from the schematic via
#         Tools → Update PCB from Schematic) --------------------------------
NETS = [
    "", "GND", "+24V", "+3V3", "VBUS",
    "CC1", "CC2",
    "I2C_SDA", "I2C_SCL", "PD_INT", "PD_VOUT_EN",
    "SPI_SCK", "SPI_MOSI", "SPI_MISO",
    "SPI_CS1", "SPI_CS2", "SPI_CS3", "SPI_CS4",
    "NCV_RSTB", "NCV_FSOB",
    "RST_BTN", "BOOT_BTN", "EN_3V3",
    "USB_D+", "USB_D-",
]
for k in range(1, 33):
    NETS.append(f"OUT{k}")
for i, n in enumerate(NETS):
    OUT.append(f'  (net {i} "{n}")')

# --- Edge.Cuts: rectangular outline ---------------------------------------
def gr_line(x1, y1, x2, y2, layer="Edge.Cuts", width=0.1):
    return (f'  (gr_line (start {x1} {y1}) (end {x2} {y2})'
            f' (stroke (width {width}) (type solid)) (layer "{layer}") (uuid "{u()}"))')

OUT.append(gr_line(0, 0, W, 0))
OUT.append(gr_line(W, 0, W, H))
OUT.append(gr_line(W, H, 0, H))
OUT.append(gr_line(0, H, 0, 0))

# --- Mounting holes (M3 NPTH at corners) ----------------------------------
def mount_hole(x, y, ref):
    return f'''  (footprint "MountingHole:MountingHole_3.2mm_M3"
    (layer "F.Cu") (uuid "{u()}") (at {x} {y})
    (attr through_hole exclude_from_pos_files exclude_from_bom)
    (property "Reference" "{ref}" (at 0 -4 0) (unlocked yes) (layer "F.SilkS")
      (uuid "{u()}") (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "M3" (at 0 4 0) (unlocked yes) (layer "F.Fab")
      (uuid "{u()}") (effects (font (size 1 1) (thickness 0.15))))
    (property "Footprint" "MountingHole:MountingHole_3.2mm_M3" (at 0 0 0) hide
      (layer "F.Fab") (uuid "{u()}") (effects (font (size 1.27 1.27) (thickness 0.15))))
    (fp_circle (center 0 0) (end {HOLE_PAD/2} 0) (stroke (width 0.05) (type solid))
      (fill none) (layer "F.CrtYd") (uuid "{u()}"))
    (pad "" np_thru_hole circle (at 0 0) (size {HOLE_DRILL} {HOLE_DRILL})
      (drill {HOLE_DRILL}) (layers "F&B.Cu" "*.Mask")
      (clearance 0.1) (zone_connect 0) (uuid "{u()}"))
  )'''

OUT.append(mount_hole(MARGIN,     MARGIN,     "MH1"))
OUT.append(mount_hole(W - MARGIN, MARGIN,     "MH2"))
OUT.append(mount_hole(MARGIN,     H - MARGIN, "MH3"))
OUT.append(mount_hole(W - MARGIN, H - MARGIN, "MH4"))

# --- Floorplan annotations on User.Comments -------------------------------
def cmt_box(x1, y1, x2, y2, label):
    o = []
    for (a, b, c, d) in [(x1,y1,x2,y1),(x2,y1,x2,y2),(x2,y2,x1,y2),(x1,y2,x1,y1)]:
        o.append(f'  (gr_line (start {a} {b}) (end {c} {d}) (stroke (width 0.15) (type dash)) (layer "Cmts.User") (uuid "{u()}"))')
    cx, cy = (x1+x2)/2, (y1+y2)/2
    o.append(f'  (gr_text "{label}" (at {cx} {cy} 0) (layer "Cmts.User") (uuid "{u()}")')
    o.append('    (effects (font (size 1.5 1.5) (thickness 0.2)) (justify center)))')
    return "\n".join(o)

# Floorplan zones (left-to-right): USB-C/PD, Buck+ESP32, 4xNCV+terminals,
# Flyback diode field at the bottom under the NCV/terminal column.
OUT.append(cmt_box( 4,  6,  44, 60, "USB-C PD\\n(J1, U1, C1/C2, D1)"))
OUT.append(cmt_box(44,  6,  90, 36, "Buck 24V→3V3\\n(U7, L1, C3, R6/R7)"))
OUT.append(cmt_box(44, 36,  90, 96, "ESP32-S3\\n(U2, C4/C5, R1..R5)"))
OUT.append(cmt_box(90,  6, 130, 96, "4× NCV7240\\n(U3..U6 + decoupling)"))
OUT.append(cmt_box(130, 6, 156, 96, "Screw terminals\\n(J2..J5, 32 outputs)"))
OUT.append(cmt_box(90, 60, 156, 96, "Flyback diode field\\n(D2..D33, B260A, K→+24V)"))

# Board label
OUT.append(f'  (gr_text "NCV7240 x4 Driver — 24V PD EPR" (at {W/2} 3 0) (layer "F.SilkS") (uuid "{u()}")')
OUT.append('    (effects (font (size 1.5 1.5) (thickness 0.25)) (justify center)))')
OUT.append(f'  (gr_text "rev 0.1 — 2026" (at {W/2} {H-3} 0) (layer "F.SilkS") (uuid "{u()}")')
OUT.append('    (effects (font (size 1 1) (thickness 0.15)) (justify center)))')

# --- Tear-drop GND zones on inner layer + 24V plane ------------------------
def zone(net_idx, net_name, layer, pts):
    o = []
    o.append(f'  (zone (net {net_idx}) (net_name "{net_name}") (layer "{layer}") (uuid "{u()}") (hatch edge 0.5)')
    o.append('    (connect_pads (clearance 0.3))')
    o.append('    (min_thickness 0.25) (filled_areas_thickness no)')
    o.append('    (fill yes (thermal_gap 0.5) (thermal_bridge_width 0.5))')
    o.append('    (polygon (pts')
    for (x,y) in pts:
        o.append(f'      (xy {x} {y})')
    o.append('    ))')
    o.append('  )')
    return "\n".join(o)

# Inset zones 0.5 mm from board edge
Z = 0.5
gnd_pts  = [(Z,Z),(W-Z,Z),(W-Z,H-Z),(Z,H-Z)]
p24_pts  = [(Z,Z),(W-Z,Z),(W-Z,H-Z),(Z,H-Z)]
OUT.append(zone(NETS.index("GND"),  "GND",  "In1.Cu", gnd_pts))
OUT.append(zone(NETS.index("+24V"), "+24V", "In2.Cu", p24_pts))
# Also a top-side GND pour (typical practice for return paths under SPI bus)
OUT.append(zone(NETS.index("GND"),  "GND",  "B.Cu",   gnd_pts))

OUT.append(')')

sys.stdout.write("\n".join(OUT) + "\n")
