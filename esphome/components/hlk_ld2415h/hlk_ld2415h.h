#pragma once

#include "esphome/core/component.h"
#include "esphome/components/uart/uart.h"
#include "esphome/components/sensor/sensor.h"
#include "esphome/components/text_sensor/text_sensor.h"
#include "esphome/components/binary_sensor/binary_sensor.h"

namespace esphome {
namespace hlk_ld2415h {

class HLKLD2415HComponent : public Component, public uart::UARTDevice {
 public:
  void setup() override;
  void loop() override;
  void dump_config() override;
  float get_setup_priority() const override { return setup_priority::DATA; }

  void set_speed_sensor(sensor::Sensor *sensor) { this->speed_sensor_ = sensor; }
  void set_direction_text_sensor(text_sensor::TextSensor *sensor) { this->direction_text_sensor_ = sensor; }
  void set_vehicle_detected_binary_sensor(binary_sensor::BinarySensor *sensor) { this->vehicle_detected_binary_sensor_ = sensor; }

 protected:
  void parse_data_();
  void process_speed_(float speed, bool approaching);
  void clear_detection_();

  sensor::Sensor *speed_sensor_{nullptr};
  text_sensor::TextSensor *direction_text_sensor_{nullptr};
  binary_sensor::BinarySensor *vehicle_detected_binary_sensor_{nullptr};

  std::string buffer_;
  uint32_t last_detection_time_{0};
  static const uint32_t DETECTION_TIMEOUT_MS = 2000;  // Clear detection after 2 seconds of no data
};

}  // namespace hlk_ld2415h
}  // namespace esphome
