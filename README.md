# Speed Radar

DIY street speed radar with Home Assistant integration. Uses the HLK-LD2415H 24GHz Doppler radar module connected to an ESP32 (WT32-ETH02) via Ethernet with PoE power.

## Features

- Real-time vehicle speed detection (1-240 km/h)
- Direction detection (approaching/leaving)
- 180m detection range
- Home Assistant integration via ESPHome
- PoE powered for easy outdoor installation
- Weatherproof enclosure design

## Hardware

| Component | Purpose | Price |
|-----------|---------|-------|
| HLK-LD2415H | 24GHz Doppler radar | ~$20 |
| WT32-ETH02 + Adapter | ESP32 with Ethernet | ~$8 |
| PoE Splitter 48V→12V | Power from PoE | ~$1 |
| LM2596 Buck Converter | 12V→5V for ESP32 | ~$2 |
| IP66 Junction Box | Waterproof enclosure | ~$12 |
| Cable Glands + Vent | Weatherproofing | ~$6 |
| **Total** | | **~$50** |

## Wiring

```
PoE Switch
    │
    ▼
┌─────────────┐
│ PoE Splitter│ 48V → 12V
└──────┬──────┘
       │ 12V
       ├────────────────► HLK-LD2415H VCC (9-24V)
       │
       ▼
┌─────────────┐
│ Buck Conv.  │ 12V → 5V
└──────┬──────┘
       │ 5V
       ▼
   WT32-ETH02 VIN

Radar → ESP32:
- Radar TX  → GPIO5 (RX)
- Radar RX  → GPIO17 (TX)
- GND       → GND (common)
```

## Radar Protocol

The HLK-LD2415H outputs simple ASCII at 9600 baud:

| Output | Meaning |
|--------|---------|
| `V+045.2\r\n` | Vehicle approaching at 45.2 km/h |
| `V-032.8\r\n` | Vehicle leaving at 32.8 km/h |

## Installation

1. Copy `esphome/speed-radar.yaml` to your ESPHome config directory
2. Copy `esphome/components/hlk_ld2415h/` folder to your ESPHome components directory
3. Update WiFi/network credentials in the YAML
4. Flash to your WT32-ETH02
5. Add to Home Assistant

## Home Assistant Entities

| Entity | Type | Description |
|--------|------|-------------|
| `sensor.speed_radar_vehicle_speed` | Number | Current speed in km/h |
| `sensor.speed_radar_vehicle_speed_mph` | Number | Current speed in mph |
| `text_sensor.speed_radar_direction` | Text | "Approaching" or "Leaving" |
| `binary_sensor.speed_radar_vehicle_detected` | Motion | On when vehicle detected |
| `sensor.speed_radar_max_speed_today` | Number | Highest speed today |
| `sensor.speed_radar_detection_count` | Counter | Vehicles detected today |

## Example Automations

See `home_assistant/automations.yaml` for examples:
- Flash warning light when speeding
- Log all detections
- Send notification for excessive speed
- Track statistics

## Enclosure Tips

- Use IP66 rated ABS enclosure (radar passes through 2-3mm ABS)
- Mount angled so rain runs off radar-facing side
- Add rain hood/visor above radar area
- Use IP68 cable glands for PoE cable entry
- Include waterproof vent to prevent condensation
- Optional: conformal coat PCBs for extra protection

## License

MIT
