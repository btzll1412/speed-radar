#include "hlk_ld2415h.h"
#include "esphome/core/log.h"

namespace esphome {
namespace hlk_ld2415h {

static const char *const TAG = "hlk_ld2415h";

void HLKLD2415HComponent::setup() {
  ESP_LOGCONFIG(TAG, "Setting up HLK-LD2415H...");
  this->buffer_.reserve(16);
}

void HLKLD2415HComponent::dump_config() {
  ESP_LOGCONFIG(TAG, "HLK-LD2415H:");
  ESP_LOGCONFIG(TAG, "  Min Speed Threshold: %.1f km/h", this->min_speed_threshold_);
  ESP_LOGCONFIG(TAG, "  Max Speed Threshold: %.1f km/h", this->max_speed_threshold_);
  LOG_SENSOR("  ", "Speed", this->speed_sensor_);
  LOG_TEXT_SENSOR("  ", "Direction", this->direction_text_sensor_);
  LOG_BINARY_SENSOR("  ", "Vehicle Detected", this->vehicle_detected_binary_sensor_);
  LOG_SENSOR("  ", "Vehicle Count", this->vehicle_count_sensor_);
  LOG_SENSOR("  ", "Approaching Count", this->approaching_count_sensor_);
  LOG_SENSOR("  ", "Leaving Count", this->leaving_count_sensor_);
  LOG_SENSOR("  ", "Average Speed", this->average_speed_sensor_);
  LOG_SENSOR("  ", "Max Speed", this->max_speed_sensor_);
}

void HLKLD2415HComponent::loop() {
  // Read all available data from UART
  while (this->available()) {
    uint8_t c;
    this->read_byte(&c);

    if (c == '\n') {
      // End of frame, parse it
      this->parse_data_();
      this->buffer_.clear();
    } else if (c != '\r') {
      // Add to buffer (ignore carriage return)
      if (this->buffer_.length() < 15) {
        this->buffer_ += static_cast<char>(c);
      }
    }
  }

  // Clear detection state if no data received for DETECTION_TIMEOUT_MS
  if (this->last_detection_time_ > 0 &&
      millis() - this->last_detection_time_ > DETECTION_TIMEOUT_MS) {
    this->clear_detection_();
  }
}

void HLKLD2415HComponent::parse_data_() {
  // Expected format: V+XXX.X or V-XXX.X
  // V = header
  // + = approaching, - = leaving
  // XXX.X = speed in km/h

  if (this->buffer_.length() < 7) {
    return;  // Too short
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

  // Parse speed value (characters 2 onwards)
  std::string speed_str = this->buffer_.substr(2);

  // Remove any trailing whitespace
  size_t end = speed_str.find_last_not_of(" \t\r\n");
  if (end != std::string::npos) {
    speed_str = speed_str.substr(0, end + 1);
  }

  float speed = 0;
  try {
    speed = std::stof(speed_str);
  } catch (...) {
    ESP_LOGW(TAG, "Failed to parse speed: %s", speed_str.c_str());
    return;
  }

  // Apply speed thresholds to filter pedestrians and noise
  if (speed < this->min_speed_threshold_) {
    ESP_LOGV(TAG, "Speed %.1f km/h below threshold (%.1f), ignoring (likely pedestrian)",
             speed, this->min_speed_threshold_);
    return;
  }

  if (speed > this->max_speed_threshold_) {
    ESP_LOGW(TAG, "Speed %.1f km/h above max threshold (%.1f), ignoring (likely noise)",
             speed, this->max_speed_threshold_);
    return;
  }

  ESP_LOGD(TAG, "Vehicle speed: %.1f km/h, Direction: %s", speed, approaching ? "approaching" : "leaving");

  this->process_speed_(speed, approaching);
}

void HLKLD2415HComponent::process_speed_(float speed, bool approaching) {
  uint32_t now = millis();

  // Check if this is a new vehicle (gap since last detection)
  bool is_new_vehicle = (this->last_vehicle_time_ == 0 ||
                         now - this->last_vehicle_time_ > VEHICLE_GAP_MS ||
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
    this->last_vehicle_time_ = now;
  } else {
    // Update max speed for current vehicle if higher
    if (speed > this->last_speed_) {
      // Update max if this reading is higher than previous max
      if (speed > this->max_speed_) {
        this->max_speed_ = speed;
        if (this->max_speed_sensor_ != nullptr) {
          this->max_speed_sensor_->publish_state(this->max_speed_);
        }
      }
    }
  }
}

void HLKLD2415HComponent::update_statistics_(float speed, bool approaching) {
  // Increment counts
  this->vehicle_count_++;
  if (approaching) {
    this->approaching_count_++;
  } else {
    this->leaving_count_++;
  }

  // Update speed sum for average calculation
  this->speed_sum_ += speed;

  // Update max speed
  if (speed > this->max_speed_) {
    this->max_speed_ = speed;
  }

  // Publish statistics
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
    float avg = this->speed_sum_ / this->vehicle_count_;
    this->average_speed_sensor_->publish_state(avg);
  }

  if (this->max_speed_sensor_ != nullptr) {
    this->max_speed_sensor_->publish_state(this->max_speed_);
  }

  ESP_LOGI(TAG, "New vehicle #%d: %.1f km/h %s (avg: %.1f, max: %.1f)",
           this->vehicle_count_, speed, approaching ? "approaching" : "leaving",
           this->speed_sum_ / this->vehicle_count_, this->max_speed_);
}

void HLKLD2415HComponent::clear_detection_() {
  this->last_detection_time_ = 0;

  // Clear speed to 0
  if (this->speed_sensor_ != nullptr) {
    this->speed_sensor_->publish_state(0);
  }

  // Clear vehicle detected
  if (this->vehicle_detected_binary_sensor_ != nullptr) {
    this->vehicle_detected_binary_sensor_->publish_state(false);
  }
}

void HLKLD2415HComponent::reset_statistics() {
  ESP_LOGI(TAG, "Resetting statistics");

  this->vehicle_count_ = 0;
  this->approaching_count_ = 0;
  this->leaving_count_ = 0;
  this->speed_sum_ = 0;
  this->max_speed_ = 0;
  this->last_vehicle_time_ = 0;

  // Publish reset values
  if (this->vehicle_count_sensor_ != nullptr) {
    this->vehicle_count_sensor_->publish_state(0);
  }
  if (this->approaching_count_sensor_ != nullptr) {
    this->approaching_count_sensor_->publish_state(0);
  }
  if (this->leaving_count_sensor_ != nullptr) {
    this->leaving_count_sensor_->publish_state(0);
  }
  if (this->average_speed_sensor_ != nullptr) {
    this->average_speed_sensor_->publish_state(0);
  }
  if (this->max_speed_sensor_ != nullptr) {
    this->max_speed_sensor_->publish_state(0);
  }
}

}  // namespace hlk_ld2415h
}  // namespace esphome
