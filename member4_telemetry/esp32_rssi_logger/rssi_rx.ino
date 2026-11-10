/*
 * Member 4 — 2.4 GHz RSSI Receiver / Logger (ESP32-WROOM-32)
 * ==========================================================
 * Sits at the focal point of the copper Yagi-Uda boom, connects to the
 * beacon access point (beacon_tx.ino), and streams the measured RSSI (dBm)
 * over USB serial so serial_rssi_logger.py can record one value per 10 deg
 * turntable step.
 *
 * SERIAL PROTOCOL (115200 baud, newline-terminated)
 *   Every ~100 ms the board prints:   RSSI,<dBm>
 *   e.g.                              RSSI,-46
 *   The Python logger reads these, averages a burst at each angle, and
 *   writes data/empirical_pattern.csv.
 *
 * Keep SSID / password / channel identical to beacon_tx.ino.
 * Board: "ESP32 Dev Module" in Arduino IDE.
 */

#include <WiFi.h>

const char *AP_SSID     = "EMT_YAGI_BEACON";
const char *AP_PASSWORD = "yagi2440";

unsigned long lastReconnectAttempt = 0;

void connectToBeacon() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(AP_SSID, AP_PASSWORD);
  Serial.print("Connecting to ");
  Serial.print(AP_SSID);
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 10000) {
    delay(250);
    Serial.print(".");
  }
  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("Connected. RX IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("Connect FAILED (will retry).");
  }
}

void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println();
  Serial.println("=== EMT 2.4 GHz RSSI RX ===");
  connectToBeacon();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    // Non-blocking reconnect every 3 s.
    if (millis() - lastReconnectAttempt > 3000) {
      lastReconnectAttempt = millis();
      connectToBeacon();
    }
    Serial.println("RSSI,NaN");   // logger treats NaN as a dropped sample
    delay(100);
    return;
  }

  // WiFi.RSSI() returns the received signal strength of the AP link in dBm.
  long rssi = WiFi.RSSI();
  Serial.print("RSSI,");
  Serial.println(rssi);
  delay(100);   // ~10 samples/second
}
