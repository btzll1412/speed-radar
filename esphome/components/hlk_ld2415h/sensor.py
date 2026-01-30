import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import sensor
from esphome.const import (
    CONF_ID,
    DEVICE_CLASS_SPEED,
    STATE_CLASS_MEASUREMENT,
    UNIT_KILOMETER_PER_HOUR,
)
from . import CONF_HLK_LD2415H_ID, HLKLD2415HComponent, hlk_ld2415h_ns

CONF_SPEED = "speed"

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(CONF_HLK_LD2415H_ID): cv.use_id(HLKLD2415HComponent),
        cv.Optional(CONF_SPEED): sensor.sensor_schema(
            unit_of_measurement=UNIT_KILOMETER_PER_HOUR,
            accuracy_decimals=1,
            device_class=DEVICE_CLASS_SPEED,
            state_class=STATE_CLASS_MEASUREMENT,
        ),
    }
)


async def to_code(config):
    parent = await cg.get_variable(config[CONF_HLK_LD2415H_ID])

    if speed_config := config.get(CONF_SPEED):
        sens = await sensor.new_sensor(speed_config)
        cg.add(parent.set_speed_sensor(sens))
