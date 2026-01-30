import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import text_sensor
from esphome.const import CONF_ID
from . import CONF_HLK_LD2415H_ID, HLKLD2415HComponent, hlk_ld2415h_ns

CONF_DIRECTION = "direction"

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(CONF_HLK_LD2415H_ID): cv.use_id(HLKLD2415HComponent),
        cv.Optional(CONF_DIRECTION): text_sensor.text_sensor_schema(),
    }
)


async def to_code(config):
    parent = await cg.get_variable(config[CONF_HLK_LD2415H_ID])

    if direction_config := config.get(CONF_DIRECTION):
        sens = await text_sensor.new_text_sensor(direction_config)
        cg.add(parent.set_direction_text_sensor(sens))
