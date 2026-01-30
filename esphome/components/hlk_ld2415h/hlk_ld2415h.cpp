#include "hlk_ld2415h.h"
#include "esphome/core/log.h"
#include <algorithm>

namespace esphome {
namespace hlk_ld2415h {

static const char *const TAG = "hlk_ld2415h";

void HLKLD2415HComponent::setup() {
  ESP_LOGCONFIG(TAG, "Setting up HLK-LD2415H...");
  this->buffer_.reserve(16);
  this->speed_samples_.reserve(MAX_SAMPLES);
}

void HLKLD2415HComponent::dump_config() {
  ESP_LOGCONFIG(TAG, "HLK-LD2415H:");
  ESP_LOGCONFIG(TAG, "  Speed Limit: %.1f km/h", this->speed_limit_);
  ESP_LOGCONFIG(TAG, "  Min Speed Threshold: %.1f km/h", this->min_speed_threshold_);
  ESP_LOGCONFIG(TAG, "  Max Speed Threshold: %.1f km/h", this->max_speed_threshold_);
  ESP_LOGCONFIG(TAG, "  Detection Timeout: %u ms", this->detection_timeout_ms_);
  ESP_LOGCONFIG(TAG, "  Vehicle Gap: %u ms", this->vehicle_gap_ms_);
  ESP_LOGCONFIG(TAG, "  Direction Filter: %s",
                this->direction_filter_ == DirectionFilter::BOTH ? "Both" :
                this->direction_filter_ == DirectionFilter::APPROACHING_ONLY ? "Approaching Only" : "Leaving Only");
  ESP_LOGCONFIG(TAG, "  Angle Compensation: %.1f degrees (factor: %.4f)", this->angle_degrees_, this->angle_cos_factor_);
  ESP_LOGCONFIG(TAG, "  Speed Offset: %.1f km/h", this->speed_offset_);
  LOG_SENSOR("  ", "Speed", this->speed_sensor_);
  LOG_TEXT_SENSOR("  ", "Direction", this->direction_text_sensor_);
  LOG_BINARY_SENSOR("  ", "Vehicle Detected", this->vehicle_detected_binary_sensor_);
}

void HLKLD2415HComponent::loop() {
  // Read all available data from UART
  while (this->available()) {
    uint8_t c;
    this->read_byte(&c);

    if (c == '\n') {
      this->parse_data_();
      this->buffer_.clear();
    } else if (c != '\r') {
      if (this->buffer_.length() < 15) {
        this->buffer_ += static_cast<char>(c);
      }
    }
  }

  // Clear detection state if no data received for detection_timeout_ms_
  if (this->last_detection_time_ > 0 &&
      millis() - this->last_detection_time_ > this->detection_timeout_ms_) {
    this->clear_detection_();
  }
}

void HLKLD2415HComponent::parse_data_() {
  if (this->buffer_.length() < 7) {
    return;
  }

  if (this->buffer_[0] != 'V') {
    ESP_LOGW(TAG, "Invalid header: %s", this->buffer_.c_str());
    return;
  }

  char direction_char = this->buffer_[1];
  if (direction_char != '+' && direction_char != '-') {
    ESP_LOGW(TAG, "Invalid direction: %c", direction_char);
    return;
  }

  bool approaching = (direction_char == '+');

  // Apply direction filter
  if (this->direction_filter_ == DirectionFilter::APPROACHING_ONLY && !approaching) {
    ESP_LOGV(TAG, "Ignoring leaving vehicle (filter: approaching only)");
    return;
  }
  if (this->direction_filter_ == DirectionFilter::LEAVING_ONLY && approaching) {
    ESP_LOGV(TAG, "Ignoring approaching vehicle (filter: leaving only)");
    return;
  }

  // Parse speed value
  std::string speed_str = this->buffer_.substr(2);
  size_t end = speed_str.find_last_not_of(" \t\r\n");
  if (end != std::string::npos) {
    speed_str = speed_str.substr(0, end + 1);
  }

  float raw_speed = 0;
  try {
    raw_speed = std::stof(speed_str);
  } catch (...) {
    ESP_LOGW(TAG, "Failed to parse speed: %s", speed_str.c_str());
    return;
  }

  // Apply calibration (angle compensation + offset)
  float speed = this->apply_calibration_(raw_speed);

  // Apply speed thresholds
  if (speed < this->min_speed_threshold_) {
    ESP_LOGV(TAG, "Speed %.1f km/h below threshold, ignoring", speed);
    return;
  }

  if (speed > this->max_speed_threshold_) {
    ESP_LOGW(TAG, "Speed %.1f km/h above max threshold, ignoring", speed);
    return;
  }

  ESP_LOGD(TAG, "Vehicle: %.1f km/h %s (raw: %.1f)", speed, approaching ? "approaching" : "leaving", raw_speed);

  this->process_speed_(speed, approaching);
}

float HLKLD2415HComponent::apply_calibration_(float raw_speed) {
  // Apply angle compensation: actual_speed = measured_speed / cos(angle)
  float calibrated = raw_speed / this->angle_cos_factor_;
  // Apply offset
  calibrated += this->speed_offset_;
  return calibrated;
}

void HLKLD2415HComponent::set_angle_compensation(float angle_degrees) {
  this->angle_degrees_ = angle_degrees;
  // Convert to radians and calculate cosine
  float radians = angle_degrees * M_PI / 180.0f;
  this->angle_cos_factor_ = cos(radians);
  // Prevent division by zero or very small numbers
  if (this->angle_cos_factor_ < 0.1f) {
    this->angle_cos_factor_ = 0.1f;
  }
  ESP_LOGI(TAG, "Angle compensation set to %.1f degrees (factor: %.4f)", angle_degrees, this->angle_cos_factor_);
}

void HLKLD2415HComponent::process_speed_(float speed, bool approaching) {
  uint32_t now = millis();

  // Check if this is a new vehicle
  bool is_new_vehicle = (this->last_vehicle_time_ == 0 ||
                         now - this->last_vehicle_time_ > this->vehicle_gap_ms_ ||
                         approaching != this->last_approaching_);

  this->last_detection_time_ = now;
  this->last_speed_ = speed;
  this->last_approaching_ = approaching;

  // Update speed sensor
  if (this->speed_sensor_ != nullptr) {
    this->speed_sensor_->publish_state(speed);
  }

  // Update direction text sensor
  if (this->direction_text_sensor_ != nullptr) {
    this->direction_text_sensor_->publish_state(approaching ? "Approaching" : "Leaving");
  }

  // Update vehicle detected binary sensor
  if (this->vehicle_detected_binary_sensor_ != nullptr) {
    this->vehicle_detected_binary_sensor_->publish_state(true);
  }

  // Update statistics if this is a new vehicle
  if (is_new_vehicle) {
    this->update_statistics_(speed, approaching);
    this->update_hourly_stats_(speed);
    this->last_vehicle_time_ = now;
  } else {
    // Update max speed for current vehicle if higher
    if (speed > this->max_speed_) {
      this->max_speed_ = speed;
      if (this->max_speed_sensor_ != nullptr) {
        this->max_speed_sensor_->publish_state(this->max_speed_);
      }
    }
  }
}

void HLKLD2415HComponent::update_statistics_(float speed, bool approaching) {
  // Increment counts
  this->vehicle_count_++;
  if (approaching) {
    this->approaching_count_++;
    this->approaching_speed_sum_ += speed;
  } else {
    this->leaving_count_++;
    this->leaving_speed_sum_ += speed;
  }

  // Update speed sum for average
  this->speed_sum_ += speed;

  // Update max speed
  if (speed > this->max_speed_) {
    this->max_speed_ = speed;
  }

  // Check for speeder
  if (speed > this->speed_limit_) {
    this->speeder_count_++;
    float over_limit = speed - this->speed_limit_;
    if (over_limit > this->worst_over_limit_) {
      this->worst_over_limit_ = over_limit;
    }
  }

  // Add to samples for percentile calculation
  if (this->speed_samples_.size() >= MAX_SAMPLES) {
    this->speed_samples_.erase(this->speed_samples_.begin());
  }
  this->speed_samples_.push_back(speed);

  // Publish all statistics
  if (this->vehicle_count_sensor_ != nullptr) {
    this->vehicle_count_sensor_->publish_state(this->vehicle_count_);
  }

  if (this->approaching_count_sensor_ != nullptr) {
    this->approaching_count_sensor_->publish_state(this->approaching_count_);
  }

  if (this->leaving_count_sensor_ != nullptr) {
    this->leaving_count_sensor_->publish_state(this->leaving_count_);
  }

  if (this->average_speed_sensor_ != nullptr && this->vehicle_count_ > 0) {
    this->average_speed_sensor_->publish_state(this->speed_sum_ / this->vehicle_count_);
  }

  if (this->max_speed_sensor_ != nullptr) {
    this->max_speed_sensor_->publish_state(this->max_speed_);
  }

  // Speed limit violation stats
  if (this->speeder_count_sensor_ != nullptr) {
    this->speeder_count_sensor_->publish_state(this->speeder_count_);
  }

  if (this->violation_percentage_sensor_ != nullptr && this->vehicle_count_ > 0) {
    float percentage = (float)this->speeder_count_ / (float)this->vehicle_count_ * 100.0f;
    this->violation_percentage_sensor_->publish_state(percentage);
  }

  if (this->worst_speeder_sensor_ != nullptr) {
    this->worst_speeder_sensor_->publish_state(this->worst_over_limit_);
  }

  // Direction-specific averages
  if (this->avg_speed_approaching_sensor_ != nullptr && this->approaching_count_ > 0) {
    this->avg_speed_approaching_sensor_->publish_state(this->approaching_speed_sum_ / this->approaching_count_);
  }

  if (this->avg_speed_leaving_sensor_ != nullptr && this->leaving_count_ > 0) {
    this->avg_speed_leaving_sensor_->publish_state(this->leaving_speed_sum_ / this->leaving_count_);
  }

  // 85th percentile
  if (this->percentile_85_speed_sensor_ != nullptr && this->speed_samples_.size() >= 10) {
    this->percentile_85_speed_sensor_->publish_state(this->calculate_percentile_85_());
  }

  ESP_LOGI(TAG, "Vehicle #%d: %.1f km/h %s | Avg: %.1f | Speeders: %d (%.1f%%)",
           this->vehicle_count_, speed, approaching ? "approaching" : "leaving",
           this->speed_sum_ / this->vehicle_count_,
           this->speeder_count_,
           this->vehicle_count_ > 0 ? (float)this->speeder_count_ / this->vehicle_count_ * 100.0f : 0);
}

void HLKLD2415HComponent::update_hourly_stats_(float speed) {
  this->current_hour_count_++;
  this->current_hour_speed_sum_ += speed;

  // Update current hour sensors
  if (this->current_hour_count_sensor_ != nullptr) {
    this->current_hour_count_sensor_->publish_state(this->current_hour_count_);
  }

  if (this->current_hour_avg_speed_sensor_ != nullptr && this->current_hour_count_ > 0) {
    this->current_hour_avg_speed_sensor_->publish_state(this->current_hour_speed_sum_ / this->current_hour_count_);
  }

  // Check if this hour is the new peak
  if (this->current_hour_count_ > this->peak_hour_count_) {
    this->peak_hour_count_ = this->current_hour_count_;
    this->peak_hour_ = this->current_hour_;

    if (this->peak_hour_sensor_ != nullptr) {
      this->peak_hour_sensor_->publish_state(this->peak_hour_);
    }
    if (this->peak_hour_count_sensor_ != nullptr) {
      this->peak_hour_count_sensor_->publish_state(this->peak_hour_count_);
    }
  }
}

void HLKLD2415HComponent::set_current_hour(uint8_t hour) {
  if (hour != this->current_hour_ && hour < 24) {
    // Save current hour stats before switching
    this->hourly_counts_[this->current_hour_] = this->current_hour_count_;
    this->hourly_speed_sums_[this->current_hour_] = this->current_hour_speed_sum_;

    // Switch to new hour
    this->current_hour_ = hour;
    this->current_hour_count_ = this->hourly_counts_[hour];
    this->current_hour_speed_sum_ = this->hourly_speed_sums_[hour];

    ESP_LOGI(TAG, "Hour changed to %d (count: %d)", hour, this->current_hour_count_);

    // Update sensors
    if (this->current_hour_count_sensor_ != nullptr) {
      this->current_hour_count_sensor_->publish_state(this->current_hour_count_);
    }
    if (this->current_hour_avg_speed_sensor_ != nullptr && this->current_hour_count_ > 0) {
      this->current_hour_avg_speed_sensor_->publish_state(this->current_hour_speed_sum_ / this->current_hour_count_);
    }
  }
}

float HLKLD2415HComponent::calculate_percentile_85_() {
  if (this->speed_samples_.empty()) {
    return 0;
  }

  // Make a copy and sort
  std::vector<float> sorted = this->speed_samples_;
  std::sort(sorted.begin(), sorted.end());

  // Calculate 85th percentile index
  size_t index = (size_t)(sorted.size() * 0.85);
  if (index >= sorted.size()) {
    index = sorted.size() - 1;
  }

  return sorted[index];
}

void HLKLD2415HComponent::clear_detection_() {
  this->last_detection_time_ = 0;

  if (this->speed_sensor_ != nullptr) {
    this->speed_sensor_->publish_state(0);
  }

  if (this->vehicle_detected_binary_sensor_ != nullptr) {
    this->vehicle_detected_binary_sensor_->publish_state(false);
  }
}

void HLKLD2415HComponent::reset_statistics() {
  ESP_LOGI(TAG, "Resetting all statistics");

  // Reset basic stats
  this->vehicle_count_ = 0;
  this->approaching_count_ = 0;
  this->leaving_count_ = 0;
  this->speed_sum_ = 0;
  this->max_speed_ = 0;
  this->last_vehicle_time_ = 0;

  // Reset speed limit stats
  this->speeder_count_ = 0;
  this->worst_over_limit_ = 0;

  // Reset direction stats
  this->approaching_speed_sum_ = 0;
  this->leaving_speed_sum_ = 0;

  // Reset hourly stats
  for (int i = 0; i < 24; i++) {
    this->hourly_counts_[i] = 0;
    this->hourly_speed_sums_[i] = 0;
  }
  this->current_hour_count_ = 0;
  this->current_hour_speed_sum_ = 0;
  this->peak_hour_ = 0;
  this->peak_hour_count_ = 0;

  // Clear samples
  this->speed_samples_.clear();

  // Publish reset values
  if (this->vehicle_count_sensor_ != nullptr) this->vehicle_count_sensor_->publish_state(0);
  if (this->approaching_count_sensor_ != nullptr) this->approaching_count_sensor_->publish_state(0);
  if (this->leaving_count_sensor_ != nullptr) this->leaving_count_sensor_->publish_state(0);
  if (this->average_speed_sensor_ != nullptr) this->average_speed_sensor_->publish_state(0);
  if (this->max_speed_sensor_ != nullptr) this->max_speed_sensor_->publish_state(0);
  if (this->speeder_count_sensor_ != nullptr) this->speeder_count_sensor_->publish_state(0);
  if (this->violation_percentage_sensor_ != nullptr) this->violation_percentage_sensor_->publish_state(0);
  if (this->worst_speeder_sensor_ != nullptr) this->worst_speeder_sensor_->publish_state(0);
  if (this->avg_speed_approaching_sensor_ != nullptr) this->avg_speed_approaching_sensor_->publish_state(0);
  if (this->avg_speed_leaving_sensor_ != nullptr) this->avg_speed_leaving_sensor_->publish_state(0);
  if (this->current_hour_count_sensor_ != nullptr) this->current_hour_count_sensor_->publish_state(0);
  if (this->current_hour_avg_speed_sensor_ != nullptr) this->current_hour_avg_speed_sensor_->publish_state(0);
  if (this->peak_hour_sensor_ != nullptr) this->peak_hour_sensor_->publish_state(0);
  if (this->peak_hour_count_sensor_ != nullptr) this->peak_hour_count_sensor_->publish_state(0);
  if (this->percentile_85_speed_sensor_ != nullptr) this->percentile_85_speed_sensor_->publish_state(0);
}

}  // namespace hlk_ld2415h
}  // namespace esphome
