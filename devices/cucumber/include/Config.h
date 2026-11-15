#pragma once

// ============================================================
// demo_05_iot — Cucumber R (ESP32-S2) MQTT Config
// Publishes environmental sensor readings to the demo_05_iot
// mqtt_collector service, which stores them and serves them
// back over a REST API (viewable in a browser).
// ============================================================

// --- WiFi ---
#define WIFI_SSID           "YOUR_WIFI_NAME"
#include "secrets.h"  // defines WIFI_PASS and WIFI_PASS_FALLBACK (fallback tried if primary fails)
#define WIFI_TIMEOUT_MS     15000        // timeout per password attempt

// --- MQTT broker (mosquitto service from demo_05_iot's docker compose) ---
// Use your computer's LAN IP here (not "localhost" -- the board is a
// separate device on the network). Find it with `ipconfig getifaddr en1`.
#define MQTT_BROKER_IP   "192.168.1.100"  // <-- IP ของคอมพิวเตอร์ที่รัน gateway
#define MQTT_BROKER_PORT 1883
#define MQTT_CLIENT_ID   "cucumber_demo05" // must be unique per device on the broker
#define MQTT_TOPIC       "/cn466/data"     // matches mqtt_app.py's subscribe topic

// demo_05_iot's schema is {"node": <int>, "value": <float>} -- one message
// per numeric value, so each sensor reading gets its own node id.
#define NODE_BMP280_TEMP_C   1
#define NODE_BMP280_PRESSURE 2
#define NODE_HTS221_TEMP_C   3
#define NODE_HTS221_HUMIDITY 4

// --- I2C pins (Cucumber board, per official Gravitech pinout diagram) ---
// BMP280 @ 0x76, HTS221 @ 0x5F -- both on the same I2C0 bus.
#define SDA_PIN 41
#define SCL_PIN 40

// --- Timing ---
#define PUBLISH_INTERVAL_MS 3000
