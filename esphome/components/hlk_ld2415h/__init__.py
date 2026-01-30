import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import uart
from esphome.const import CONF_ID

DEPENDENCIES = ["uart"]
CODEOWNERS = ["@speed-radar"]

CONF_HLK_LD2415H_ID = "hlk_ld2415h_id"
CONF_MIN_SPEED_THRESHOLD = "min_speed_threshold"
CONF_MAX_SPEED_THRESHOLD = "max_speed_threshold"

hlk_ld2415h_ns = cg.esphome_ns.namespace("hlk_ld2415h")
HLKLD2415HComponent = hlk_ld2415h_ns.class_(
    "HLKLD2415HComponent", cg.Component, uart.UARTDevice
)

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(HLKLD2415HComponent),
        cv.Optional(CONF_MIN_SPEED_THRESHOLD, default=10.0): cv.float_range(min=0, max=100),
        cv.Optional(CONF_MAX_SPEED_THRESHOLD, default=250.0): cv.float_range(min=50, max=300),
    }
).extend(uart.UART_DEVICE_SCHEMA)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await uart.register_uart_device(var, config)

    cg.add(var.set_min_speed_threshold(config[CONF_MIN_SPEED_THRESHOLD]))
    cg.add(var.set_max_speed_threshold(config[CONF_MAX_SPEED_THRESHOLD]))
