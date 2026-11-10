/*
 * Member 4 — 2.4 GHz Beacon Transmitter (ESP32-WROOM-32)
 * ======================================================
 * Turns an ESP32 into a continuous 2.4 GHz packet beacon so the receiver
 * board (rssi_rx.ino) always has a steady signal whose RSSI can be logged
 * while the antenna-under-test is rotated through 360 deg.
 *
 * It starts a SoftAP (an access point). An access point broadcasts Wi-Fi
 * beacon frames ~10x per second on its own, and we also broadcast a small
 * UDP packet continuously so the RSSI reading stays fresh and stable.
 *
 * WIRING / USE
 *   - Flash this to the ESP32 that sits with the TRANSMIT antenna (or the
 *     reference whip). Place it ~R meters away (see friis_link_budget.py).
 *   - Flash rssi_rx.ino to the ESP32 at the Yagi focal point.
 *   - Keep SSID/channel identical on both sketches.
 *
 * Board: "ESP32 Dev Module" in Arduino IDE. Channel 7 ~= 2.442 GHz,
 * matching the design freeze f0 = 2.44 GHz.
 */

#include <WiFi.h>
#include <WiFiUdp.h>

const char *AP_SSID     = "EMT_YAGI_BEACON";
const char *AP_PASSWORD = "yagi2440";   // >= 8 chars required by SoftAP
const int   WIFI_CHANNEL = 7;           // 2.442 GHz (design f0 = 2.44 GHz)

WiFiUDP udp;
const IPAddress BROADCAST_IP(192, 168, 4, 255);
const uint16_t  BEACON_PORT = 4210;

unsigned long packetCount = 0;

void setup() {
  Serial.begin(115200);
  delay(200);

  // SoftAP on a fixed channel. ssid_hidden=0, max_connection=4.
  WiFi.mode(WIFI_AP);
  bool ok = WiFi.softAP(AP_SSID, AP_PASSWORD, WIFI_CHANNEL, 0, 4);
  // Push TX power to maximum for a strong, stable far-field signal.
  WiFi.setTxPower(WIFI_POWER_19_5dBm);

  udp.begin(BEACON_PORT);

  Serial.println();
  Serial.println("=== EMT 2.4 GHz Beacon TX ===");
  Serial.print("SoftAP start: "); Serial.println(ok ? "OK" : "FAILED");
  Serial.print("SSID    : "); Serial.println(AP_SSID);
  Serial.print("Channel : "); Serial.println(WIFI_CHANNEL);
  Serial.print("AP IP   : "); Serial.println(WiFi.softAPIP());
  Serial.println("Broadcasting beacon packets at 100 Hz...");
}

void loop() {
  // Continuous UDP broadcast so the RX always has a recent packet to read.
  udp.beginPacket(BROADCAST_IP, BEACON_PORT);
  udp.print("EMT_YAGI_BEACON ");
  udp.print(packetCount++);
  udp.endPacket();

  if (packetCount % 500 == 0) {
    Serial.print("beacons sent: ");
    Serial.println(packetCount);
  }
  delay(10);   // ~100 packets/second
}
