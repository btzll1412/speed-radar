import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import uart
from esphome.const import CONF_ID

DEPENDENCIES = ["uart"]
CODEOWNERS = ["@speed-radar"]

CONF_HLK_LD2415H_ID = "hlk_ld2415h_id"
CONF_MIN_SPEED_THRESHOLD = "min_speed_threshold"
CONF_MAX_SPEED_THRESHOLD = "max_speed_threshold"
CONF_SPEED_LIMIT = "speed_limit"
CONF_DIRECTION_FILTER = "direction_filter"
CONF_ANGLE_COMPENSATION = "angle_compensation"
CONF_SPEED_OFFSET = "speed_offset"

hlk_ld2415h_ns = cg.esphome_ns.namespace("hlk_ld2415h")
HLKLD2415HComponent = hlk_ld2415h_ns.class_(
    "HLKLD2415HComponent", cg.Component, uart.UARTDevice
)

# Direction filter enum values
DIRECTION_FILTER_OPTIONS = {
    "both": 0,
    "approaching": 1,
    "leaving": 2,
}

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(HLKLD2415HComponent),
        cv.Optional(CONF_MIN_SPEED_THRESHOLD, default=10.0): cv.float_range(min=0, max=100),
        cv.Optional(CONF_MAX_SPEED_THRESHOLD, default=250.0): cv.float_range(min=50, max=300),
        cv.Optional(CONF_SPEED_LIMIT, default=50.0): cv.float_range(min=10, max=200),
        cv.Optional(CONF_DIRECTION_FILTER, default="both"): cv.enum(DIRECTION_FILTER_OPTIONS, lower=True),
        cv.Optional(CONF_ANGLE_COMPENSATION, default=0.0): cv.float_range(min=0, max=60),
        cv.Optional(CONF_SPEED_OFFSET, default=0.0): cv.float_range(min=-20, max=20),
    }
).extend(uart.UART_DEVICE_SCHEMA)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await uart.register_uart_device(var, config)

    cg.add(var.set_min_speed_threshold(config[CONF_MIN_SPEED_THRESHOLD]))
    cg.add(var.set_max_speed_threshold(config[CONF_MAX_SPEED_THRESHOLD]))
    cg.add(var.set_speed_limit(config[CONF_SPEED_LIMIT]))
    cg.add(var.set_direction_filter(config[CONF_DIRECTION_FILTER]))
    cg.add(var.set_angle_compensation(config[CONF_ANGLE_COMPENSATION]))
    cg.add(var.set_speed_offset(config[CONF_SPEED_OFFSET]))
