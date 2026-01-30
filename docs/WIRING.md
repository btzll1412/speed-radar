# Wiring Guide

## Overview

This guide covers wiring the HLK-LD2415H radar to the WT32-ETH02 with PoE power.

## Components

- WT32-ETH02 (ESP32 with Ethernet)
- HLK-LD2415H (24GHz Doppler radar)
- PoE Splitter (48V → 12V, 802.3af)
- LM2596 Buck Converter (12V → 5V)

## Pin Connections

### WT32-ETH02 Pinout

```
           ┌─────────────────┐
     3V3 ──┤ 1            40 ├── GND
      EN ──┤ 2            39 ├── IO35
     IO36 ──┤ 3            38 ├── IO34
     IO39 ──┤ 4            37 ├── IO33
     IO34 ──┤ 5            36 ├── IO32
     IO35 ──┤ 6            35 ├── IO25
     IO32 ──┤ 7            34 ├── IO26
     IO33 ──┤ 8            33 ├── IO27
     IO25 ──┤ 9            32 ├── IO14
     IO26 ──┤ 10           31 ├── IO12
     IO27 ──┤ 11           30 ├── GND
     IO14 ──┤ 12           29 ├── IO13
     IO12 ──┤ 13           28 ├── IO15
     GND ──┤ 14           27 ├── IO2
     IO13 ──┤ 15           26 ├── IO4
  RXD/IO3 ──┤ 16           25 ├── IO0 (ETH CLK)
  TXD/IO1 ──┤ 17           24 ├── 5V
      5V ──┤ 18           23 ├── IO16 (ETH PWR)
     GND ──┤ 19           22 ├── IO17 ← RADAR TX
     IO5 ──┤ 20           21 ├── IO18 (ETH MDIO)
           └─────────────────┘
            ↑
         RADAR RX
```

### HLK-LD2415H Pinout

```
┌─────────────────────┐
│  HLK-LD2415H        │
│                     │
│  VCC (9-24V) ───────┼── Red wire
│  GND ───────────────┼── Black wire
│  TX ────────────────┼── Yellow/White wire
│  RX ────────────────┼── Green wire
│                     │
└─────────────────────┘
```

## Complete Wiring Diagram

```
                    PoE Switch (802.3af)
                           │
                           │ Cat5e/6
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  WEATHERPROOF ENCLOSURE                                      │
│                                                              │
│   ┌────────────────────┐                                     │
│   │    PoE Splitter    │                                     │
│   │    48V → 12V       │                                     │
│   │                    │                                     │
│   │  DATA OUT ─────────┼─────────► WT32-ETH02 RJ45           │
│   │                    │                                     │
│   │  12V+ (Red) ───────┼──┬───────► HLK-LD2415H VCC          │
│   │                    │  │                                  │
│   │                    │  │  ┌────────────────┐              │
│   │                    │  └──► Buck Converter │              │
│   │                    │     │  12V → 5V      │              │
│   │                    │     │                │              │
│   │                    │     │  5V OUT ───────┼─► WT32 5V    │
│   │                    │     └────────────────┘              │
│   │                    │                                     │
│   │  GND (Black) ──────┼────────────────────────► Common GND │
│   └────────────────────┘                                     │
│                                                              │
│                                                              │
│   HLK-LD2415H              WT32-ETH02                        │
│   ┌──────────┐             ┌──────────┐                      │
│   │          │             │          │                      │
│   │ VCC ◄────┼── 12V ──────┤          │                      │
│   │          │             │          │                      │
│   │ GND ◄────┼── GND ──────┤ GND      │                      │
│   │          │             │          │                      │
│   │ TX  ─────┼─────────────► IO5      │ (ESP32 RX)           │
│   │          │             │          │                      │
│   │ RX  ◄────┼─────────────┤ IO17     │ (ESP32 TX)           │
│   │          │             │          │                      │
│   └──────────┘             │ 5V ◄─────┼── From Buck          │
│        ▲                   │          │                      │
│        │                   └──────────┘                      │
│   FACING ROAD                                                │
│                                                              │
│   [IP68 Cable Gland]              [Waterproof Vent]          │
└──────────────────────────────────────────────────────────────┘
```

## Wire Colors (Typical)

| Connection | Wire Color | Notes |
|------------|------------|-------|
| 12V+ | Red | From PoE splitter |
| GND | Black | Common ground |
| 5V | Red/Orange | From buck converter to ESP32 |
| Radar TX → ESP RX | Yellow | Data from radar |
| Radar RX ← ESP TX | Green | Commands to radar (optional) |

## Step-by-Step Wiring

### 1. Prepare the Buck Converter

Before connecting anything:
1. Connect buck converter input to a 12V source (or use multimeter)
2. Adjust the potentiometer until output reads exactly **5.0V**
3. Mark the potentiometer position

### 2. Power Wiring

1. **PoE Splitter 12V+** → Split to:
   - HLK-LD2415H VCC (direct 12V)
   - Buck Converter VIN (input)

2. **Buck Converter 5V OUT** → WT32-ETH02 5V pin

3. **All GNDs connected together**:
   - PoE Splitter GND
   - Buck Converter GND
   - HLK-LD2415H GND
   - WT32-ETH02 GND

### 3. Data Wiring

| From | To | Purpose |
|------|-----|---------|
| Radar TX | ESP32 GPIO5 | Speed data from radar |
| Radar RX | ESP32 GPIO17 | Commands to radar (optional) |

### 4. Ethernet

Connect PoE Splitter data output to WT32-ETH02 RJ45 port.

## Important Notes

### Power

- The radar needs 9-24V DC. 12V from PoE splitter is perfect.
- The ESP32 needs 5V. Use a buck converter, NOT the radar's voltage!
- Always adjust buck converter BEFORE connecting ESP32.
- Total power draw: ~2W (well under 802.3af 15W limit)

### Signal Levels

- HLK-LD2415H uses 3.3V TTL logic
- WT32-ETH02 uses 3.3V GPIO
- No level shifter needed!

### Grounding

- All grounds MUST be connected together
- Use star grounding if possible (all grounds meet at one point)
- Poor grounding = noisy readings

### UART Settings

- Baud rate: 9600
- Data bits: 8
- Stop bits: 1
- Parity: None

## Enclosure Mounting

### Radar Orientation

```
    ROAD
    ═════════════════►  Traffic flow

         ┌─────────┐
         │ RADAR   │  ← Mount at 15-30° angle
         │ ◉◉◉◉◉◉ │    facing oncoming traffic
         └─────────┘
              │
         ┌────┴────┐
         │ ENCLOSURE│
         └─────────┘
              │
           [POLE]
```

### Mounting Tips

1. Mount 1-2 meters above ground
2. Angle radar 15-30° toward oncoming traffic
3. Keep radar face clear (no metal in front)
4. Ensure enclosure drains away from radar side
5. Add rain hood above radar area if exposed to weather

## Testing

1. Power on and check:
   - PoE splitter LED (if any)
   - Buck converter output = 5V
   - ESP32 power LED

2. Check ESPHome logs for:
   ```
   [I][hlk_ld2415h:] Speed: XX.X km/h, Direction: approaching
   ```

3. Walk in front of radar - should detect ~5 km/h

4. Test with vehicle at known speed
