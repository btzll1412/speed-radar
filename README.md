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

### Multi-Site Deployment
- **Remote push via HTTPS** - Deploy radars across different networks
- **Webhook-based** - Secure communication with unique webhook IDs
- **Cloudflare Tunnel support** - No port forwarding needed
- **Instant detection alerts** - Push immediately on vehicle detection
- **Periodic sync** - Push stats every 30 seconds

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

### Prerequisites

- ESPHome installed (via Home Assistant add-on or standalone)
- Home Assistant with ESPHome integration
- USB-to-Serial adapter (for initial flash only)
- PoE-capable network switch or injector

### Step 1: Prepare Files

1. Copy `esphome/speed-radar.yaml` to your ESPHome config directory
2. Copy `esphome/components/hlk_ld2415h/` folder to your ESPHome components directory
3. Create `secrets.yaml` with your credentials (see `secrets.yaml.example`):

```yaml
# secrets.yaml
api_encryption_key: "your-32-character-base64-key-here"
ota_password: "your-ota-password"

# MQTT for instant communication (required for multi-site)
mqtt_broker: "192.168.1.100"      # Your HA IP or external hostname
mqtt_port: "1883"
mqtt_username: "radar"
mqtt_password: "your-mqtt-password"
```

Generate an API key with: `openssl rand -base64 32`

### Step 2: Assemble Hardware

1. **Mount PoE Splitter** in enclosure
   - Connect PoE input from Ethernet cable
   - 12V output goes to radar and buck converter

2. **Wire Buck Converter**
   - Input: 12V from PoE splitter
   - Output: 5V to WT32-ETH02 VIN

3. **Connect Radar to ESP32**
   ```
   HLK-LD2415H    →    WT32-ETH02
   ─────────────────────────────
   VCC (9-24V)    →    12V from PoE splitter
   GND            →    GND (common ground)
   TX             →    GPIO5 (RX)
   RX             →    GPIO17 (TX)
   ```

4. **Verify all ground connections are common**

### Step 3: Initial Flash

1. Connect WT32-ETH02 to computer via USB-to-Serial adapter:
   ```
   USB-Serial    →    WT32-ETH02
   ───────────────────────────
   TX            →    RX (GPIO3)
   RX            →    TX (GPIO1)
   GND           →    GND
   3.3V          →    3.3V (or use external 5V to VIN)
   ```

2. Put ESP32 in flash mode:
   - Hold BOOT button
   - Press and release EN button
   - Release BOOT button

3. Flash using ESPHome:
   ```bash
   esphome run speed-radar.yaml
   ```

4. Select the serial port when prompted

### Step 4: Deploy & Connect

1. Disconnect USB adapter
2. Connect Ethernet cable from PoE switch to WT32-ETH02
3. Device will boot and connect to your network
4. Check your router/DHCP for the device IP

### Step 5: Add to Home Assistant

1. Go to **Settings → Devices & Services**
2. ESPHome should auto-discover "Speed Radar"
3. Click **Configure** and enter your API encryption key
4. All entities will appear automatically

## Usage Guide

### Initial Configuration

After adding to Home Assistant, configure these settings:

1. **Set Your Speed Limit**
   - Go to `number.speed_radar_speed_limit`
   - Set your street's posted speed limit (e.g., 50 km/h)

2. **Adjust Pedestrian Filter**
   - Go to `number.speed_radar_min_speed_threshold`
   - Default 15 km/h filters out pedestrians and joggers
   - Lower to 10 km/h to capture fast cyclists
   - Raise to 20 km/h for vehicle-only detection

3. **Set Direction Filter** (optional)
   - Go to `select.speed_radar_direction_filter`
   - "Both" - detect traffic in both directions
   - "Approaching Only" - only inbound traffic
   - "Leaving Only" - only outbound traffic

### Calibration

#### Angle Compensation

If your radar isn't mounted perpendicular to the road:

1. Have a friend drive past at a known speed (use their speedometer)
2. Note the speed displayed by the radar
3. Calculate the mounting angle using the formula:
   ```
   angle = arccos(displayed_speed / actual_speed)
   ```
4. Set `number.speed_radar_angle_compensation` to this angle

**Example:** If actual speed is 50 km/h but radar shows 43 km/h:
- cos(angle) = 43/50 = 0.86
- angle ≈ 30°

#### Speed Offset

For fine-tuning after angle compensation:

1. Compare radar readings to a known reference (GPS speedometer)
2. If radar reads 2 km/h low, set `number.speed_radar_speed_offset` to +2
3. If radar reads 3 km/h high, set offset to -3

### Understanding the Data

#### Real-Time Sensors

| Sensor | What It Tells You |
|--------|-------------------|
| Vehicle Speed | Current speed of detected vehicle |
| Direction | Whether vehicle is approaching or leaving |
| Vehicle Detected | Binary on/off for motion detection |

#### Daily Statistics (reset at midnight)

| Sensor | What It Tells You |
|--------|-------------------|
| Vehicle Count | Total vehicles detected today |
| Average Speed | Mean speed of all vehicles |
| Max Speed | Fastest vehicle today |
| Speeder Count | Vehicles exceeding speed limit |
| Violation % | Percentage of speeders |
| Worst Speeder | Highest amount OVER the limit |

#### Traffic Engineering

| Sensor | What It Tells You |
|--------|-------------------|
| 85th Percentile | Speed 85% of vehicles stay under |
| Peak Hour | Busiest hour (0-23) |
| Peak Hour Count | Vehicles during peak hour |

### Creating Dashboards

Example Lovelace card for your dashboard:

```yaml
type: entities
title: Street Speed Monitor
entities:
  - entity: sensor.speed_radar_vehicle_speed
    name: Current Speed
  - entity: text_sensor.speed_radar_direction
    name: Direction
  - entity: sensor.speed_radar_vehicle_count
    name: Vehicles Today
  - entity: sensor.speed_radar_average_speed
    name: Average Speed
  - entity: sensor.speed_radar_speeder_count
    name: Speeders Today
  - entity: sensor.speed_radar_violation_percentage
    name: Violation Rate
  - entity: sensor.speed_radar_percentile_85_speed
    name: 85th Percentile
```

### Useful Automations

#### Flash Light for Speeders

```yaml
automation:
  - alias: "Flash warning light for speeders"
    trigger:
      - platform: numeric_state
        entity_id: sensor.speed_radar_vehicle_speed
        above: 55  # 5 over limit
    action:
      - service: light.turn_on
        target:
          entity_id: light.warning_flasher
        data:
          flash: short
```

#### Daily Summary Notification

```yaml
automation:
  - alias: "Daily traffic summary"
    trigger:
      - platform: time
        at: "23:55:00"
    action:
      - service: notify.mobile_app
        data:
          title: "Daily Traffic Report"
          message: >
            Vehicles: {{ states('sensor.speed_radar_vehicle_count') }}
            Average: {{ states('sensor.speed_radar_average_speed') }} km/h
            Speeders: {{ states('sensor.speed_radar_speeder_count') }}
            ({{ states('sensor.speed_radar_violation_percentage') }}%)
            Peak hour: {{ states('sensor.speed_radar_peak_hour') }}:00
```

### Maintenance

- **Statistics reset automatically at midnight**
- Use **Reset Statistics** button to manually reset counters
- **OTA updates**: Flash new firmware over Ethernet (no USB needed)
- Check **Uptime** sensor to verify device stability

### Troubleshooting

| Issue | Solution |
|-------|----------|
| No detections | Check UART wiring (TX↔RX crossed correctly) |
| Erratic readings | Increase min_speed_threshold, check for reflections |
| Speed too low | Adjust angle_compensation for mounting angle |
| Speed too high | Lower angle_compensation or add negative offset |
| Counts too high | Increase vehicle_gap_time to separate vehicles |
| Device offline | Check PoE power, Ethernet connection |

### OTA Updates

After initial USB flash, update over the network:

```bash
esphome run speed-radar.yaml
# Select the network option when prompted
```

Or use Home Assistant's ESPHome dashboard for one-click updates

## Multi-Site / Remote Deployment

Deploy multiple radars across your neighborhood using the **Speed Radar Hub** add-on with **instant MQTT communication**. Updates appear in Home Assistant immediately - just like VoIP phones connected to a server.

### How It Works

```
[Your House]                           [Remote Locations]
┌──────────────────────┐               ┌─────────────────┐
│ Home Assistant       │               │ Speed Radar 2   │
│                      │               │ (Neighbor WiFi) │
│ ┌──────────────────┐ │               └────────┬────────┘
│ │ Speed Radar Hub  │ │                        │
│ │    Add-on        │ │                        │ MQTT
│ │  - Web UI        │ │                        │ (instant)
│ │  - Config push   │ │                        │
│ └────────┬─────────┘ │               ┌────────┴────────┐
│          │           │               │ Speed Radar 3   │
│          ▼           │               │ (Mobile hotspot)│
│ ┌──────────────────┐ │               └────────┬────────┘
│ │  MQTT Broker     │◄├───────────────────────┘
│ │  (Mosquitto)     │ │  All radars connect to same broker
│ └────────┬─────────┘ │
│          │           │
│   MQTT Discovery     │
│          ▼           │
│  [HA Entities auto-  │
│   created for each   │
│   radar]             │
└──────────────────────┘
```

### Instant Communication

| Direction | How It Works | Latency |
|-----------|--------------|---------|
| **Radar → HA** | MQTT publish on every detection | Instant (~50ms) |
| **HA → Radar** | MQTT publish on config change | Instant (~50ms) |

This is the same architecture used by VoIP phones - always-connected, bidirectional, instant updates.

### Speed Radar Hub Add-on Features

| Feature | Description |
|---------|-------------|
| **Instant updates** | MQTT pub/sub for real-time communication |
| **Instant config sync** | Change settings in UI → applies to radar instantly |
| **Auto HA integration** | Sensors created via MQTT discovery |
| **Web dashboard** | View all radars, stats, readings |
| **Historical data** | SQLite stores readings for analysis |
| **One-click radar setup** | Click "Add Radar" → configure MQTT |

### Step 1: Install Mosquitto MQTT Broker

1. Go to **Settings → Add-ons → Add-on Store**
2. Search for "Mosquitto broker" and click **Install**
3. Go to the add-on's **Configuration** tab
4. Add a user/password for your radars (or use HA credentials)
5. Start the add-on

### Step 2: Install Speed Radar Hub Add-on

1. Go to **Settings → Add-ons → Add-on Store**
2. Click the menu (⋮) → **Repositories**
3. Add: `https://github.com/btzll1412/speed-radar`
4. Click **Add** → Close
5. Find "Speed Radar Hub" in the store and click **Install**
6. Go to **Configuration** tab → Enter your Mosquitto credentials
7. Start the add-on and open the Web UI

### Step 3: Configure the ESP32

Add MQTT settings to your `secrets.yaml`:

```yaml
# MQTT Broker (for instant communication)
mqtt_broker: "your-home-assistant.duckdns.org"  # or IP for local
mqtt_port: "1883"
mqtt_username: "radar"
mqtt_password: "your-mqtt-password"
```

For remote sites, the broker must be accessible from the internet (via Cloudflare Tunnel or port forwarding).

### Step 4: Add Radar in Hub UI

1. Open Speed Radar Hub from the sidebar
2. Click **Add Radar**
3. Enter a name (e.g., "Main Street") - this must match the ESP's device name
4. The radar will automatically connect via MQTT

### Step 5: Verify in Home Assistant

Entities are auto-created via MQTT discovery:
- `sensor.main_street_speed`
- `sensor.main_street_vehicle_count`
- `sensor.main_street_average_speed`
- `binary_sensor.main_street_vehicle_detected`
- ...and more

Settings changed in the Hub UI apply to the radar **instantly**.

### Security

| Layer | Protection |
|-------|------------|
| **MQTT Auth** | Username/password per radar |
| **TLS/SSL** | Encrypt MQTT with TLS (port 8883) |
| **Cloudflare Tunnel** | Expose MQTT securely without port forwarding |
| **Ingress** | Add-on UI only accessible through HA |

### Exposing MQTT for Remote Sites

For radars outside your home network to connect, your MQTT broker must be accessible:

**Option 1: Cloudflare Tunnel (Recommended)**
```bash
# Add TCP tunnel for MQTT
cloudflared tunnel route tcp 1883
```

**Option 2: Port Forward**
- Forward port 1883 (or 8883 for TLS) to your Home Assistant IP
- Use TLS for security

**Option 3: Cloud MQTT Broker**
- Use a cloud broker like HiveMQ Cloud, CloudMQTT, or EMQX Cloud
- All radars and the add-on connect to the cloud broker
- No port forwarding needed

Update `secrets.yaml` on remote radars with the external address:
```yaml
mqtt_broker: "your-home.duckdns.org"  # External address
mqtt_port: "8883"                      # TLS port
```

### Adding WiFi for Remote Sites

For locations without Ethernet, add WiFi to your config:

```yaml
# Add this to speed-radar.yaml for WiFi-only sites
wifi:
  ssid: "NeighborNetworkName"
  password: "NeighborPassword"

  # Fallback hotspot for initial setup
  ap:
    ssid: "SpeedRadar-Setup"
    password: "setuppassword"

# Comment out or remove the ethernet section
# ethernet:
#   type: LAN8720
#   ...
```

### MQTT Entities

| Entity | Type | Description |
|--------|------|-------------|
| `switch.speed_radar_mqtt_enabled` | switch | Enable/disable MQTT communication |

MQTT settings are configured in `secrets.yaml` and applied at boot.

### Cost for Remote Sites

| Option | Hardware | Internet |
|--------|----------|----------|
| Neighbor with WiFi | $0 | Free (ask nicely!) |
| Cellular hotspot | $20-50 | $10-20/mo |
| Starlink | $500+ | $120/mo |

Most practical: Ask neighbors to share WiFi access. Data usage is minimal (<1 MB/day).

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
├── repository.yaml                  # HA add-on repository config
├── speed_radar_hub/                 # Speed Radar Hub HA Add-on
│   ├── config.yaml                  # Add-on configuration
│   ├── Dockerfile
│   ├── run.sh
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py                  # FastAPI application
│   │   ├── database.py              # SQLite database
│   │   └── mqtt.py                  # MQTT communication
│   └── templates/                   # Web UI templates
├── docs/
│   ├── WIRING.md                    # Detailed wiring guide
│   └── INSTALLATION.md              # Step-by-step installation
├── esphome/
│   ├── speed-radar.yaml             # Main ESPHome configuration
│   ├── secrets.yaml.example         # Template for credentials
│   └── components/
│       └── hlk_ld2415h/             # Custom radar component
│           ├── __init__.py
│           ├── sensor.py
│           ├── text_sensor.py
│           ├── binary_sensor.py
│           ├── hlk_ld2415h.h
│           └── hlk_ld2415h.cpp
└── home_assistant/
    ├── automations.yaml             # Example automations
    └── dashboard_card.yaml          # Example Lovelace card
```

## License

MIT
