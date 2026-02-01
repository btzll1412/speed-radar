"""
Speed Radar Hub - MQTT Module
Handles bidirectional MQTT communication:
- Subscribe to radar data topics (instant updates)
- Publish config changes to radars (instant apply)
- MQTT discovery for Home Assistant integration
"""

import json
import asyncio
from typing import Optional, Dict, Any, Callable
import paho.mqtt.client as mqtt


class MQTTClient:
    """MQTT client for bidirectional radar communication."""

    def __init__(
        self,
        host: str = "core-mosquitto",
        port: int = 1883,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self.on_radar_data: Optional[Callable] = None
        self.on_radar_detection: Optional[Callable] = None
        self.radars: Dict[str, Dict] = {}  # slug -> radar info

    async def connect(self):
        """Connect to MQTT broker."""
        self.client = mqtt.Client(client_id="speed_radar_hub")

        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        try:
            self.client.connect(self.host, self.port, 60)
            self.client.loop_start()
            # Wait for connection
            for _ in range(10):
                if self.connected:
                    break
                await asyncio.sleep(0.5)
        except Exception as e:
            print(f"MQTT connection failed: {e}")

    async def disconnect(self):
        """Disconnect from MQTT broker."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()

    def _on_connect(self, client, userdata, flags, rc):
        """Called when connected to MQTT broker."""
        if rc == 0:
            self.connected = True
            print("Connected to MQTT broker")

            # Subscribe to all radar topics for instant updates
            # speed_radar/+/speed - real-time speed readings
            # speed_radar/+/detection - vehicle detection events
            # speed_radar/+/stats - periodic statistics
            # speed_radar/+/status - online/offline status
            client.subscribe("speed_radar/+/speed")
            client.subscribe("speed_radar/+/detection")
            client.subscribe("speed_radar/+/stats")
            client.subscribe("speed_radar/+/status")
            print("Subscribed to speed_radar/+/# topics")
        else:
            print(f"MQTT connection failed with code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Called when disconnected from MQTT broker."""
        self.connected = False
        print("Disconnected from MQTT broker")

    def _on_message(self, client, userdata, msg):
        """Called when a message is received - INSTANT processing."""
        try:
            # Parse topic: speed_radar/{radar_name}/{type}
            parts = msg.topic.split("/")
            if len(parts) != 3 or parts[0] != "speed_radar":
                return

            radar_slug = parts[1]
            msg_type = parts[2]

            # Parse payload
            if msg.payload:
                try:
                    data = json.loads(msg.payload.decode())
                except:
                    data = {"value": msg.payload.decode()}
            else:
                data = {}

            # Handle different message types
            if msg_type == "speed":
                # Real-time speed reading
                self._handle_speed_reading(radar_slug, data)
            elif msg_type == "detection":
                # Vehicle detection event
                self._handle_detection(radar_slug, data)
            elif msg_type == "stats":
                # Periodic statistics
                self._handle_stats(radar_slug, data)
            elif msg_type == "status":
                # Online/offline status
                self._handle_status(radar_slug, data)

        except Exception as e:
            print(f"Error processing MQTT message: {e}")

    def _handle_speed_reading(self, radar_slug: str, data: Dict):
        """Handle real-time speed reading - forward to HA immediately."""
        if radar_slug in self.radars:
            radar = self.radars[radar_slug]
            # Publish to HA topic immediately
            state_topic = f"speed_radar/{radar_slug}/state"
            self.client.publish(state_topic, json.dumps(data))
            print(f"[{radar_slug}] Speed: {data.get('speed', 0):.1f} km/h")

    def _handle_detection(self, radar_slug: str, data: Dict):
        """Handle vehicle detection - forward to HA and trigger callbacks."""
        if radar_slug in self.radars:
            radar = self.radars[radar_slug]
            # Publish to HA
            state_topic = f"speed_radar/{radar_slug}/state"
            data["detected"] = data.get("event") == "vehicle_detected"
            self.client.publish(state_topic, json.dumps(data))

            if data.get("event") == "vehicle_detected":
                speed = data.get("speed", 0)
                speeder = data.get("speeder", False)
                print(f"[{radar_slug}] Detection: {speed:.1f} km/h {'SPEEDER!' if speeder else ''}")

                # Callback for database recording
                if self.on_radar_detection:
                    asyncio.create_task(self.on_radar_detection(radar_slug, data))

    def _handle_stats(self, radar_slug: str, data: Dict):
        """Handle periodic statistics update."""
        if radar_slug in self.radars:
            # Publish full state to HA
            state_topic = f"speed_radar/{radar_slug}/state"
            self.client.publish(state_topic, json.dumps(data))

            # Callback for database recording
            if self.on_radar_data:
                asyncio.create_task(self.on_radar_data(radar_slug, data))

    def _handle_status(self, radar_slug: str, data: Dict):
        """Handle online/offline status."""
        status = data.get("value", "offline") if isinstance(data, dict) else str(data)
        availability_topic = f"speed_radar/{radar_slug}/availability"
        self.client.publish(availability_topic, status)
        print(f"[{radar_slug}] Status: {status}")

    def _slugify(self, text: str) -> str:
        """Convert text to slug format."""
        return text.lower().replace(" ", "_").replace("-", "_")

    def register_radar(self, radar: Dict[str, Any]):
        """Register a radar for MQTT handling."""
        slug = self._slugify(radar["name"])
        self.radars[slug] = radar
        print(f"Registered radar for MQTT: {slug}")

    # ============================================================
    # Config Publishing - INSTANT settings to radars
    # ============================================================

    async def publish_config(self, radar: Dict[str, Any], config: Dict[str, Any]):
        """Publish configuration to a radar - INSTANT apply!"""
        if not self.client or not self.connected:
            return False

        radar_slug = self._slugify(radar["name"])
        config_topic = f"speed_radar/{radar_slug}/config"

        # Publish config - radar will receive and apply immediately
        self.client.publish(config_topic, json.dumps(config), retain=True)
        print(f"Published config to {radar_slug}: {config}")
        return True

    # ============================================================
    # HA Discovery
    # ============================================================

    async def publish_discovery(self, radar: Dict[str, Any]):
        """Publish MQTT discovery messages for a radar."""
        if not self.client or not self.connected:
            return

        radar_slug = self._slugify(radar["name"])
        self.register_radar(radar)

        device_info = {
            "identifiers": [f"speed_radar_{radar['id']}"],
            "name": f"Speed Radar - {radar['name']}",
            "manufacturer": "DIY",
            "model": "HLK-LD2415H",
            "sw_version": "1.0.0"
        }

        # Define sensors to create
        sensors = [
            {
                "name": "Speed",
                "unique_id": f"speed_radar_{radar['id']}_speed",
                "state_topic": f"speed_radar/{radar_slug}/state",
                "value_template": "{{ value_json.speed | default(0) }}",
                "unit_of_measurement": "km/h",
                "icon": "mdi:speedometer"
            },
            {
                "name": "Vehicle Count",
                "unique_id": f"speed_radar_{radar['id']}_vehicle_count",
                "state_topic": f"speed_radar/{radar_slug}/state",
                "value_template": "{{ value_json.vehicle_count | default(0) }}",
                "unit_of_measurement": "vehicles",
                "icon": "mdi:car-multiple"
            },
            {
                "name": "Average Speed",
                "unique_id": f"speed_radar_{radar['id']}_average_speed",
                "state_topic": f"speed_radar/{radar_slug}/state",
                "value_template": "{{ value_json.average_speed | default(0) | round(1) }}",
                "unit_of_measurement": "km/h",
                "icon": "mdi:speedometer-medium"
            },
            {
                "name": "Max Speed",
                "unique_id": f"speed_radar_{radar['id']}_max_speed",
                "state_topic": f"speed_radar/{radar_slug}/state",
                "value_template": "{{ value_json.max_speed | default(0) | round(1) }}",
                "unit_of_measurement": "km/h",
                "icon": "mdi:speedometer"
            },
            {
                "name": "Speeder Count",
                "unique_id": f"speed_radar_{radar['id']}_speeder_count",
                "state_topic": f"speed_radar/{radar_slug}/state",
                "value_template": "{{ value_json.speeder_count | default(0) }}",
                "unit_of_measurement": "vehicles",
                "icon": "mdi:car-emergency"
            },
            {
                "name": "Violation Percentage",
                "unique_id": f"speed_radar_{radar['id']}_violation_pct",
                "state_topic": f"speed_radar/{radar_slug}/state",
                "value_template": "{{ value_json.violation_percentage | default(0) | round(1) }}",
                "unit_of_measurement": "%",
                "icon": "mdi:percent"
            },
            {
                "name": "85th Percentile",
                "unique_id": f"speed_radar_{radar['id']}_percentile_85",
                "state_topic": f"speed_radar/{radar_slug}/state",
                "value_template": "{{ value_json.percentile_85 | default(0) | round(1) }}",
                "unit_of_measurement": "km/h",
                "icon": "mdi:chart-bell-curve"
            },
            {
                "name": "Direction",
                "unique_id": f"speed_radar_{radar['id']}_direction",
                "state_topic": f"speed_radar/{radar_slug}/state",
                "value_template": "{{ value_json.direction | default('Unknown') }}",
                "icon": "mdi:arrow-left-right"
            }
        ]

        # Publish discovery for each sensor
        for sensor in sensors:
            config_topic = f"homeassistant/sensor/{radar_slug}_{self._slugify(sensor['name'])}/config"
            config_payload = {
                "name": f"{radar['name']} {sensor['name']}",
                "unique_id": sensor["unique_id"],
                "state_topic": sensor["state_topic"],
                "value_template": sensor["value_template"],
                "device": device_info,
                "icon": sensor["icon"]
            }
            if sensor.get("unit_of_measurement"):
                config_payload["unit_of_measurement"] = sensor["unit_of_measurement"]

            self.client.publish(config_topic, json.dumps(config_payload), retain=True)

        # Binary sensor for vehicle detected
        binary_config = {
            "name": f"{radar['name']} Vehicle Detected",
            "unique_id": f"speed_radar_{radar['id']}_detected",
            "state_topic": f"speed_radar/{radar_slug}/state",
            "value_template": "{{ 'ON' if value_json.detected else 'OFF' }}",
            "device": device_info,
            "device_class": "motion",
            "icon": "mdi:car"
        }
        self.client.publish(
            f"homeassistant/binary_sensor/{radar_slug}_detected/config",
            json.dumps(binary_config),
            retain=True
        )

        # Online status sensor
        online_config = {
            "name": f"{radar['name']} Online",
            "unique_id": f"speed_radar_{radar['id']}_online",
            "state_topic": f"speed_radar/{radar_slug}/availability",
            "device": device_info,
            "device_class": "connectivity",
            "payload_on": "online",
            "payload_off": "offline"
        }
        self.client.publish(
            f"homeassistant/binary_sensor/{radar_slug}_online/config",
            json.dumps(online_config),
            retain=True
        )

        print(f"Published MQTT discovery for radar: {radar['name']}")

    async def remove_discovery(self, radar: Dict[str, Any]):
        """Remove MQTT discovery messages for a radar."""
        if not self.client or not self.connected:
            return

        radar_slug = self._slugify(radar["name"])

        # Remove from registered radars
        if radar_slug in self.radars:
            del self.radars[radar_slug]

        # Remove all sensors
        sensor_names = ["speed", "vehicle_count", "average_speed", "max_speed",
                       "speeder_count", "violation_pct", "percentile_85", "direction"]
        for name in sensor_names:
            topic = f"homeassistant/sensor/{radar_slug}_{name}/config"
            self.client.publish(topic, "", retain=True)

        # Remove binary sensors
        self.client.publish(f"homeassistant/binary_sensor/{radar_slug}_detected/config", "", retain=True)
        self.client.publish(f"homeassistant/binary_sensor/{radar_slug}_online/config", "", retain=True)

    async def publish_state(self, radar: Dict[str, Any], data: Dict[str, Any]):
        """Publish state update for a radar (legacy HTTP compatibility)."""
        if not self.client or not self.connected:
            return

        radar_slug = self._slugify(radar["name"])

        # Publish state
        state_topic = f"speed_radar/{radar_slug}/state"
        self.client.publish(state_topic, json.dumps(data))

        # Publish availability
        availability_topic = f"speed_radar/{radar_slug}/availability"
        self.client.publish(availability_topic, "online")

    async def publish_offline(self, radar: Dict[str, Any]):
        """Mark a radar as offline."""
        if not self.client or not self.connected:
            return

        radar_slug = self._slugify(radar["name"])
        availability_topic = f"speed_radar/{radar_slug}/availability"
        self.client.publish(availability_topic, "offline")
