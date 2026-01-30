import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import uart
from esphome.const import CONF_ID

DEPENDENCIES = ["uart"]
CODEOWNERS = ["@speed-radar"]

CONF_HLK_LD2415H_ID = "hlk_ld2415h_id"

hlk_ld2415h_ns = cg.esphome_ns.namespace("hlk_ld2415h")
HLKLD2415HComponent = hlk_ld2415h_ns.class_(
    "HLKLD2415HComponent", cg.Component, uart.UARTDevice
)

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(HLKLD2415HComponent),
    }
).extend(uart.UART_DEVICE_SCHEMA)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await uart.register_uart_device(var, config)
