
<!-- START OF 05_MQTT_PROTOCOL.md -->
# 📡 MQTT Protocol Design — Lindu.id

## Broker Configuration

| Parameter | Value |
|-----------|-------|
| Host | mqtt.lindu.id |
| TLS Port | 8883 |
| Local Port | 1883 (internal only) |
| Protocol | MQTT 3.1.1 / 5.0 |
| TLS | TLS 1.2/1.3 (Let's Encrypt cert) |
| Auth | Username/Password + Client Certificate |
| Keepalive | 60 seconds |
| Max Packet Size | 256 KB |
| QoS Support | 0, 1, 2 |

---

## Topic Hierarchy

```text
lindu/
├── system/
│   ├── health           → System health broadcast
│   └── time             → NTP time sync broadcast (optional)
│
├── sensor/
│   ├── {node_id}/
│   │   ├── metrics      → Raw sensor data (10 Hz)
│   │   ├── status       → Node heartbeat (Online/Offline LWT)
│   │   └── event        → Local vibration detection event
│   └── all/metrics      → Aggregated (retained, last known)
│
├── actuator/
│   ├── {actuator_id}/
│   │   └── status       → Actuator state (door open/closed, valve)
│   └── cmd/all          → Broadcast GLOBAL ALARM (calculated via Edge Haversine)
│
└── alert/
    ├── external         → Alert from BMKG/JMA
    └── system           → System-level alerts (node offline, etc.)
```

---

## Topic Details & Payloads

### `lindu/sensor/{node_id}/metrics`
**Publisher:** Sensor Node  
**Subscriber:** Consensus Engine (Paho-MQTT)
**QoS:** 1 (at least once)  
**Retain:** false  
**Rate:** 10 Hz (100ms interval) → burst mode during vibration detection  

```json
{
  "node_id": "node1",
  "ts": 1725379200.123,
  "seq": 12345,
  "accel": { "x": 0.012, "y": -0.003, "z": 9.812 },
  "gyro":  { "x": 0.001, "y": 0.002,  "z": -0.001 },
  "pga": 0.015,
  "sta_lta": 1.2,
  "vibration": false,
  "rssi": -65,
  "battery_pct": 98,
  "uptime_s": 3600
}
```

### `lindu/sensor/{node_id}/status`
**Publisher:** Sensor Node  
**QoS:** 1  
**Retain:** true (last known state)  
**Rate:** Every 30 seconds (heartbeat)  

```json
{
  "node_id": "node1",
  "ts": 1725379200.000,
  "status": "online",
  "firmware_version": "1.2.0",
  "wifi_rssi": -65,
  "battery_pct": 98,
  "uptime_s": 3600,
  "ip": "192.168.1.101",
  "location": {
    "name": "Living Room Building A",
    "lat": -6.2000,
    "lon": 106.8160
  }
}
```

### `lindu/sensor/{node_id}/event`
**Publisher:** Sensor Node  
**QoS:** 2 (exactly once — critical)  
**Retain:** false  
**Trigger:** Only upon local vibration detection  

```json
{
  "node_id": "node1",
  "ts": 1725379200.050,
  "event_type": "vibration_detected",
  "pga_peak": 0.125,
  "sta_lta_peak": 4.8,
  "duration_ms": 250,
  "axis_dominant": "Z",
  "raw_window": [...]
}
```

### `lindu/actuator/cmd/all` (Global Broadcast Alarm)
**Publisher:** Consensus Engine / Server
**Subscriber:** All Nodes (Sensor & Actuator)
**QoS:** 2 (exactly once — critical)  
**Retain:** true (5 minutes, then clear)  

**Note:** Messages are sent globally. The calculation of the danger radius (*Edge Geospatial Filtering*) is executed at the Edge Node using the Haversine formula.

```json
{
  "cmd": "ALARM_ON",
  "level": "CRITICAL",
  "confidence": 100,
  "desc": "EEW from JMA (M7.2)",
  "epi_lat": -6.200,
  "epi_lon": 106.816,
  "radius_km": 100,
  "magnitude": 7.2
}
```

### `lindu/alert/external`
**Publisher:** API Integrator  
**Subscriber:** Consensus Engine, Dashboard (React/Flask)
**QoS:** 1  

```json
{
  "source": "bmkg",
  "ts": 1725379100.000,
  "magnitude": 5.5,
  "depth_km": 15,
  "epi_lat": -6.100,
  "epi_lon": 106.900,
  "radius_km": 100,
  "location_desc": "10 km Southwest of Jakarta",
  "tsunami_warning": false
}
```

---

## QoS Strategy

| Topic | QoS | Reason |
|-------|-----|--------|
| sensor metrics | 1 | High frequency, loss acceptable |
| sensor status | 1 | Heartbeat, occasional loss ok |
| sensor event | 2 | Critical detection, no loss |
| alert/earthquake | 2 | Life-critical alert |
| alert/external | 1 | Informational |
| cmd/exec | 2 | Command must arrive exactly once |
| actuator/ack | 1 | Confirmation, retryable |

---

## Retained Messages Strategy

| Topic | Retain | TTL |
|-------|--------|-----|
| sensor/{id}/status | ✅ Yes | Until new update |
| actuator/{id}/status | ✅ Yes | Until new update |
| alert/earthquake | ✅ Yes | 5 minutes (delete after) |
| sensor/{id}/metrics | ❌ No | Too much/frequent |

---

## MQTT Security

### TLS Configuration
```
# Mosquitto config (mosquitto.conf)
listener 8883
cafile   /etc/mosquitto/certs/ca.crt
certfile /etc/mosquitto/certs/server.crt
keyfile  /etc/mosquitto/certs/server.key
tls_version tlsv1.2
require_certificate false  # Client cert optional
allow_anonymous false
password_file /etc/mosquitto/passwd
```

### Client Authentication (ESP32)
```cpp
// Sensor node MQTT connection
mqttClient.setServer("mqtt.lindu.id", 8883);
mqttClient.setCredentials("node1", "secret_password_here");
mqttClient.setCACert(ca_cert_pem);   // Server CA cert embedded
```

### ACL (Access Control List)
```
# Sensor nodes: can only publish to sensor topic, subscribe to alert+cmd
user node1
topic write lindu/sensor/node1/#
topic read lindu/alert/#
topic read lindu/cmd/node1/#
topic read lindu/system/#

# Actuator: only subscribe to alert/cmd, publish ack
user actuator1
topic read lindu/alert/#
topic read lindu/cmd/actuator1/#
topic write lindu/actuator/actuator1/#

# Consensus engine: full access
user consensus_engine
topic readwrite lindu/#
```

---

## Connection & Reconnect Strategy (ESP32)

```cpp
void reconnectMQTT() {
    int retries = 0;
    while (!mqttClient.connected() && retries < 5) {
        if (mqttClient.connect(CLIENT_ID, USERNAME, PASSWORD)) {
            // Resubscribe after reconnect
            mqttClient.subscribe("lindu/alert/#", 2);
            mqttClient.subscribe("lindu/cmd/" + nodeId + "/#", 2);
            publishStatus("online");
        } else {
            delay(5000 * (retries + 1));  // Exponential backoff
            retries++;
        }
    }
}

// Will message (LWT) — send on sudden disconnect
String willTopic = "lindu/sensor/" + nodeId + "/status";
String willPayload = "{\"status\":\"offline\",\"node_id\":\"" + nodeId + "\"}";
mqttClient.setWill(willTopic.c_str(), willPayload.c_str(), 1, true);
```


---

<!-- START OF 17_MQTT_MAPPING.md -->
# 📡 MQTT Command & Topic Mapping — lindu.id

This document is the **API Contract** for all IoT communication in the Lindu.id system. All components (Sensor Nodes, Actuator Nodes, Python Server, and React Dashboard) communicate purely through the MQTT Broker using the following JSON structures.

---

## 1. Communication Topics (*Topic Tree*)
The system uses the primary `lindu/` namespace.

| Topic | Data Flow Direction | Function |
|-------|------------------|--------|
| `lindu/sensor/+/status` | Node ➡️ Server & UI | Liveness heartbeat & GPS/Pose reporting from the Node. UPSERTed to PostgreSQL. |
| `lindu/sensor/+/event` | Node ➡️ Server & UI | Seismic vibration report (only sent during an earthquake, streaming PGA & RMS). |
| `lindu/actuator/cmd/all`| Server ➡️ Actuator & UI | Global command to activate/deactivate Sirens. |

*(The `+` is an MQTT wildcard representing a unique `node_id`, for example, `node_jkt_01`)*.

---

## 2. Payload Structure (JSON Mappings)

### A. Heartbeat / Liveness (Status)
Sent by the Sensor Node every few seconds to inform the system that the device is healthy, has power, and provides its coordinates and physical orientation. Data is UPSERTed into a Dockerized PostgreSQL database.

*   **Topic Example:** `lindu/sensor/node_01/status`
*   **Publisher:** ESP32 Sensor Node
*   **Subscriber:** Python Consensus Engine, Web Dashboard
*   **Payload JSON:**
```json
{
  "node_id": "node_01",
  "status": "online",
  "lat": -6.2088,
  "lon": 106.8456,
  "pose": "Flat",
  "tilt_angle": 2.5
}
```
*(Note: If the device dies due to a power outage during an earthquake, the MQTT broker will automatically send the same message with status `"offline"` using the `Last Will and Testament (LWT)` feature).*

### B. Seismic Telemetry (Event — Streaming Mode)
Sent by the ESP32 Sensor when the STA/LTA algorithm detects an earthquake. Unlike conventional systems that only send 1 notification, Lindu.id uses **Telemetry Mode**: the sensor will continuously stream data every **1 second** while the earthquake is ongoing, and will only stop if vibrations subside for **10 consecutive seconds**.

*   **Topic Example:** `lindu/sensor/node_01/event`
*   **Publisher:** ESP32 Sensor Node
*   **Subscriber:** Python Consensus Engine, Web Dashboard
*   **Frequency:** Every 1 second while Telemetry Mode is active
*   **Payload JSON:**
```json
{
  "node_id": "node_01",
  "ts": 1725432225,
  "uptime": 125400,
  "pga": 0.52,
  "rms": 0.35,
  "sta_lta": 12.4,
  "freq_hz": 7,
  "ax": 0.31,
  "ay": -0.12,
  "az": 0.48,
  "lat": -6.2088,
  "lon": 106.8456
}
```

| Field | Type | Description |
|-------|------|------------|
| `ts` | ulong | **Unix Epoch** (seconds since Jan 1 1970). Synced via NTP `pool.ntp.org`. 0 if NTP fails. |
| `uptime` | ulong | Time since boot (milliseconds). Fallback if NTP fails, useful for relative correlation. |
| `pga` | float | Peak Ground Acceleration in G scale (0.0 = calm, 1.0 = very strong) |
| `rms` | float | Root Mean Square acceleration in G scale |
| `sta_lta` | float | Short-term vs long-term energy ratio (>5.0 = seismic anomaly) |
| `freq_hz` | int | Dominant frequency from ZCR (1-10 Hz = earthquake, >20 Hz = truck/machinery) |
| `ax, ay, az` | float | 3-axis dynamic acceleration in m/s² (gravity removed via DC Offset) |
| `lat, lon` | float | Sender's GPS coordinates. Included in every message so data is *self-contained*. |


### C. Global Actuator Command (Alarm & Control)
Sent exclusively by the Python Server after validating the Physics Law of Earthquake Propagation Speed from multiple sensors. Controls all actuators (sirens, doors) in the field.

*   **Topic Example:** `lindu/actuator/cmd/all`
*   **Publisher:** Python Consensus Engine
*   **Subscriber:** ESP32 Actuator Node, Web Dashboard
*   **Payload JSON (Turn ON Alarm):**
```json
{
  "cmd": "ALARM_ON",
  "epi_lat": -6.2088,
  "epi_lon": 106.8456,
  "radius_km": 150,
  "desc": "Earthquake Detected!"
}
```

*   **Payload JSON (Turn OFF Alarm):**
```json
{
  "cmd": "ALARM_OFF"
}
```
*(Explanation: The Actuator Node will calculate its distance (based on its NVS GPS) to `epi_lat` and `epi_lon`. If its distance is under `radius_km`, the relay/siren will activate).*

---

## 3. Command Mapping List (CMD)

| Command (`cmd`) | Additional Parameters | Effect on Actuator (Hardware) | Effect on React Dashboard (Geoshake-style UI) |
|------------------|--------------------|-------------------------------|--------------------------|
| `ALARM_ON` | `epi_lat, epi_lon, radius_km` | Siren Relay Active (ON) IF within the radius zone. | Animated epicenters appear, PGA-based color-coded nodes flash red, Helicorder 24h mockup records event. |
| `ALARM_OFF` | (None) | Siren Relay Off (OFF). System silent. | Warning screens dismissed, Node Detail Modals return to normal. |
| `UPDATE_FIRMWARE` | `version` (e.g., "v1.2.0") | Sensor Node downloads `.bin` from Cloud for OTA. | N/A |
| `RESET` | (None) | Force restarts the ESP32 (*Soft Reboot*). | N/A |

---

## 4. Security and Quality of Service (QoS)
All critical messages (like `ALARM_ON` and `event`) are published using **QoS 1 (At Least Once)** to ensure messages are not lost over poor cellular/WiFi networks during a disaster. The `status` message can use QoS 0 (Fire and Forget) to save bandwidth.


---

<!-- START OF 16_DATABASE_SCHEMA.md -->
# 🗄️ Database Schema & Telemetry — Lindu.id

## 1. Database Architecture (Time-Series)

The Lindu.id system handles thousands of data logs per second during an earthquake. Traditional databases like MySQL would bottleneck during mass-insert operations.

Therefore, this system is designed using **Dockerized PostgreSQL** extended with **TimescaleDB** (a PostgreSQL extension optimized for Time-Series Data). Its main feature is **Hypertables**, which automatically partition data by time to maintain lightning-fast read/write speeds even when data reaches billions of rows.

---

## 2. Master Table (Relational)

This table stores static data from the devices in the field.

### `tb_nodes`
| Column | Data Type | Description |
|-------|-----------|------------|
| `node_id` | `VARCHAR(32)` | Primary Key (Example: `node_001`) |
| `role` | `VARCHAR(16)` | `sensor` or `actuator` |
| `lat` | `DOUBLE PRECISION` | Latitude (High-precision GPS coordinate) |
| `lon` | `DOUBLE PRECISION` | Longitude (High-precision GPS coordinate) |
| `fw_version` | `VARCHAR(16)` | Firmware version (Example: `v1.2.0`) |
| `pose` | `VARCHAR(16)` | Sensor orientation (e.g., `Flat`, `Wall`) |
| `tilt_angle` | `FLOAT` | Measured tilt angle |
| `registered_at`| `TIMESTAMPTZ` | Time the device was first registered |

---

## 3. Hypertable (Time-Series)

These tables receive continuous streaming data and are automatically partitioned by TimescaleDB based on the `timestamp`.

### `tb_sensor_events`
Records crucial moments when a Node detects a local shock. Vital for TDOA/Geiger algorithm calculations and seismic wave propagation speed research.

| Column | Data Type | Description |
|-------|-----------|------------|
| `time_event` | `TIMESTAMPTZ(3)` | Shock time (Millisecond precision) |
| `node_id` | `VARCHAR(32)` | Foreign Key to `tb_nodes` |
| `pga` | `FLOAT` | Peak Ground Acceleration |
| `rms` | `FLOAT` | Root Mean Square acceleration |
| `sta_lta`| `FLOAT` | P-Wave seismic wave detection ratio |
| `freq_hz` | `INTEGER` | Dominant vibration frequency (ZCR) |
| `is_confirmed` | `BOOLEAN` | True if validated as an earthquake, False if a truck passed by |

### `tb_sensor_telemetry` ⭐ NEW
Second-by-second recording during an earthquake (**Telemetry Mode**). This is the "black box" of raw data allowing post-earthquake research and seismic wave reconstruction.

| Column | Data Type | Description |
|-------|-----------|------------|
| `ts` | `TIMESTAMPTZ(3)` | Measurement time (from NTP, millisecond precision) |
| `node_id` | `VARCHAR(32)` | Node sending the data |
| `pga` | `FLOAT` | Current Peak Ground Acceleration (g) |
| `rms` | `FLOAT` | Current Root Mean Square acceleration (g) |
| `sta_lta` | `FLOAT` | Current STA/LTA energy ratio |
| `freq_hz` | `INTEGER` | Dominant vibration frequency from ZCR (Hz) |
| `ax` | `FLOAT` | Dynamic acceleration X-axis (m/s², gravity removed) |
| `ay` | `FLOAT` | Dynamic acceleration Y-axis |
| `az` | `FLOAT` | Dynamic acceleration Z-axis |
| `lat` | `DOUBLE PRECISION` | Sensor Latitude coordinate |
| `lon` | `DOUBLE PRECISION` | Sensor Longitude coordinate |
| `uptime_ms` | `BIGINT` | Time since the device was powered on (milliseconds) |

### `tb_system_alerts`
Historical record ("Black Box") of exactly when the Server sounded the global siren, and where the trigger originated.

| Column | Data Type | Description |
|-------|-----------|------------|
| `time_alert` | `TIMESTAMPTZ(3)` | Exact time the server sent the Broadcast instruction |
| `source` | `VARCHAR(32)` | Trigger: `LOCAL_CONSENSUS`, `BMKG_EEW`, `JMA_EEW` |
| `epi_lat` | `DOUBLE PRECISION` | Predicted earthquake epicenter Latitude |
| `epi_lon` | `DOUBLE PRECISION` | Predicted earthquake epicenter Longitude |
| `radius_km` | `FLOAT` | Target danger radius |
| `description` | `TEXT` | Event description (e.g., "Earthquake validated by node_01 and node_02") |

### `tb_node_telemetry`
Records the health status ("Health Check") of the Node every few minutes, as well as instant death logs (LWT).

| Column | Data Type | Description |
|-------|-----------|------------|
| `time_log` | `TIMESTAMPTZ` | Log time |
| `node_id` | `VARCHAR(32)` | Reporting node |
| `status` | `VARCHAR(16)` | `ONLINE`, `OFFLINE` (from MQTT LWT) |
| `wifi_rssi` | `INTEGER` | WiFi signal strength (dBm) |
| `batt_voltage` | `FLOAT` | Remaining battery/backup UPS voltage |

---

## 4. Reporting & Forensics Advantages

With this database schema, the Lindu.id Server can present various critical analyses on the **React Web Dashboard** using its **Geoshake-style UI** (Animated epicenters, PGA-based color-coded nodes, Helicorder 24h mockup, RMS & PGA metrics, Node Detail Modals):

1. **Earthquake Replay (Visualization):** Retrieves data from `tb_sensor_events` and plots it on a Map to see how earthquake waves propagate across the island second by second.
2. **Network Death Analysis (Damage Assessment):** If a query in `tb_node_telemetry` shows 500 Nodes in Cianjur changed status to `OFFLINE` within 2 seconds after an earthquake, agencies can conclude a **massive electrical blackout or cut optical fiber in Cianjur**, indicating severe regional damage.
3. **Algorithm Optimization:** Geologists and Data Scientists can pull `is_confirmed = False` data (false shocks) to retrain the AI (Machine Learning) so the device can better distinguish genuine earthquakes from passing heavy trucks.

---

## 5. Storage Efficiency Strategy (Data Retention & Downsampling)

To prevent the server's hard drive from filling up due to an IoT "Data Tsunami", the Lindu.id system implements 2 Lines of Storage Defense:

### A. Edge Defense (Node Level)
The ESP32 **DOES NOT** continuously stream vibration data to the server. Around 99.9% of accelerometer data (safe status) is discarded locally in the ESP32's RAM. The node only sends an event log (`sensor_events`) when it detects an anomaly.

### B. Database Defense (TimescaleDB Level)
For incoming data, TimescaleDB runs automated background routines:
1. **Continuous Aggregates (Downsampling):** Voltage/signal telemetry data older than 7 days is automatically aggregated from *minute* resolution to *hour/day* resolution. Annual charts remain viewable but consume 99% less storage.
2. **Native Compression:** Historical data (e.g., > 30 days) is compressed in a *Columnar* format, reducing data size by **90-95%**.
3. **Automated Drop Chunks:** Retention Policy. `tb_node_telemetry` logs older than 30 days are permanently deleted (as old health checks lose value). However, `tb_sensor_events` and `tb_system_alerts` (Earthquake Records) are set to be **kept forever** for geological history research.

---

## 6. Device Lifecycle & Mobility (Relocation)

The Lindu.id system is designed to be dynamic (Plug-and-Play). If a user moves a device from Jakarta to Bandung, they simply reconfigure the WiFi, GPS coordinates, and pose through the device's Captive Portal.

To prevent data duplication when the device powers back on and reports to the Server, the database implements an **UPSERT (Update or Insert)** logic. When the Node publishes the `lindu/sensor/<id>/status` payload, the Server executes the following SQL command:

```sql
INSERT INTO tb_nodes (node_id, role, lat, lon, pose, tilt_angle)
VALUES ('node_001', 'sensor', -6.9, 107.6, 'Flat', 2.5)
ON CONFLICT (node_id) 
DO UPDATE SET 
    lat = EXCLUDED.lat, 
    lon = EXCLUDED.lon,
    pose = EXCLUDED.pose,
    tilt_angle = EXCLUDED.tilt_angle;
```

**Impact:** The device's location pin on the React Web Dashboard map will instantly shift to the new city in real-time, ensuring subsequent earthquake radius calculations use the most up-to-date geographical location and orientation.


---

<!-- START OF 07_EXTERNAL_API.md -->
# 🌐 External API Integration — Lindu.id

## Overview

Lindu.id integrates two official government earthquake data sources to supplement our internal sensor network. All data, including sensor telemetry and external API events, is stored in a PostgreSQL (Dockerized) database. The data is visualized on our React Dashboard, which now features a "Geoshake-style" UI (Animated epicenters, PGA-based color-coded nodes, Helicorder 24h mockup, RMS & PGA metrics, Node Detail Modals). Our hardware nodes are built using ESP32 with LSM6DS3 sensors.

| Source | URL | Update Frequency | Format |
|--------|-----|------------------|--------|
| BMKG (Indonesia) | https://data.bmkg.go.id | ~5 minutes | JSON |
| JMA (Japan) | https://www.data.jma.go.jp | ~1 minute | JSON/XML |

---

## BMKG API Integration

### Available Endpoints

```text
# Latest earthquake (updated ~5 minutes)
GET https://data.bmkg.go.id/DataMKG/TEWS/autogempa.json
→ Latest single earthquake event

GET https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.json  
→ 15 latest earthquakes

GET https://data.bmkg.go.id/DataMKG/TEWS/gempadirasakan.json
→ Felt earthquakes (more selective)

# Shakemap (if available)
GET https://data.bmkg.go.id/DataMKG/TEWS/{date}/{eventid}-mmi.png
```

### Response Format `autogempa.json`

```json
{
  "Infogempa": {
    "gempa": {
      "Tanggal": "04 Sep 2026",
      "Jam": "01:23:45 WIB",
      "DateTime": "2026-09-03T18:23:45+00:00",
      "Coordinates": "-6.20,106.82",
      "Lintang": "6.20 LS",
      "Bujur": "106.82 BT",
      "Magnitude": "5.2",
      "Kedalaman": "10 km",
      "Wilayah": "Pusat gempa berada di darat 12 km Barat Daya JAKARTA",
      "Potensi": "Gempa ini dirasakan, tidak berpotensi tsunami",
      "Dirasakan": "III-IV Jakarta, II-III Bogor",
      "Shakemap": "20260903182345.mmi.jpg"
    }
  }
}
```

### Python Client

```python
import httpx
import asyncio
from dataclasses import dataclass
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class EarthquakeEvent:
    source: str
    event_id: str
    datetime_utc: datetime
    magnitude: float
    depth_km: float
    epicenter_lat: float
    epicenter_lon: float
    location_desc: str
    tsunami_potential: bool
    raw: dict

class BMKGClient:
    BASE_URL = "https://data.bmkg.go.id/DataMKG/TEWS"
    POLL_INTERVAL = 30  # seconds
    
    def __init__(self):
        self.last_event_id = None
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def get_latest_event(self) -> EarthquakeEvent | None:
        try:
            resp = await self.client.get(f"{self.BASE_URL}/autogempa.json")
            resp.raise_for_status()
            data = resp.json()
            
            gempa = data["Infogempa"]["gempa"]
            return self._parse_event(gempa)
        except Exception as e:
            logger.error(f"BMKG API error: {e}")
            return None
    
    async def get_recent_events(self, limit=15) -> list[EarthquakeEvent]:
        try:
            resp = await self.client.get(f"{self.BASE_URL}/gempaterkini.json")
            resp.raise_for_status()
            data = resp.json()
            
            events = []
            for gempa in data["Infogempa"]["gempa"][:limit]:
                event = self._parse_event(gempa)
                if event:
                    events.append(event)
            return events
        except Exception as e:
            logger.error(f"BMKG events API error: {e}")
            return []
    
    def _parse_event(self, gempa: dict) -> EarthquakeEvent | None:
        try:
            coords = gempa["Coordinates"].split(",")
            lat, lon = float(coords[0]), float(coords[1])
            
            # Parse datetime (BMKG format varies)
            dt_str = gempa.get("DateTime", "")
            dt = datetime.fromisoformat(dt_str) if dt_str else datetime.utcnow()
            
            return EarthquakeEvent(
                source="bmkg",
                event_id=f"bmkg_{gempa.get('Shakemap', dt.strftime('%Y%m%d%H%M%S'))}",
                datetime_utc=dt,
                magnitude=float(gempa["Magnitude"]),
                depth_km=float(gempa["Kedalaman"].replace(" km", "")),
                epicenter_lat=lat,
                epicenter_lon=lon,
                location_desc=gempa.get("Wilayah", ""),
                tsunami_potential="tsunami" in gempa.get("Potensi", "").lower() 
                                  and "tidak berpotensi" not in gempa.get("Potensi", "").lower(),
                raw=gempa
            )
        except Exception as e:
            logger.error(f"Error parsing BMKG event: {e}")
            return None
    
    async def poll_loop(self, callback):
        """Background polling loop"""
        while True:
            event = await self.get_latest_event()
            if event and event.event_id != self.last_event_id:
                self.last_event_id = event.event_id
                await callback(event)
            await asyncio.sleep(self.POLL_INTERVAL)
```

---

## JMA API Integration

### Endpoints

```text
# JMA Earthquake List (JSON format)
GET https://www.data.jma.go.jp/multi/quake/index.html?lang=en
→ Web page, requires scraping or use an alternative

# JMA official data feed (GeoJSON)
GET https://www.data.jma.go.jp/svd/eqdb/data/shindo-search/js/data/eqlist.js

# JMA EEW RSS Feed
GET https://www.data.jma.go.jp/svd/eqev/data/nteq/top.html

# Alternative: P2P JMA Earthquake API (community)
GET https://api.p2pquake.net/v2/history?codes=551&limit=10
→ JSON format, easy to use, aggregated from JMA
```

### P2P Quake API (Recommended for JMA)

```python
class JMAClient:
    """
    Uses P2P Quake API as a proxy for JMA data.
    This API is free, requires no auth, and provides clean JSON format.
    """
    P2P_URL = "https://api.p2pquake.net/v2/history"
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)

    async def get_recent_events(self, limit=10) -> list[EarthquakeEvent]:
        params = {
            "codes": 551,    # 551 = Earthquake Information
            "limit": limit
        }
        try:
            resp = await self.client.get(self.P2P_URL, params=params)
            data = resp.json()
            
            events = []
            for item in data:
                if item.get("code") == 551:
                    event = self._parse_p2p_event(item)
                    if event:
                        events.append(event)
            return events
        except Exception as e:
            logger.error(f"JMA/P2P API error: {e}")
            return []
    
    def _parse_p2p_event(self, item: dict) -> EarthquakeEvent | None:
        """
        P2P Quake API response format:
        {
          "code": 551,
          "time": "2026/09/04 01:23:45",
          "earthquake": {
            "time": "2026/09/04 01:23:45",
            "hypocenter": {
              "name": "Off the coast of Chiba",
              "latitude": 35.5,
              "longitude": 140.2,
              "depth": 50,
              "magnitude": 4.2
            },
            "maxScale": 20
          }
        }
        """
        try:
            hypo = item["earthquake"]["hypocenter"]
            
            dt_str = item["earthquake"]["time"]
            dt = datetime.strptime(dt_str, "%Y/%m/%d %H:%M:%S")
            
            return EarthquakeEvent(
                source="jma",
                event_id=f"jma_{item.get('id', dt.strftime('%Y%m%d%H%M%S'))}",
                datetime_utc=dt,
                magnitude=hypo.get("magnitude", 0),
                depth_km=hypo.get("depth", 0),
                epicenter_lat=hypo.get("latitude", 0),
                epicenter_lon=hypo.get("longitude", 0),
                location_desc=hypo.get("name", ""),
                tsunami_potential=False,  # Needs checking other fields
                raw=item
            )
        except Exception as e:
            logger.error(f"Error parsing JMA event: {e}")
            return None
```

---

## Geofencing & Event Filtering

To ensure accurate and timely alerts, the Consensus algorithm in Python strictly prevents false positives and groups multiple nodes using Haversine P-Wave velocity limits. The geofence filter classifies relevant events based on distance and magnitude.

```python
from math import radians, cos, sin, asin, sqrt

def haversine(lat1, lon1, lat2, lon2) -> float:
    """Distance in km between two lat/lon points"""
    R = 6371  # Earth radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return 2 * R * asin(sqrt(a))

class GeofenceFilter:
    # Lindu.id system location (center/server)
    HOME_LAT = -6.200
    HOME_LON = 106.816
    
    # Relevance radii
    CRITICAL_RADIUS_KM = 100    # < 100 km: DANGER
    WARNING_RADIUS_KM = 500     # < 500 km: WARNING
    INFO_RADIUS_KM = 2000       # < 2000 km: INFO (Japan, etc.)
    
    def classify_event(self, event: EarthquakeEvent) -> str | None:
        dist = haversine(
            self.HOME_LAT, self.HOME_LON,
            event.epicenter_lat, event.epicenter_lon
        )
        
        if dist > self.INFO_RADIUS_KM:
            return None  # Too far, ignore
        
        # Also check minimum magnitude
        if event.magnitude < 3.0:
            return None  # Too small
        
        if dist <= self.CRITICAL_RADIUS_KM and event.magnitude >= 4.0:
            return "DANGER"
        elif dist <= self.WARNING_RADIUS_KM and event.magnitude >= 5.0:
            return "WARNING"
        elif dist <= self.INFO_RADIUS_KM and event.magnitude >= 6.0:
            return "INFO"
        
        return None
```

---

## USGS Global Feed (Optional — Phase 3)

```text
# USGS Earthquake Hazards Program — GeoJSON Feed
GET https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson
GET https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson
GET https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson

# Update frequency: every 1 minute (all_hour), 5 minutes (daily feeds)
# Free, no auth required
# Format: Standard GeoJSON
```

---

## API Rate Limits & Ethics

| API | Rate Limit | Notes |
|-----|------------|-------|
| BMKG | Not specified, use ≤ 2 req/minute | Government server, do not abuse |
| P2P Quake (JMA) | Not specified, use ≤ 1 req/minute | Community service |
| USGS | Very relaxed, updates every 1-5 minutes | CDN cached |

**Best Practices:**
- Use caching — do not poll more frequently than the update interval.
- Set an informative `User-Agent` header: `LinduID/1.0 (lindu.id; contact@lindu.id)`.
- Handle errors gracefully, avoid excessive retries.
- Store the last event ID for deduplication.
- Ensure all historical and real-time data is efficiently stored in our **PostgreSQL (Dockerized)** database.

---

## ✅ Research Notes (Updated)

### P2P Quake API — WebSocket Real-time (Main Recommendation for JMA)

Based on research, **P2P Quake API WebSocket** is the best choice for JMA data as it supports **real-time push** without polling:

```python
import websockets
import json

class JMAWebSocketClient:
    WS_URL = "wss://api.p2pquake.net/v2/ws"
    
    # Important Event Codes:
    # 551 = Earthquake Information (confirmed, post-event)
    # 552 = Tsunami Forecast
    # 554 = EEW Alert — Forecast (INITIAL, less accurate)
    # 555 = EEW Alert — WARNING (ALREADY CONFIRMED)
    
    async def connect_and_listen(self, callback):
        async with websockets.connect(self.WS_URL) as ws:
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                
                code = data.get("code")
                
                if code == 555:  # EEW Warning — most critical!
                    await callback(self._parse_eew(data))
                elif code == 551:  # Confirmed earthquake info
                    await callback(self._parse_quake(data))
    
    def _parse_eew(self, data: dict) -> EarthquakeEvent:
        # EEW structure differs from post-event quake info
        return EarthquakeEvent(
            source="jma_eew",
            event_id=f"jma_eew_{data.get('id')}",
            datetime_utc=datetime.now(),  # EEW doesn't have a post-event time
            magnitude=data.get("earthquake", {}).get("hypocenter", {}).get("magnitude", 0),
            ...
        )
```

**P2P Quake API Rate Limits (2026):**
- REST History: 60 req/minute
- REST JMA: 10 req/minute  
- WebSocket: **2 concurrent connections per IP**

### BMKG — Important Notes

- **There is no public MQTT/WebSocket stream** from BMKG — only REST polling is available.
- The `autogempa.json` data is **preliminary/automatic** — and may be revised.
- **Recommended: delay 30-60 seconds** before triggering a critical alert from BMKG (wait for confirmation).
- For official real-time BMKG access (InaTEWS), an authorization letter to **inatews@bmkg.go.id** is required.
- **Safe polling interval: every 60-120 seconds** to avoid rate limiting.

### ESP32 MQTT Library — Final Recommendation

Our hardware nodes are built using **ESP32** microcontrollers.

| Priority | Library | Framework | Native TLS | Recommendation |
|----------|---------|-----------|------------|----------------|
| ✅ #1 | **PsychicMqttClient** | Arduino | Yes | Best for Arduino ESP32-S3 |
| ✅ #2 | **MycilaMQTT** | Arduino | Yes | Active alternative with a clean API |
| ✅ #3 | **esp-mqtt** (Espressif) | ESP-IDF | Yes | Best for ESP-IDF, MQTT 5.0 |
| ⚠️ | PubSubClient | Arduino | Via wrapper | Blocking, not ideal for TLS |
| ❌ | AsyncMqttClient | Arduino | No | Legacy, no longer updated |

### LSM6DS3 — Optimal Parameters

Our nodes rely on the **LSM6DS3** sensor for accurate seismic detection.

| Parameter | Value | Notes |
|-----------|-------|-------|
| Accelerometer ODR | **104 Hz** (not 1600 Hz) | 104 Hz is sufficient for seismic data, saves power |
| Full Scale | **±2g or ±4g** | Not ±8g — more sensitive for small earthquakes |
| STA window | **0.5-1 seconds** (52-104 samples) | Seismology standard |
| LTA window | **10-30 seconds** | Rolling average background |
| STA/LTA threshold | **3.0-5.0** | Tune according to environment |
| High-pass filter | **< 0.5 Hz** cutoff | Remove DC offset & drift |
| Band-pass filter | **1-20 Hz** | Relevant seismic frequencies |

> **Correction:** An ODR of 1600 Hz is too high for local seismic events and wastes power. 
> 104 Hz is the practical standard for earthquake detection with MEMS sensors.


---
