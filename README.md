# Speed Radar

DIY street speed radar with Home Assistant integration. Uses the HLK-LD2415H 24GHz Doppler radar module connected to an ESP32 (WT32-ETH02) via Ethernet with PoE power.

## Features

- Real-time vehicle speed detection (1-240 km/h)
- Direction detection (approaching/leaving)
- 180m detection range
- **Pedestrian filtering** - ignores speeds below configurable threshold (default 15 km/h)
- **Vehicle counting** - tracks total, approaching, and leaving vehicles
- **Speed statistics** - average speed and max speed
- Home Assistant integration via ESPHome
- PoE powered for easy outdoor installation
- Weatherproof enclosure design
- Statistics auto-reset at midnight

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

## Pedestrian Filtering

The radar detects all moving objects, including pedestrians. To filter these out:

| Movement Type | Typical Speed |
|---------------|---------------|
| Walking | 3-6 km/h |
| Jogging | 8-12 km/h |
| Cycling | 15-25 km/h |
| Vehicles | 20+ km/h |

The default `min_speed_threshold` is set to **15 km/h**, which filters out pedestrians and most cyclists. You can adjust this in the ESPHome config or at runtime via Home Assistant.

## Installation

1. Copy `esphome/speed-radar.yaml` to your ESPHome config directory
2. Copy `esphome/components/hlk_ld2415h/` folder to your ESPHome components directory
3. Update credentials in `secrets.yaml`
4. Flash to your WT32-ETH02
5. Add to Home Assistant

## Home Assistant Entities

### Sensors

| Entity | Type | Description |
|--------|------|-------------|
| `sensor.speed_radar_vehicle_speed` | Speed | Current detected speed (km/h) |
| `sensor.speed_radar_vehicle_speed_mph` | Speed | Current speed in mph |
| `sensor.speed_radar_vehicle_count` | Counter | Total vehicles detected today |
| `sensor.speed_radar_approaching_count` | Counter | Vehicles approaching today |
| `sensor.speed_radar_leaving_count` | Counter | Vehicles leaving today |
| `sensor.speed_radar_average_speed` | Speed | Average speed of all vehicles (km/h) |
| `sensor.speed_radar_average_speed_mph` | Speed | Average speed in mph |
| `sensor.speed_radar_max_speed` | Speed | Highest speed detected today (km/h) |
| `sensor.speed_radar_max_speed_mph` | Speed | Max speed in mph |

### Text Sensors

| Entity | Values | Description |
|--------|--------|-------------|
| `text_sensor.speed_radar_direction` | Approaching / Leaving | Vehicle direction |

### Binary Sensors

| Entity | Description |
|--------|-------------|
| `binary_sensor.speed_radar_vehicle_detected` | On when vehicle actively detected |

### Controls

| Entity | Type | Description |
|--------|------|-------------|
| `button.speed_radar_restart` | Button | Restart the device |
| `button.speed_radar_reset_statistics` | Button | Reset all counters and stats |
| `number.speed_radar_min_speed_threshold` | Number | Adjust pedestrian filter (km/h) |

## Configuration Options

In the ESPHome YAML, you can configure:

```yaml
hlk_ld2415h:
  id: radar
  uart_id: radar_uart
  min_speed_threshold: 15.0  # Filter speeds below this (km/h)
  max_speed_threshold: 200.0 # Filter speeds above this (km/h)
```

## Example Automations

See `home_assistant/automations.yaml` for examples:
- Flash warning light when speeding
- Log all detections
- Send notification for excessive speed
- Daily summary notification
- Trigger camera recording for speeders

## Enclosure Tips

- Use IP66 rated ABS enclosure (radar passes through 2-3mm ABS)
- Mount angled so rain runs off radar-facing side
- Add rain hood/visor above radar area
- Use IP68 cable glands for PoE cable entry
- Include waterproof vent to prevent condensation
- Optional: conformal coat PCBs for extra protection

## License

MIT
