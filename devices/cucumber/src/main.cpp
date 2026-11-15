#include <Arduino.h>
#include <WiFi.h>
#include <Wire.h>
#include <PubSubClient.h>
#include <Adafruit_BMP280.h>
#include <Adafruit_HTS221.h>
#include "Config.h"

// ============================================================
// demo_05_iot -- Cucumber R (ESP32-S2)
// ============================================================
// setup(): connect WiFi, connect to the mosquitto service from
//          demo_05_iot's docker compose over MQTT
// loop():  read BMP280 (temp/pressure) + HTS221 (temp/humidity)
//          every PUBLISH_INTERVAL_MS, publish each value as its
//          own {"node":<id>,"value":<v>} message to /cn466/data
//          so mqtt_collector stores it and rest_app can serve it
//          back at GET /items/<id>.
// ============================================================

Adafruit_BMP280 bmp;
Adafruit_HTS221 hts;
bool bmpReady = false;
bool htsReady = false;

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

static uint32_t lastPublish = 0;

// Why the last attempt failed: scan for the target SSID and print what the radio can see.
void diagnoseWiFi() {
    Serial.printf("[WiFi] status=%d (1=no SSID, 4=connect failed, 6=disconnected)\n", (int)WiFi.status());
    int n = WiFi.scanNetworks();
    Serial.printf("[WiFi] scan: %d networks\n", n);
    bool seen = false;
    for (int i = 0; i < n; i++) {
        if (WiFi.SSID(i) == WIFI_SSID) {
            seen = true;
            Serial.printf("[WiFi]   %s RSSI=%d ch=%d auth=%d\n", WiFi.SSID(i).c_str(), WiFi.RSSI(i),
                          WiFi.channel(i), (int)WiFi.encryptionType(i));
        }
    }
    if (!seen) Serial.printf("[WiFi]   '%s' NOT visible to the board\n", WIFI_SSID);
}

bool tryWiFiPassword(const char *password) {
    Serial.printf("[WiFi] Connecting to %s", WIFI_SSID);
    WiFi.disconnect(true);
    delay(300);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, password);

    uint32_t start = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - start < WIFI_TIMEOUT_MS) {
        delay(300);
        Serial.print(".");
    }
    Serial.println();
    return WiFi.status() == WL_CONNECTED;
}

void connectWiFi() {
    bool ok = tryWiFiPassword(WIFI_PASS);
    if (!ok) {
        Serial.println("[WiFi] Primary password failed, trying fallback...");
        ok = tryWiFiPassword(WIFI_PASS_FALLBACK);
    }
    if (!ok) {
        diagnoseWiFi();
        Serial.println("[WiFi] FAILED with either password. Restarting...");
        delay(2000);
        ESP.restart();
    }
    Serial.println("[WiFi] Connected successfully!");
    Serial.print("[WiFi] IP address: ");
    Serial.println(WiFi.localIP());
}

void connectMQTT() {
    mqtt.setServer(MQTT_BROKER_IP, MQTT_BROKER_PORT);
    while (!mqtt.connected()) {
        Serial.printf("[MQTT] Connecting to %s:%d as %s ... ",
                      MQTT_BROKER_IP, MQTT_BROKER_PORT, MQTT_CLIENT_ID);
        if (mqtt.connect(MQTT_CLIENT_ID)) {
            Serial.println("connected");
        } else {
            Serial.printf("failed, rc=%d. Retrying in 2s\n", mqtt.state());
            delay(2000);
        }
    }
}

void publishNodeValue(int node, float value) {
    char payload[64];
    snprintf(payload, sizeof(payload), "{\"node\":%d,\"value\":%.2f}", node, value);
    mqtt.publish(MQTT_TOPIC, payload);
    Serial.printf("[MQTT] Published -> %s: %s\n", MQTT_TOPIC, payload);
}

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("\n\n[BOOT] demo_05_iot -- BMP280 + HTS221 -> MQTT -> REST");

    WiFi.onEvent([](arduino_event_id_t, arduino_event_info_t info) {
        Serial.printf("[WiFi] disconnect reason=%d (15=bad password, 201=AP not found, 2=auth expired)\n",
                      info.wifi_sta_disconnected.reason);
    }, ARDUINO_EVENT_WIFI_STA_DISCONNECTED);

    Wire.begin(SDA_PIN, SCL_PIN);

    bmpReady = bmp.begin(0x76) || bmp.begin(0x77);
    if (bmpReady) {
        bmp.setSampling(Adafruit_BMP280::MODE_NORMAL,
                         Adafruit_BMP280::SAMPLING_X2,
                         Adafruit_BMP280::SAMPLING_X16,
                         Adafruit_BMP280::FILTER_X16,
                         Adafruit_BMP280::STANDBY_MS_500);
        Serial.println("[BMP280] Init OK");
    } else {
        Serial.println("[BMP280] ERROR: sensor not found");
    }

    htsReady = hts.begin_I2C();
    if (htsReady) {
        Serial.println("[HTS221] Init OK");
    } else {
        Serial.println("[HTS221] ERROR: sensor not found");
    }

    connectWiFi();
    connectMQTT();
}

void loop() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[WiFi] Disconnected! Reconnecting...");
        connectWiFi();
    }
    if (!mqtt.connected()) {
        connectMQTT();
    }
    mqtt.loop();

    if (millis() - lastPublish >= PUBLISH_INTERVAL_MS) {
        lastPublish = millis();

        float bmpTemp = 0, bmpPressure = 0;
        if (bmpReady) {
            bmpTemp = bmp.readTemperature();
            bmpPressure = bmp.readPressure() / 100.0F; // Pa -> hPa
        }

        float htsTemp = 0, htsHumidity = 0;
        if (htsReady) {
            sensors_event_t humEvent, tempEvent;
            hts.getEvent(&humEvent, &tempEvent);
            htsTemp = tempEvent.temperature;
            htsHumidity = humEvent.relative_humidity;
        }

        Serial.printf("[Sensor] BMP280: T=%.2f C, P=%.2f hPa | HTS221: T=%.2f C, RH=%.2f %%\n",
                      bmpTemp, bmpPressure, htsTemp, htsHumidity);

        if (bmpReady) {
            publishNodeValue(NODE_BMP280_TEMP_C, bmpTemp);
            publishNodeValue(NODE_BMP280_PRESSURE, bmpPressure);
        }
        if (htsReady) {
            publishNodeValue(NODE_HTS221_TEMP_C, htsTemp);
            publishNodeValue(NODE_HTS221_HUMIDITY, htsHumidity);
        }
    }
}
