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

  // Sensor setters
  void set_speed_sensor(sensor::Sensor *sensor) { this->speed_sensor_ = sensor; }
  void set_direction_text_sensor(text_sensor::TextSensor *sensor) { this->direction_text_sensor_ = sensor; }
  void set_vehicle_detected_binary_sensor(binary_sensor::BinarySensor *sensor) { this->vehicle_detected_binary_sensor_ = sensor; }

  // Statistics sensor setters
  void set_vehicle_count_sensor(sensor::Sensor *sensor) { this->vehicle_count_sensor_ = sensor; }
  void set_approaching_count_sensor(sensor::Sensor *sensor) { this->approaching_count_sensor_ = sensor; }
  void set_leaving_count_sensor(sensor::Sensor *sensor) { this->leaving_count_sensor_ = sensor; }
  void set_average_speed_sensor(sensor::Sensor *sensor) { this->average_speed_sensor_ = sensor; }
  void set_max_speed_sensor(sensor::Sensor *sensor) { this->max_speed_sensor_ = sensor; }

  // Configuration setters (can be called from HA at runtime)
  void set_min_speed_threshold(float threshold) { this->min_speed_threshold_ = threshold; }
  void set_max_speed_threshold(float threshold) { this->max_speed_threshold_ = threshold; }
  void set_vehicle_gap_ms(uint32_t gap_ms) { this->vehicle_gap_ms_ = gap_ms; }
  void set_detection_timeout_ms(uint32_t timeout_ms) { this->detection_timeout_ms_ = timeout_ms; }

  // Getters for current config values
  float get_min_speed_threshold() const { return this->min_speed_threshold_; }
  float get_max_speed_threshold() const { return this->max_speed_threshold_; }
  uint32_t get_vehicle_gap_ms() const { return this->vehicle_gap_ms_; }
  uint32_t get_detection_timeout_ms() const { return this->detection_timeout_ms_; }

  // Public methods
  void reset_statistics();

 protected:
  void parse_data_();
  void process_speed_(float speed, bool approaching);
  void clear_detection_();
  void update_statistics_(float speed, bool approaching);

  // Core sensors
  sensor::Sensor *speed_sensor_{nullptr};
  text_sensor::TextSensor *direction_text_sensor_{nullptr};
  binary_sensor::BinarySensor *vehicle_detected_binary_sensor_{nullptr};

  // Statistics sensors
  sensor::Sensor *vehicle_count_sensor_{nullptr};
  sensor::Sensor *approaching_count_sensor_{nullptr};
  sensor::Sensor *leaving_count_sensor_{nullptr};
  sensor::Sensor *average_speed_sensor_{nullptr};
  sensor::Sensor *max_speed_sensor_{nullptr};

  // Buffer and timing
  std::string buffer_;
  uint32_t last_detection_time_{0};
  uint32_t last_vehicle_time_{0};  // Track when last vehicle passed (for counting unique vehicles)
  float last_speed_{0};
  bool last_approaching_{false};

  // Statistics tracking
  uint32_t vehicle_count_{0};
  uint32_t approaching_count_{0};
  uint32_t leaving_count_{0};
  float speed_sum_{0};
  float max_speed_{0};

  // Configuration (all adjustable from Home Assistant at runtime)
  float min_speed_threshold_{10.0};     // Ignore speeds below this (filters pedestrians)
  float max_speed_threshold_{250.0};    // Ignore speeds above this (filters noise)
  uint32_t detection_timeout_ms_{2000}; // Clear detection after this many ms of no data
  uint32_t vehicle_gap_ms_{3000};       // Minimum gap (ms) between readings to count as new vehicle
};

}  // namespace hlk_ld2415h
}  // namespace esphome
