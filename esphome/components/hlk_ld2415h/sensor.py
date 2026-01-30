import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import sensor
from esphome.const import (
    CONF_ID,
    DEVICE_CLASS_SPEED,
    STATE_CLASS_MEASUREMENT,
    STATE_CLASS_TOTAL_INCREASING,
    UNIT_KILOMETER_PER_HOUR,
)
from . import CONF_HLK_LD2415H_ID, HLKLD2415HComponent, hlk_ld2415h_ns

CONF_SPEED = "speed"
CONF_VEHICLE_COUNT = "vehicle_count"
CONF_APPROACHING_COUNT = "approaching_count"
CONF_LEAVING_COUNT = "leaving_count"
CONF_AVERAGE_SPEED = "average_speed"
CONF_MAX_SPEED = "max_speed"

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(CONF_HLK_LD2415H_ID): cv.use_id(HLKLD2415HComponent),
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
    }
)


async def to_code(config):
    parent = await cg.get_variable(config[CONF_HLK_LD2415H_ID])

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
