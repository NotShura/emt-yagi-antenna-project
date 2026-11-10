# ESP32 RSSI Telemetry — Field-Sweep Toolkit

Two ESP32 sketches plus a Python logger that together capture the real 360°
radiation pattern of the copper Yagi and write `data/empirical_pattern.csv`.

| File | Runs on | Role |
|---|---|---|
| `beacon_tx.ino` | ESP32 #1 (far end) | Continuous 2.4 GHz beacon (SoftAP + 100 Hz UDP broadcast) on channel 7 ≈ 2.442 GHz |
| `rssi_rx.ino` | ESP32 #2 (Yagi focal point) | Connects to the beacon and streams `RSSI,<dBm>` over USB serial at ~10 Hz |
| `serial_rssi_logger.py` | Your laptop | Reads the serial stream, averages a burst per 10° step, writes the empirical CSV |

## Hardware setup

1. Flash `beacon_tx.ino` to ESP32 #1; place it at distance **R** from the
   antenna, where `R ≥ 2D²/λ` (run `python member4_telemetry/friis_link_budget.py`
   for the exact value — typically ~1.5 m here).
2. Flash `rssi_rx.ino` to ESP32 #2 and mount it at the focal point of the
   copper boom (behind the driven element). Keep it tethered to the laptop by USB.
3. Keep `AP_SSID`, `AP_PASSWORD`, and the channel identical in both sketches.

> Arduino IDE board: **ESP32 Dev Module**. Install the "esp32 by Espressif"
> boards package first.

## Capture the sweep

```bash
pip install pyserial          # one-time
python serial_rssi_logger.py --port COM5        # Windows
python serial_rssi_logger.py --port /dev/ttyUSB0 --dwell 3   # Linux/macOS
```

The script steps through 0°–350°. At each angle, rotate the turntable so the
**main beam points at that angle (0° = toward the directors)**, press Enter,
and it averages ~2 s of readings.

## Zero-purchase alternative (no ESP32)

Use a phone as the beacon (2.4 GHz hotspot) and a second phone running a free
Wi-Fi analyser as the meter, then type the dBm values in:

```bash
python serial_rssi_logger.py --manual
```

## Dry run (no hardware at all)

```bash
python serial_rssi_logger.py --dummy
```

All three modes produce the same `data/empirical_pattern.csv`, which Member 1's
GUI overlay and `friis_link_budget.py`'s error analysis pick up automatically.
