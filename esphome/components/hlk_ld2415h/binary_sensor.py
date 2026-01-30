import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import binary_sensor
from esphome.const import CONF_ID, DEVICE_CLASS_MOTION
from . import CONF_HLK_LD2415H_ID, HLKLD2415HComponent, hlk_ld2415h_ns

CONF_VEHICLE_DETECTED = "vehicle_detected"

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(CONF_HLK_LD2415H_ID): cv.use_id(HLKLD2415HComponent),
        cv.Optional(CONF_VEHICLE_DETECTED): binary_sensor.binary_sensor_schema(
            device_class=DEVICE_CLASS_MOTION,
        ),
    }
)


async def to_code(config):
    parent = await cg.get_variable(config[CONF_HLK_LD2415H_ID])

    if vehicle_detected_config := config.get(CONF_VEHICLE_DETECTED):
        sens = await binary_sensor.new_binary_sensor(vehicle_detected_config)
        cg.add(parent.set_vehicle_detected_binary_sensor(sens))
