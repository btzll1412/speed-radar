import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import sensor
from esphome.const import (
    CONF_ID,
    DEVICE_CLASS_SPEED,
    STATE_CLASS_MEASUREMENT,
    STATE_CLASS_TOTAL_INCREASING,
    UNIT_KILOMETER_PER_HOUR,
    UNIT_PERCENT,
)
from . import CONF_HLK_LD2415H_ID, HLKLD2415HComponent, hlk_ld2415h_ns

# Basic sensors
CONF_SPEED = "speed"
CONF_VEHICLE_COUNT = "vehicle_count"
CONF_APPROACHING_COUNT = "approaching_count"
CONF_LEAVING_COUNT = "leaving_count"
CONF_AVERAGE_SPEED = "average_speed"
CONF_MAX_SPEED = "max_speed"

# Speed limit & violation sensors
CONF_SPEEDER_COUNT = "speeder_count"
CONF_VIOLATION_PERCENTAGE = "violation_percentage"
CONF_WORST_SPEEDER = "worst_speeder"

# Direction-specific stats
CONF_AVG_SPEED_APPROACHING = "avg_speed_approaching"
CONF_AVG_SPEED_LEAVING = "avg_speed_leaving"

# Hourly stats
CONF_CURRENT_HOUR_COUNT = "current_hour_count"
CONF_CURRENT_HOUR_AVG_SPEED = "current_hour_avg_speed"
CONF_PEAK_HOUR = "peak_hour"
CONF_PEAK_HOUR_COUNT = "peak_hour_count"

# Percentile
CONF_PERCENTILE_85_SPEED = "percentile_85_speed"

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(CONF_HLK_LD2415H_ID): cv.use_id(HLKLD2415HComponent),
        # Basic sensors
        cv.Optional(CONF_SPEED): sensor.sensor_schema(
            unit_of_measurement=UNIT_KILOMETER_PER_HOUR,
            accuracy_decimals=1,
            device_class=DEVICE_CLASS_SPEED,
            state_class=STATE_CLASS_MEASUREMENT,
        ),
        cv.Optional(CONF_VEHICLE_COUNT): sensor.sensor_schema(
            accuracy_decimals=0,
            state_class=STATE_CLASS_TOTAL_INCREASING,
            icon="mdi:car-multiple",
        ),
        cv.Optional(CONF_APPROACHING_COUNT): sensor.sensor_schema(
            accuracy_decimals=0,
            state_class=STATE_CLASS_TOTAL_INCREASING,
            icon="mdi:car-arrow-left",
        ),
        cv.Optional(CONF_LEAVING_COUNT): sensor.sensor_schema(
            accuracy_decimals=0,
            state_class=STATE_CLASS_TOTAL_INCREASING,
            icon="mdi:car-arrow-right",
        ),
        cv.Optional(CONF_AVERAGE_SPEED): sensor.sensor_schema(
            unit_of_measurement=UNIT_KILOMETER_PER_HOUR,
            accuracy_decimals=1,
            device_class=DEVICE_CLASS_SPEED,
            state_class=STATE_CLASS_MEASUREMENT,
            icon="mdi:speedometer-medium",
        ),
        cv.Optional(CONF_MAX_SPEED): sensor.sensor_schema(
            unit_of_measurement=UNIT_KILOMETER_PER_HOUR,
            accuracy_decimals=1,
            device_class=DEVICE_CLASS_SPEED,
            state_class=STATE_CLASS_MEASUREMENT,
            icon="mdi:speedometer",
        ),
        # Speed limit & violation sensors
        cv.Optional(CONF_SPEEDER_COUNT): sensor.sensor_schema(
            accuracy_decimals=0,
            state_class=STATE_CLASS_TOTAL_INCREASING,
            icon="mdi:car-emergency",
        ),
        cv.Optional(CONF_VIOLATION_PERCENTAGE): sensor.sensor_schema(
            unit_of_measurement=UNIT_PERCENT,
            accuracy_decimals=1,
            state_class=STATE_CLASS_MEASUREMENT,
            icon="mdi:percent",
        ),
        cv.Optional(CONF_WORST_SPEEDER): sensor.sensor_schema(
            unit_of_measurement=UNIT_KILOMETER_PER_HOUR,
            accuracy_decimals=1,
            state_class=STATE_CLASS_MEASUREMENT,
            icon="mdi:speedometer-slow",
        ),
        # Direction-specific stats
        cv.Optional(CONF_AVG_SPEED_APPROACHING): sensor.sensor_schema(
            unit_of_measurement=UNIT_KILOMETER_PER_HOUR,
            accuracy_decimals=1,
            device_class=DEVICE_CLASS_SPEED,
            state_class=STATE_CLASS_MEASUREMENT,
            icon="mdi:car-arrow-left",
        ),
        cv.Optional(CONF_AVG_SPEED_LEAVING): sensor.sensor_schema(
            unit_of_measurement=UNIT_KILOMETER_PER_HOUR,
            accuracy_decimals=1,
            device_class=DEVICE_CLASS_SPEED,
            state_class=STATE_CLASS_MEASUREMENT,
            icon="mdi:car-arrow-right",
        ),
        # Hourly stats
        cv.Optional(CONF_CURRENT_HOUR_COUNT): sensor.sensor_schema(
            accuracy_decimals=0,
            state_class=STATE_CLASS_MEASUREMENT,
            icon="mdi:counter",
        ),
        cv.Optional(CONF_CURRENT_HOUR_AVG_SPEED): sensor.sensor_schema(
            unit_of_measurement=UNIT_KILOMETER_PER_HOUR,
            accuracy_decimals=1,
            device_class=DEVICE_CLASS_SPEED,
            state_class=STATE_CLASS_MEASUREMENT,
            icon="mdi:clock-fast",
        ),
        cv.Optional(CONF_PEAK_HOUR): sensor.sensor_schema(
            accuracy_decimals=0,
            state_class=STATE_CLASS_MEASUREMENT,
            icon="mdi:clock-alert",
        ),
        cv.Optional(CONF_PEAK_HOUR_COUNT): sensor.sensor_schema(
            accuracy_decimals=0,
            state_class=STATE_CLASS_MEASUREMENT,
            icon="mdi:car-clock",
        ),
        # Percentile
        cv.Optional(CONF_PERCENTILE_85_SPEED): sensor.sensor_schema(
            unit_of_measurement=UNIT_KILOMETER_PER_HOUR,
            accuracy_decimals=1,
            device_class=DEVICE_CLASS_SPEED,
            state_class=STATE_CLASS_MEASUREMENT,
            icon="mdi:chart-bell-curve",
        ),
    }
)


async def to_code(config):
    parent = await cg.get_variable(config[CONF_HLK_LD2415H_ID])

    # Basic sensors
    if speed_config := config.get(CONF_SPEED):
        sens = await sensor.new_sensor(speed_config)
        cg.add(parent.set_speed_sensor(sens))

    if vehicle_count_config := config.get(CONF_VEHICLE_COUNT):
        sens = await sensor.new_sensor(vehicle_count_config)
        cg.add(parent.set_vehicle_count_sensor(sens))

    if approaching_count_config := config.get(CONF_APPROACHING_COUNT):
        sens = await sensor.new_sensor(approaching_count_config)
        cg.add(parent.set_approaching_count_sensor(sens))

    if leaving_count_config := config.get(CONF_LEAVING_COUNT):
        sens = await sensor.new_sensor(leaving_count_config)
        cg.add(parent.set_leaving_count_sensor(sens))

    if average_speed_config := config.get(CONF_AVERAGE_SPEED):
        sens = await sensor.new_sensor(average_speed_config)
        cg.add(parent.set_average_speed_sensor(sens))

    if max_speed_config := config.get(CONF_MAX_SPEED):
        sens = await sensor.new_sensor(max_speed_config)
        cg.add(parent.set_max_speed_sensor(sens))

    # Speed limit & violation sensors
    if speeder_count_config := config.get(CONF_SPEEDER_COUNT):
        sens = await sensor.new_sensor(speeder_count_config)
        cg.add(parent.set_speeder_count_sensor(sens))

    if violation_percentage_config := config.get(CONF_VIOLATION_PERCENTAGE):
        sens = await sensor.new_sensor(violation_percentage_config)
        cg.add(parent.set_violation_percentage_sensor(sens))

    if worst_speeder_config := config.get(CONF_WORST_SPEEDER):
        sens = await sensor.new_sensor(worst_speeder_config)
        cg.add(parent.set_worst_speeder_sensor(sens))

    # Direction-specific stats
    if avg_speed_approaching_config := config.get(CONF_AVG_SPEED_APPROACHING):
        sens = await sensor.new_sensor(avg_speed_approaching_config)
        cg.add(parent.set_avg_speed_approaching_sensor(sens))

    if avg_speed_leaving_config := config.get(CONF_AVG_SPEED_LEAVING):
        sens = await sensor.new_sensor(avg_speed_leaving_config)
        cg.add(parent.set_avg_speed_leaving_sensor(sens))

    # Hourly stats
    if current_hour_count_config := config.get(CONF_CURRENT_HOUR_COUNT):
        sens = await sensor.new_sensor(current_hour_count_config)
        cg.add(parent.set_current_hour_count_sensor(sens))

    if current_hour_avg_speed_config := config.get(CONF_CURRENT_HOUR_AVG_SPEED):
        sens = await sensor.new_sensor(current_hour_avg_speed_config)
        cg.add(parent.set_current_hour_avg_speed_sensor(sens))

    if peak_hour_config := config.get(CONF_PEAK_HOUR):
        sens = await sensor.new_sensor(peak_hour_config)
        cg.add(parent.set_peak_hour_sensor(sens))

    if peak_hour_count_config := config.get(CONF_PEAK_HOUR_COUNT):
        sens = await sensor.new_sensor(peak_hour_count_config)
        cg.add(parent.set_peak_hour_count_sensor(sens))

    # Percentile
    if percentile_85_speed_config := config.get(CONF_PERCENTILE_85_SPEED):
        sens = await sensor.new_sensor(percentile_85_speed_config)
        cg.add(parent.set_percentile_85_speed_sensor(sens))
