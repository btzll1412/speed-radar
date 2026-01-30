# Installation Guide

## Prerequisites

- ESPHome installed (via Home Assistant add-on or standalone)
- Home Assistant (for integration)
- USB-to-Serial adapter (for initial flashing of WT32-ETH02)

## Step 1: Prepare ESPHome Configuration

1. Copy the `esphome/` folder contents to your ESPHome config directory:
   ```bash
   cp -r esphome/components /config/esphome/
   cp esphome/speed-radar.yaml /config/esphome/
   cp esphome/secrets.yaml.example /config/esphome/secrets.yaml
   ```

2. Edit `secrets.yaml` with your credentials:
   ```yaml
   api_encryption_key: "generate-with-openssl-rand-base64-32"
   ota_password: "your-secure-password"
   ```

   Generate an API key:
   ```bash
   openssl rand -base64 32
   ```

## Step 2: Flash the WT32-ETH02

### First-Time Flashing (USB Required)

The WT32-ETH02 needs initial flashing via USB-to-Serial adapter.

1. Connect USB-to-Serial adapter to WT32-ETH02 adapter board:
   - Adapter TX → ETH02 RX
   - Adapter RX → ETH02 TX
   - Adapter GND → ETH02 GND
   - Adapter 5V → ETH02 5V (or use separate power)

2. Put ESP32 in flash mode:
   - Hold BOOT button
   - Press and release EN (reset) button
   - Release BOOT button

3. Flash using ESPHome:
   ```bash
   esphome run speed-radar.yaml
   ```

   Or via Home Assistant ESPHome add-on:
   - Go to ESPHome dashboard
   - Click three dots on speed-radar
   - Select "Install" → "Plug into this computer"

### Subsequent Updates (OTA)

After initial flash, updates can be done over the network:
```bash
esphome run speed-radar.yaml
```

Or via Home Assistant ESPHome add-on.

## Step 3: Assemble Hardware

See [WIRING.md](WIRING.md) for detailed wiring instructions.

Quick checklist:
- [ ] Buck converter adjusted to 5V output
- [ ] PoE splitter connected
- [ ] 12V to radar VCC
- [ ] 5V to ESP32
- [ ] All grounds connected
- [ ] Radar TX → ESP32 GPIO5
- [ ] Radar RX → ESP32 GPIO17
- [ ] Ethernet connected

## Step 4: Test Before Sealing

Before putting everything in the enclosure:

1. Power on via PoE
2. Check ESPHome logs:
   ```bash
   esphome logs speed-radar.yaml
   ```

3. Look for startup messages:
   ```
   [I][app:] ESPHome version X.X.X
   [C][hlk_ld2415h:] HLK-LD2415H:
   [C][hlk_ld2415h:]   Speed Sensor: 'Vehicle Speed'
   ```

4. Wave your hand or walk past the radar
5. Verify readings appear:
   ```
   [D][hlk_ld2415h:] Speed: 4.2 km/h, Direction: approaching
   ```

## Step 5: Add to Home Assistant

1. Go to Home Assistant → Settings → Devices & Services
2. ESPHome should auto-discover "Speed Radar"
3. Click Configure and enter encryption key
4. Entities should appear:
   - `sensor.speed_radar_vehicle_speed`
   - `sensor.speed_radar_vehicle_speed_mph`
   - `text_sensor.speed_radar_direction`
   - `binary_sensor.speed_radar_vehicle_detected`
   - `sensor.speed_radar_max_speed_today`
   - `sensor.speed_radar_detection_count`

## Step 6: Prepare Enclosure

### Weatherproofing Checklist

- [ ] Test fit all components
- [ ] Mark and drill holes for cable glands
- [ ] Install cable glands (IP68 rated)
- [ ] Install waterproof vent/breather
- [ ] Apply conformal coating to PCBs (optional)
- [ ] Add silica gel packets

### Radar Window

The radar works through thin ABS plastic (2-3mm). Options:

1. **Direct mounting**: Mount radar behind enclosure wall
2. **Window cutout**: Cut hole, cover with thin polycarbonate

### Component Mounting

Use:
- PCB standoffs (M3 screws)
- Double-sided tape (VHB)
- Cable ties for wire management
- Hot glue for strain relief

## Step 7: Install Outdoors

### Location Selection

- 1-2 meters above ground
- Clear view of road
- Protected from direct rain if possible
- Away from metal objects that could reflect radar

### Mounting Options

1. **Pole mount**: Use hose clamps or U-bolts
2. **Wall mount**: Use enclosure's mounting tabs
3. **Post mount**: Attach to fence post or dedicated pole

### Orientation

```
Traffic direction →

      ┌──────────┐
      │  RADAR   │
      │ ◉◉◉◉◉◉◉ │ ← Facing oncoming traffic
      └──────────┘   at 15-30° angle
           │
       [Enclosure]
           │
        [Pole]
```

### Cable Routing

- Use outdoor-rated Cat5e/6 or run indoor cable through conduit
- Ensure cable gland seals properly
- Leave drip loop before entering enclosure
- Secure cable to mounting with UV-resistant ties

## Step 8: Final Verification

1. Power cycle the system
2. Monitor Home Assistant for readings
3. Drive past at known speed (use GPS speedometer app)
4. Compare radar reading to actual speed
5. Adjust mounting angle if needed

## Troubleshooting

### No Readings

1. Check power LED on ESP32
2. Verify UART wiring (TX to RX, RX to TX)
3. Check ESPHome logs for errors
4. Verify baud rate is 9600

### Inaccurate Speed

1. Check mounting angle (should be 15-30° to traffic)
2. Ensure no metal obstructions near radar
3. Verify enclosure material allows radar transmission
4. Check for water on enclosure surface

### Intermittent Connection

1. Check Ethernet cable connections
2. Verify PoE switch provides consistent power
3. Check for loose wire connections
4. Ensure buck converter is stable

### No Home Assistant Discovery

1. Verify ESPHome API encryption key matches
2. Check ESP32 is on same network as HA
3. Manually add ESPHome integration with IP address
4. Check firewall rules

## Maintenance

- Check enclosure seals annually
- Replace silica gel packets if discolored
- Clean radar-facing surface of debris
- Verify readings periodically against known speed
