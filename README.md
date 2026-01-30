# Speed Radar

DIY street speed radar with Home Assistant integration. Uses the HLK-LD2415H 24GHz Doppler radar module connected to an ESP32 (WT32-ETH02) via Ethernet with PoE power.

## Features

### Core Detection
- Real-time vehicle speed detection (1-240 km/h)
- Direction detection (approaching/leaving)
- 180m detection range
- ~11 readings per second

### Filtering
- **Pedestrian filtering** - ignores speeds below configurable threshold (default 15 km/h)
- **Noise filtering** - ignores speeds above max threshold (default 200 km/h)
- **Direction filtering** - detect both, approaching only, or leaving only

### Statistics
- **Vehicle counting** - total, approaching, and leaving counts
- **Speed statistics** - average speed, max speed
- **Speed limit tracking** - speeder count, violation percentage, worst speeder
- **Direction-specific stats** - separate averages for approaching vs leaving
- **Hourly statistics** - vehicles per hour, peak hour detection
- **85th percentile speed** - traffic engineering metric

### Calibration
- **Angle compensation** - correct for mounting angle (cosine correction)
- **Speed offset** - fine-tune readings with additive offset

### Integration
- Home Assistant integration via ESPHome
- All settings adjustable from HA without reflashing
- Statistics auto-reset at midnight
- PoE powered for easy outdoor installation

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

## Installation

1. Copy `esphome/speed-radar.yaml` to your ESPHome config directory
2. Copy `esphome/components/hlk_ld2415h/` folder to your ESPHome components directory
3. Create `secrets.yaml` from `secrets.yaml.example`
4. Flash to your WT32-ETH02
5. Add to Home Assistant

## Home Assistant Entities

### Speed Sensors

| Entity | Unit | Description |
|--------|------|-------------|
| `sensor.speed_radar_vehicle_speed` | km/h | Current detected speed |
| `sensor.speed_radar_vehicle_speed_mph` | mph | Current speed in mph |
| `sensor.speed_radar_average_speed` | km/h | Average speed of all vehicles |
| `sensor.speed_radar_average_speed_mph` | mph | Average speed in mph |
| `sensor.speed_radar_max_speed` | km/h | Highest speed today |

### Vehicle Counts

| Entity | Description |
|--------|-------------|
| `sensor.speed_radar_vehicle_count` | Total vehicles detected today |
| `sensor.speed_radar_approaching_count` | Vehicles approaching |
| `sensor.speed_radar_leaving_count` | Vehicles leaving |

### Speed Limit Violations

| Entity | Unit | Description |
|--------|------|-------------|
| `sensor.speed_radar_speeder_count` | count | Vehicles exceeding speed limit |
| `sensor.speed_radar_violation_percentage` | % | Percentage of vehicles speeding |
| `sensor.speed_radar_worst_speeder` | km/h | Highest amount OVER the limit |

### Direction-Specific Stats

| Entity | Unit | Description |
|--------|------|-------------|
| `sensor.speed_radar_avg_speed_approaching` | km/h | Average speed of approaching traffic |
| `sensor.speed_radar_avg_speed_leaving` | km/h | Average speed of leaving traffic |

### Hourly Statistics

| Entity | Description |
|--------|-------------|
| `sensor.speed_radar_current_hour_count` | Vehicles detected this hour |
| `sensor.speed_radar_current_hour_avg_speed` | Average speed this hour |
| `sensor.speed_radar_peak_hour` | Busiest hour of the day (0-23) |
| `sensor.speed_radar_peak_hour_count` | Vehicle count during peak hour |

### Traffic Engineering

| Entity | Unit | Description |
|--------|------|-------------|
| `sensor.speed_radar_percentile_85_speed` | km/h | Speed that 85% of vehicles stay under |

### Other Sensors

| Entity | Description |
|--------|-------------|
| `text_sensor.speed_radar_direction` | "Approaching" or "Leaving" |
| `binary_sensor.speed_radar_vehicle_detected` | On when vehicle actively detected |
| `sensor.speed_radar_uptime` | Device uptime |

### Controls - Numbers

| Entity | Range | Description |
|--------|-------|-------------|
| `number.speed_radar_speed_limit` | 10-120 km/h | Your street's speed limit |
| `number.speed_radar_min_speed_threshold` | 0-50 km/h | Filter out pedestrians/cyclists |
| `number.speed_radar_max_speed_threshold` | 50-300 km/h | Filter out noise/errors |
| `number.speed_radar_vehicle_gap_time` | 1-30 s | Gap to count as new vehicle |
| `number.speed_radar_detection_timeout` | 1-10 s | Motion sensor timeout |
| `number.speed_radar_angle_compensation` | 0-60 deg | Mounting angle correction |
| `number.speed_radar_speed_offset` | -20 to +20 km/h | Fine-tune calibration |

### Controls - Select

| Entity | Options | Description |
|--------|---------|-------------|
| `select.speed_radar_direction_filter` | Both / Approaching Only / Leaving Only | Filter by direction |

### Controls - Buttons

| Entity | Description |
|--------|-------------|
| `button.speed_radar_restart` | Restart the device |
| `button.speed_radar_reset_statistics` | Reset all counters and stats |

## Configuration Options

In the ESPHome YAML, you can set initial values:

```yaml
hlk_ld2415h:
  id: radar
  uart_id: radar_uart
  min_speed_threshold: 15.0   # Ignore below this (filters pedestrians)
  max_speed_threshold: 200.0  # Ignore above this (filters noise)
  speed_limit: 50.0           # Your street's speed limit
  direction_filter: both      # Options: both, approaching, leaving
  angle_compensation: 0.0     # Mounting angle in degrees
  speed_offset: 0.0           # Calibration offset in km/h
```

All settings can be changed from Home Assistant at runtime without reflashing.

## Pedestrian Filtering

The radar detects all moving objects. Filter them by speed:

| Movement Type | Typical Speed | Detected at 15 km/h threshold? |
|---------------|---------------|--------------------------------|
| Walking | 3-6 km/h | No |
| Jogging | 8-12 km/h | No |
| Cycling | 15-25 km/h | Partially |
| Vehicles | 20+ km/h | Yes |

Adjust `min_speed_threshold` based on your needs.

## Angle Compensation

If the radar isn't mounted perpendicular to the road, speeds will read lower than actual due to the cosine effect.

```
Mounting Angle    Speed Reading    Actual Speed
0° (perpendicular)    50 km/h         50 km/h
15°                   48 km/h         50 km/h
30°                   43 km/h         50 km/h
45°                   35 km/h         50 km/h
```

Set `angle_compensation` to your mounting angle and the system will automatically correct readings.

## 85th Percentile Speed

This is a standard traffic engineering metric. It represents the speed that 85% of vehicles travel at or below. Traffic engineers use this to:

- Set appropriate speed limits
- Identify roads where speeding is a problem
- Evaluate effectiveness of traffic calming measures

The system calculates this from the last 200 vehicle readings.

## Example Automations

See `home_assistant/automations.yaml` for examples:

- Flash warning light when speeding
- Log all detections to file
- Send notification for excessive speed
- Daily summary notification
- Trigger camera recording for speeders
- Announce speeders on smart speaker

### Example: Speeder Alert

```yaml
automation:
  - alias: "Speed Radar - Speeder Alert"
    trigger:
      - platform: state
        entity_id: sensor.speed_radar_speeder_count
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.state | int > trigger.from_state.state | int }}"
    action:
      - service: notify.mobile_app
        data:
          title: "Speeder Detected!"
          message: >
            Vehicle going {{ states('sensor.speed_radar_vehicle_speed') }} km/h
            (limit: {{ states('number.speed_radar_speed_limit') }} km/h)
```

## Enclosure Tips

- Use IP66 rated ABS enclosure (radar passes through 2-3mm ABS)
- Mount 1-2 meters above ground
- Angle radar 15-30° toward oncoming traffic
- Add rain hood/visor above radar area
- Use IP68 cable glands for PoE cable entry
- Include waterproof vent to prevent condensation
- Optional: conformal coat PCBs for extra protection

## Radar Protocol

The HLK-LD2415H outputs simple ASCII at 9600 baud:

| Output | Meaning |
|--------|---------|
| `V+045.2\r\n` | Vehicle approaching at 45.2 km/h |
| `V-032.8\r\n` | Vehicle leaving at 32.8 km/h |

## Project Structure

```
speed-radar/
├── README.md
├── docs/
│   ├── WIRING.md              # Detailed wiring guide
│   └── INSTALLATION.md        # Step-by-step installation
├── esphome/
│   ├── speed-radar.yaml       # Main ESPHome configuration
│   ├── secrets.yaml.example   # Template for credentials
│   └── components/
│       └── hlk_ld2415h/       # Custom radar component
│           ├── __init__.py
│           ├── sensor.py
│           ├── text_sensor.py
│           ├── binary_sensor.py
│           ├── hlk_ld2415h.h
│           └── hlk_ld2415h.cpp
└── home_assistant/
    ├── automations.yaml       # Example automations
    └── dashboard_card.yaml    # Example Lovelace card
```

## License

MIT
