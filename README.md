# NCV7240 x4 — ESP32 + USB-C PD EPR (24 V) Driver Board

A KiCad 8 project for a compact controller board that:

- Negotiates **24 V** from a USB-C **PD 3.1 EPR** source via the **AP33772S** sink controller.
- Hosts an **ESP32-S3** MCU for Wi-Fi/BT control, configuration and host comms.
- Drives **32 low-side switched outputs** at 24 V using **4 × NCV7240** octal low-side drivers (SPI-controlled).

> Status: skeleton — project files, design rules, net classes and BOM are in place. The schematic (`ncv7240-driver.kicad_sch`) and PCB (`ncv7240-driver.kicad_pcb`) are intentionally empty placeholders ready to be populated in KiCad 8.

---

## 1. System architecture

```
       USB-C (PD 3.1 EPR, up to 28 V / 5 A)
           │
           ▼
   ┌────────────────┐   I²C   ┌──────────────────────┐
   │   AP33772S     │◀───────▶│   ESP32-S3-WROOM-1   │
   │  PD EPR sink   │  (CFG)  │  (Wi-Fi / BT / USB)  │
   └──────┬─────────┘         └───────┬──────────────┘
          │ VBUS_OUT = 24 V           │ SPI (CS x4, SCK, MOSI, MISO)
          │                           │ + RSTB, /FSO IRQ
          ▼                           ▼
   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
   │  NCV7240 #1  │   │  NCV7240 #2  │   │  NCV7240 #3  │   │  NCV7240 #4  │
   │ 8 ch low-side│   │ 8 ch low-side│   │ 8 ch low-side│   │ 8 ch low-side│
   └──────┬───────┘   └──────┬───────┘   └──────┬───────┘   └──────┬───────┘
          ▼                  ▼                  ▼                  ▼
       OUT1..8            OUT9..16          OUT17..24          OUT25..32
       (loads sink to GND; common rail = 24 V)
```

- The AP33772S handles all CC negotiation/PPS/EPR; the ESP32 just configures the
  request profile over I²C and reads VBUS / status telemetry.
- The 4 NCV7240s share SCK/MOSI/MISO/RSTB/SI on a single SPI bus; each has its
  own **/CSB** from the ESP32. Output enable is per-channel via SPI control word.

## 2. Bill of materials (core)

| Ref       | Part                          | Pkg          | Notes                                    |
|-----------|-------------------------------|--------------|------------------------------------------|
| U1        | AP33772S                      | QFN-24       | USB-C PD 3.1 EPR sink controller         |
| U2        | ESP32-S3-WROOM-1-N8R8         | SMD module   | 8 MB flash, 8 MB PSRAM                   |
| U3..U6    | NCV7240ADQR2G                 | SSOP-24      | Octal low-side driver, SPI               |
| J1        | USB-C receptacle (EPR rated)  | TID/16-pin   | 5 A continuous, EPR cable required >3 A  |
| D1        | TVS for VBUS (e.g. SMBJ33A)   | SMB          | 33 V standoff                            |
| L1        | 10 µH @ 3 A ferrite/inductor  | 1210         | VBUS LC filter (optional)                |
| C_BULK    | 100 µF / 50 V × 2             | electrolytic | VBUS bulk on 24 V rail                   |
| FB1..FB4  | Ferrite bead, 600 Ω @ 100 MHz | 0603         | Per-NCV7240 V_PWR decoupling             |
| U7        | LDO/buck 24 V → 3.3 V (e.g. MP2451 or TPS62932) | SOT-23-6 | ≥500 mA for ESP32 peaks    |
| U8        | (optional) 3.3 V LDO          | SOT-23-5     | Clean rail for analog if needed          |
| Q_GATE    | P-MOSFET (e.g. DMP3098L)      | SOT-23       | Reverse-polarity / VBUS gate (optional)  |
| R_CS      | 1 % shunts                    | 0805         | If per-bank current sensing is desired   |

Plus per-channel flyback diodes/TVS if driving inductive loads (the NCV7240
has internal active clamp, but external TVS to 24 V rail is recommended for
solenoids/relays).

## 3. Net classes / design rules

Defined in `ncv7240-driver.kicad_pro`:

| Net class    | Track | Clearance | Vias        | Used for                              |
|--------------|-------|-----------|-------------|---------------------------------------|
| Default      | 0.25  | 0.20      | 0.6 / 0.3   | logic, SPI, I²C                       |
| Power_24V    | 0.80  | 0.40      | 0.9 / 0.4   | VBUS, 24 V plane feeds, OUTx pours    |
| USB_PD       | 0.40  | 0.25      | 0.7 / 0.3   | CC1/CC2, VBUS sense, D+/D- (90 Ω diff)|

## 4. Pin assignment (ESP32-S3 → NCVs / AP33772S)

| ESP32 pin | Net           | Goes to                                  |
|-----------|---------------|------------------------------------------|
| GPIO10    | SPI_CS1       | NCV7240 #1 /CSB                          |
| GPIO11    | SPI_CS2       | NCV7240 #2 /CSB                          |
| GPIO12    | SPI_CS3       | NCV7240 #3 /CSB                          |
| GPIO13    | SPI_CS4       | NCV7240 #4 /CSB                          |
| GPIO14    | SPI_SCK       | all NCV7240 SCLK                         |
| GPIO15    | SPI_MOSI      | all NCV7240 SI                           |
| GPIO16    | SPI_MISO      | all NCV7240 SO (open-drain, ext. pull-up)|
| GPIO17    | NCV_RSTB      | all NCV7240 /RSTB (active low, pull-up)  |
| GPIO18    | NCV_FSO       | all NCV7240 /FSO fault flag (IRQ)        |
| GPIO8     | I2C_SDA       | AP33772S SDA (+ 4.7 kΩ pull-up to 3V3)   |
| GPIO9     | I2C_SCL       | AP33772S SCL (+ 4.7 kΩ pull-up to 3V3)   |
| GPIO4     | PD_INT        | AP33772S /INT                            |
| EN        | reset btn     | per ESP32 standard wiring                |
| GPIO0     | boot btn      | per ESP32 standard wiring                |

> Avoid the strapping pins (GPIO0/3/45/46) and USB pins (19/20) for the
> dedicated nets above — already accounted for.

## 5. NCV7240 wiring notes

- Tie all `V_PWR` pins to the 24 V rail through individual ferrite beads
  + 100 nF + 10 µF local decoupling per IC.
- All `GND` pins tied to the solid 24 V-return ground pour.
- `SO` is open-drain; place one 10 kΩ pull-up to 3V3 on the shared MISO net.
- `/RSTB` shared and pulled up to 3V3 (10 kΩ); ESP32 drives low to reset all.
- `/FSO` shared open-drain fault flag → ESP32 IRQ, pulled up to 3V3.
- Daisy-chained SPI is **not** used here (independent /CSB per device is
  simpler and lets the ESP32 talk to any device individually at full clock).
- Each OUTx pad gets a generous copper pour and a screw terminal or 2.54 mm
  header per channel. For inductive loads, place a TVS/clamp diode from OUTx
  to the 24 V rail close to the load connector.

## 6. AP33772S notes

- Connect CC1/CC2 directly to the USB-C receptacle CC pins (no Rd needed —
  the AP33772S provides the sink termination).
- VBUS sense via internal divider; place 100 µF + 10 µF + 100 nF bulk on
  VBUS_OUT after the controller's NMOS pass switch.
- Pull `VPP` / `VDD` decoupling per datasheet (1 µF on VDD, 100 nF on VPP).
- The MCU configures the requested PDO (request 24 V/3 A EPR profile) via I²C
  at boot. Until configured the AP33772S falls back to its NVM defaults — flash
  the NVM with the desired default PDO request before deployment if you want
  the rail to come up without the ESP32.
- Add a SMBJ33A TVS across VBUS_OUT to GND.

## 7. Layout guidance

- 4-layer stack recommended: **Signal / GND / 24 V / Signal**.
- Keep the 24 V rail as a continuous pour on an inner layer; stitch with vias
  near each NCV7240 V_PWR pin.
- USB-C D+/D- routed as a 90 Ω differential pair, length-matched, away from
  the switching loads. (For PD-only operation D± are unused but route them
  anyway so the port can carry USB 2.0 data if desired.)
- Place the AP33772S close to the USB-C connector; keep the VBUS path short
  and wide (≥ 60 mil for 5 A).
- ESP32 antenna keep-out: leave ≥ 15 mm clearance and no copper under the
  antenna section of the module.
- Per-channel output traces: 0.8 mm minimum for 0.5 A loads, scale up for
  more. Add 2× thermal-relief pads at each NCV7240 exposed pad.

## 8. Files

```
ncv7240-driver/
├── .gitignore
├── README.md
├── fp-lib-table
├── sym-lib-table
├── ncv7240-driver.kicad_pro   # KiCad 8 project, design rules + net classes
├── ncv7240-driver.kicad_sch   # schematic (empty — to be drawn in Eeschema)
└── ncv7240-driver.kicad_pcb   # PCB     (empty — to be drawn in Pcbnew)
```

Open `ncv7240-driver.kicad_pro` in **KiCad 8.0 or newer**.

## 9. License

Hardware: CERN-OHL-S v2 (recommended) — adjust to your needs.
