#!/usr/bin/with-contenv bashio
# Speed Radar Hub - Startup Script

# Get configuration from Home Assistant
export MQTT_HOST=$(bashio::config 'mqtt_host')
export MQTT_PORT=$(bashio::config 'mqtt_port')
export MQTT_USERNAME=$(bashio::config 'mqtt_username')
export MQTT_PASSWORD=$(bashio::config 'mqtt_password')
export EXTERNAL_URL=$(bashio::config 'external_url')
export INTERNAL_URL=$(bashio::config 'internal_url')
export DATA_RETENTION_DAYS=$(bashio::config 'data_retention_days')
export TIMEZONE=$(bashio::config 'timezone')

# Get Ingress configuration
export INGRESS_PATH=$(bashio::addon.ingress_entry)

# Database path (persistent storage)
export DATABASE_PATH="/config/speed_radar_hub.db"

# Log startup
bashio::log.info "Starting Speed Radar Hub..."
bashio::log.info "MQTT Host: ${MQTT_HOST}:${MQTT_PORT}"
bashio::log.info "Ingress Path: ${INGRESS_PATH}"

# Start the FastAPI application
cd /app
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8103 --log-level info
