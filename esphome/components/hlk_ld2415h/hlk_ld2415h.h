#pragma once

#include "esphome/core/component.h"
#include "esphome/components/uart/uart.h"
#include "esphome/components/sensor/sensor.h"
#include "esphome/components/text_sensor/text_sensor.h"
#include "esphome/components/binary_sensor/binary_sensor.h"
#include <vector>
#include <cmath>

namespace esphome {
namespace hlk_ld2415h {

// Direction filter modes
enum class DirectionFilter : uint8_t {
  BOTH = 0,
  APPROACHING_ONLY = 1,
  LEAVING_ONLY = 2
};

class HLKLD2415HComponent : public Component, public uart::UARTDevice {
 public:
  void setup() override;
  void loop() override;
  void dump_config() override;
  float get_setup_priority() const override { return setup_priority::DATA; }

  // Core sensor setters
  void set_speed_sensor(sensor::Sensor *sensor) { this->speed_sensor_ = sensor; }
  void set_direction_text_sensor(text_sensor::TextSensor *sensor) { this->direction_text_sensor_ = sensor; }
  void set_vehicle_detected_binary_sensor(binary_sensor::BinarySensor *sensor) { this->vehicle_detected_binary_sensor_ = sensor; }

  // Statistics sensor setters
  void set_vehicle_count_sensor(sensor::Sensor *sensor) { this->vehicle_count_sensor_ = sensor; }
  void set_approaching_count_sensor(sensor::Sensor *sensor) { this->approaching_count_sensor_ = sensor; }
  void set_leaving_count_sensor(sensor::Sensor *sensor) { this->leaving_count_sensor_ = sensor; }
  void set_average_speed_sensor(sensor::Sensor *sensor) { this->average_speed_sensor_ = sensor; }
  void set_max_speed_sensor(sensor::Sensor *sensor) { this->max_speed_sensor_ = sensor; }

  // Speed limit & violation sensor setters
  void set_speeder_count_sensor(sensor::Sensor *sensor) { this->speeder_count_sensor_ = sensor; }
  void set_violation_percentage_sensor(sensor::Sensor *sensor) { this->violation_percentage_sensor_ = sensor; }
  void set_worst_speeder_sensor(sensor::Sensor *sensor) { this->worst_speeder_sensor_ = sensor; }

  // Direction-specific stats sensor setters
  void set_avg_speed_approaching_sensor(sensor::Sensor *sensor) { this->avg_speed_approaching_sensor_ = sensor; }
  void set_avg_speed_leaving_sensor(sensor::Sensor *sensor) { this->avg_speed_leaving_sensor_ = sensor; }

  // Hourly stats sensor setters
  void set_current_hour_count_sensor(sensor::Sensor *sensor) { this->current_hour_count_sensor_ = sensor; }
  void set_current_hour_avg_speed_sensor(sensor::Sensor *sensor) { this->current_hour_avg_speed_sensor_ = sensor; }
  void set_peak_hour_sensor(sensor::Sensor *sensor) { this->peak_hour_sensor_ = sensor; }
  void set_peak_hour_count_sensor(sensor::Sensor *sensor) { this->peak_hour_count_sensor_ = sensor; }

  // 85th percentile sensor
  void set_percentile_85_speed_sensor(sensor::Sensor *sensor) { this->percentile_85_speed_sensor_ = sensor; }

  // Configuration setters (can be called from HA at runtime)
  void set_min_speed_threshold(float threshold) { this->min_speed_threshold_ = threshold; }
  void set_max_speed_threshold(float threshold) { this->max_speed_threshold_ = threshold; }
  void set_vehicle_gap_ms(uint32_t gap_ms) { this->vehicle_gap_ms_ = gap_ms; }
  void set_detection_timeout_ms(uint32_t timeout_ms) { this->detection_timeout_ms_ = timeout_ms; }
  void set_speed_limit(float limit) { this->speed_limit_ = limit; }
  void set_direction_filter(uint8_t filter) { this->direction_filter_ = static_cast<DirectionFilter>(filter); }
  void set_angle_compensation(float angle_degrees);
  void set_speed_offset(float offset) { this->speed_offset_ = offset; }

  // Getters for current config values
  float get_min_speed_threshold() const { return this->min_speed_threshold_; }
  float get_max_speed_threshold() const { return this->max_speed_threshold_; }
  uint32_t get_vehicle_gap_ms() const { return this->vehicle_gap_ms_; }
  uint32_t get_detection_timeout_ms() const { return this->detection_timeout_ms_; }
  float get_speed_limit() const { return this->speed_limit_; }
  uint8_t get_direction_filter() const { return static_cast<uint8_t>(this->direction_filter_); }
  float get_angle_compensation() const { return this->angle_degrees_; }
  float get_speed_offset() const { return this->speed_offset_; }

  // Public methods
  void reset_statistics();
  void set_current_hour(uint8_t hour);  // Called from HA time component

 protected:
  void parse_data_();
  void process_speed_(float speed, bool approaching);
  void clear_detection_();
  void update_statistics_(float speed, bool approaching);
  void update_hourly_stats_(float speed);
  void check_hour_change_();
  float apply_calibration_(float raw_speed);
  float calculate_percentile_85_();

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

  // Speed limit & violation sensors
  sensor::Sensor *speeder_count_sensor_{nullptr};
  sensor::Sensor *violation_percentage_sensor_{nullptr};
  sensor::Sensor *worst_speeder_sensor_{nullptr};

  // Direction-specific stats sensors
  sensor::Sensor *avg_speed_approaching_sensor_{nullptr};
  sensor::Sensor *avg_speed_leaving_sensor_{nullptr};

  // Hourly stats sensors
  sensor::Sensor *current_hour_count_sensor_{nullptr};
  sensor::Sensor *current_hour_avg_speed_sensor_{nullptr};
  sensor::Sensor *peak_hour_sensor_{nullptr};
  sensor::Sensor *peak_hour_count_sensor_{nullptr};

  // 85th percentile sensor
  sensor::Sensor *percentile_85_speed_sensor_{nullptr};

  // Buffer and timing
  std::string buffer_;
  uint32_t last_detection_time_{0};
  uint32_t last_vehicle_time_{0};
  float last_speed_{0};
  bool last_approaching_{false};

  // Basic statistics tracking
  uint32_t vehicle_count_{0};
  uint32_t approaching_count_{0};
  uint32_t leaving_count_{0};
  float speed_sum_{0};
  float max_speed_{0};

  // Speed limit tracking
  uint32_t speeder_count_{0};
  float worst_over_limit_{0};  // Highest amount over the speed limit

  // Direction-specific stats
  float approaching_speed_sum_{0};
  float leaving_speed_sum_{0};

  // Hourly stats (24 hours)
  uint8_t current_hour_{0};
  uint32_t hourly_counts_[24] = {0};
  float hourly_speed_sums_[24] = {0};
  uint32_t current_hour_count_{0};
  float current_hour_speed_sum_{0};
  uint8_t peak_hour_{0};
  uint32_t peak_hour_count_{0};

  // 85th percentile tracking (stores recent speeds)
  std::vector<float> speed_samples_;
  static const size_t MAX_SAMPLES = 200;  // Keep last 200 samples for percentile calculation

  // Configuration (all adjustable from Home Assistant at runtime)
  float min_speed_threshold_{10.0};
  float max_speed_threshold_{250.0};
  uint32_t detection_timeout_ms_{2000};
  uint32_t vehicle_gap_ms_{3000};
  float speed_limit_{50.0};  // Default 50 km/h
  DirectionFilter direction_filter_{DirectionFilter::BOTH};

  // Calibration
  float angle_degrees_{0.0};      // Mounting angle in degrees
  float angle_cos_factor_{1.0};   // Pre-calculated cos(angle) for speed correction
  float speed_offset_{0.0};       // Additive offset for fine-tuning
};

}  // namespace hlk_ld2415h
}  // namespace esphome
