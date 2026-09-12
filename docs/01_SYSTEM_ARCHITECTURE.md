
<!-- START OF 01_ARCHITECTURE.md -->
# 🏗️ System Architecture — Lindu.id

## Overall Architecture Diagram

```
╔══════════════════════════════════════════════════════════════════════════╗
║                        LINDU.ID SYSTEM ARCHITECTURE                      ║
╚══════════════════════════════════════════════════════════════════════════╝

  ┌─────────────────────────────────────────────────────────────────────┐
  │                      EDGE LAYER (Sensor Nodes)                       │
  │                                                                       │
  │  ┌─────────────────────┐      ┌─────────────────────┐               │
  │  │   NODE 1 (Location A)│      │   NODE 2 (Location B)│               │
  │  │   ESP32              │      │   ESP32              │               │
  │  │   + LSM6DS3          │      │   + LSM6DS3          │               │
  │  │                      │      │                      │               │
  │  │  • Read accelero     │      │  • Read accelero     │               │
  │  │  • Gravity vector    │      │  • Gravity vector    │               │
  │  │    (pose calculation)│      │    (pose calculation)│               │
  │  │  • Edge pre-filter   │      │  • Edge pre-filter   │               │
  │  │  • Precision time    │      │  • Precision time    │               │
  │  │  • Receive alert     │      │  • Receive alert     │               │
  │  │  • Buzzer + LED      │      │  • Buzzer + LED      │               │
  │  └──────────┬──────────┘      └──────────┬──────────┘               │
  │             │  MQTT TLS (port 8883)       │  MQTT TLS (port 8883)   │
  └─────────────┼───────────────────────────-┼────────────────────────--┘
                │                             │
                ▼                             ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │                      SERVER LAYER (mqtt.lindu.id)                   │
  │                                                                       │
  │  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
  │  │  MQTT Broker    │  │  Consensus App   │  │  Dashboard API   │   │
  │  │  (Mosquitto)    │  │  (Python)        │  │  (Python/Flask)  │   │
  │  │  Port 8883 TLS  │  │                  │  │                  │   │
  │  │  Port 1883 local│  │  • Read metrics  │  │  • REST API      │   │
  │  │                 │  │  • 2-3 Node      │  │  • WebSocket     │   │
  │  │  Topic routing  │◄─►  Consensus     │  │  • Auth JWT      │   │
  │  │                 │  │  • Detect quake  │  │  • Geoshake UI   │   │
  │  │                 │  │  • Scoring       │  │                  │   │
  │  │                 │  │  • Publish alert │  │                  │   │
  │  └─────────────────┘  └──────────────────┘  └──────────────────┘   │
  │                                │                                      │
  │  ┌─────────────────┐          │  ┌──────────────────┐               │
  │  │  Database       │◄─────────┘  │  API Integrator  │               │
  │  │  (PostgreSQL)   │             │                  │               │
  │  │                 │             │  • BMKG polling  │               │
  │  │  • Dockerized   │             │  • JMA polling   │               │
  │  │  • Raw metrics  │             │  • EEW validator │               │
  │  │  • Events       │             │                  │               │
  │  │  • Alerts log   │             └──────────────────┘               │
  │  └─────────────────┘                                                 │
  └──────────────────────────────────────────┬──────────────────────────┘
                                             │
                          MQTT TLS (port 8883)│
                                             ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │                    ACTUATOR LAYER (ESP32 Actuator)                   │
  │                                                                       │
  │  ┌─────────────────────────────────────────────────────────────┐    │
  │  │              ESP32 ACTUATOR NODE (Location C/Home)           │    │
  │  │                                                              │    │
  │  │   [Servo Motor]  [Solenoid Door]  [Buzzer]  [LED Strobe]   │    │
  │  │   Close Valve    Open Door        Audio Alarm Visual Alarm │    │
  │  │      Gas         Emergency                                   │    │
  │  └─────────────────────────────────────────────────────────────┘    │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │                     EXTERNAL DATA SOURCES                            │
  │                                                                       │
  │   ┌────────────────┐              ┌────────────────┐                 │
  │   │  BMKG Indonesia│              │   JMA Japan    │                 │
  │   │  data.bmkg.go.id│             │  data.jma.go.jp│                 │
  │   │                │              │                │                 │
  │   │  • EEW         │              │  • EEW Mj      │                 │
  │   │  • Magnitude   │              │  • Magnitude   │                 │
  │   │  • Epicenter   │              │  • Epicenter   │                 │
  │   │  • Tsunami     │              │  • Tsunami     │                 │
  │   └────────────────┘              └────────────────┘                 │
  └─────────────────────────────────────────────────────────────────────┘
```

---

## Layer Breakdown

### 1. Edge Layer — Sensor Nodes

| Component | Specification |
|-----------|---------------|
| MCU | ESP32 (16MB Flash) |
| Sensor | LSM6DS3 (Accelerometer 3-axis via I2C) |
| Capabilities | Calculates gravity vector/pose for flat or wall mounting |
| OS / Kernel | FreeRTOS (Dual-Core Asymmetric Processing) |
| Connection | Wi-Fi → MQTT TLS 1.2 (Port 8883) to server |
| Fallback | Wi-Fi Mesh P2P between nodes (if internet fails) |
| Maintenance | OTA Update with A/B Rollback (Partition `app0` & `app1` @ 6MB) |
| Power | Mains + UPS/Battery (≥4 hours) + Hardware WDT |

**Sensor Node Functions:**
- **Core 1 (Sensor):** Accelerometer sampling at 100Hz ODR with Exponential Moving Average (EMA) mathematical filter. Strictly detects vibration threshold (P-Wave).
- **Core 0 (Network):** Receives Events from Core 1 via FreeRTOS Queue. Handles MQTTS encryption and NTP synchronization.
- **Edge Computing (Decentralization):** Independently computes the Haversine formula to decide if the epicenter is within its hazard radius, preventing the server from having to loop through calculations.

### 2. Server Layer — mqtt.lindu.id

#### Application 1: MQTT Broker (Mosquitto)
- Port **8883** — MQTT over TLS (external, ESP32 nodes)
- Port **1883** — MQTT without TLS (internal localhost)
- Authentication: client certificate + username/password
- Bridge to internal services

#### Application 2: Consensus Engine (Python)
- Subscribes to sensor topics from all nodes
- Runs spatial consensus algorithm (see `06_CONSENSUS_ALGORITHM.md`)
- Calculates magnitude and epicenter estimation
- Cross-validates with BMKG/JMA data
- Publishes alert commands to actuator and sensor nodes

#### Application 3: Dashboard API + Web (lindu.id)
- Backend: Python (Flask for REST API, Paho-MQTT)
- Real-time updates via WebSocket
- Web frontend: React Dashboard featuring a "Geoshake-style" UI. Includes Animated epicenters, PGA-based color-coded nodes, Helicorder 24h mockup, RMS & PGA metrics, and Node Detail Modals.

#### Application 4: External API Integrator
- BMKG polling every 30 seconds
- JMA polling every 60 seconds
- EEW validator: validates local detection with government data

### 3. Actuator Layer — ESP32 Actuator

| Component | Specification |
|-----------|---------------|
| MCU | ESP32 (standard/WROOM) |
| Connection | Wi-Fi → MQTT TLS to server |
| Actuator 1 | Servo Motor → Closes Gas Valve |
| Actuator 2 | Solenoid Door Lock → Opens Emergency Door |
| Actuator 3 | Active Buzzer → Audio Alarm |
| Actuator 4 | LED Strobe → Visual Alarm |
| Power | Mains + UPS (≥4 hours) |

---

## Data Communication Flow

### Normal Flow (Local Detection)

```
Node 1 detects vibration
    → publishes metrics to mqtt.lindu.id/sensor/node1/metrics
Node 2 detects vibration  
    → publishes metrics to mqtt.lindu.id/sensor/node2/metrics

Consensus Engine receives both
    → runs spatial consensus algorithm
    → if earthquake is confirmed:
        → publishes to lindu/alert/earthquake
        → Actuator subscribes → executes mitigation
        → Node 1,2 subscribes → sound alarm
        → Dashboard receives via WebSocket
```

### External Validation Flow

```
API Integrator polls BMKG/JMA
    → if EEW is issued by BMKG/JMA
    → publishes to lindu/alert/external
    → Consensus Engine validates + correlates
    → Triggers alert if relevant to location
```

### Fallback Mode (Disaster Scenario: Internet & Router Failure)

**DANGER:** When a major earthquake begins, power poles often fall and cut off electricity to your home's Wi-Fi Router, causing the Nodes to lose Server (Cloud) access.
**FAIL-SAFE SOLUTION:** **ESP-NOW (Offline Mesh)** network.

```text
Node 1 (Living Room) ← ESP-NOW Radio (2.4GHz) → Node 2 (Bedroom)
    → If Node 1 detects shaking, but detects Wi-Fi is disconnected.
    → Node 1 instantly transmits local ESP-NOW radio waves (no Router needed).
    → Node 2 receives the ESP-NOW signal within milliseconds.
    → All sirens in the house sound simultaneously to save residents, without the need for internet!
```

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| ESP32 Firmware | Arduino framework (C++), libraries: PubSubClient, ArduinoMqttClient, LSM6DS3 |
| MQTT Broker | Eclipse Mosquitto 2.x |
| Consensus App | Python 3.11+ (paho-mqtt, numpy, scipy) |
| Database | PostgreSQL (Dockerized) |
| Dashboard Backend | Python (Flask for REST API, Paho-MQTT) |
| Dashboard Frontend | React ("Geoshake-style" UI, Chart.js, Leaflet.js) |
| Reverse Proxy | Nginx |
| TLS Certificates | Let's Encrypt (Certbot) |
| Deployment | Docker Compose |
| CI/CD | GitHub Actions |

---

## Network & Security Architecture

```
Internet
    │
    ▼
[Nginx Reverse Proxy]
    │
    ├── :443  → lindu.id (React Dashboard)
    ├── :8883 → mqtt.lindu.id (MQTT TLS)
    └── :8080 → api.lindu.id (Flask REST API)

Internal (Docker network):
    ├── mosquitto:1883 (internal broker)
    ├── consensus-app:8000
    ├── dashboard-api:8080
    └── postgresdb:5432
```

See [`08_SECURITY.md`](./08_SECURITY.md) for security details.


---

<!-- START OF 02_FEATURES.md -->
# ✨ Feature List — Lindu.id

## Status Legend
- 🔴 **P0** — Core / Must Have (MVP)
- 🟡 **P1** — Important (Phase 2)
- 🟢 **P2** — Nice to Have (Phase 3)

---

## 1. Sensor Node Features (ESP32)

| ID | Feature | Priority | Description |
|----|---------|----------|-------------|
| SN-01 | Read LSM6DS3 accelerometer data (X,Y,Z) | 🔴 P0 | 1600 Hz ODR |
| SN-02 | Read LSM6DS3 gyroscope data | 🔴 P0 | Validates non-seismic vibrations |
| SN-03 | Local vibration threshold detection | 🔴 P0 | < 100ms response time |
| SN-04 | Calculate gravity vector/pose | 🔴 P0 | Supports flat/wall mounting configurations |
| SN-05 | Wi-Fi connection + auto reconnect | 🔴 P0 | WPA2/WPA3 |
| SN-06 | Publish metrics to server via MQTT | 🔴 P0 | QoS 1, TLS |
| SN-07 | Subscribe to server alerts via MQTT | 🔴 P0 | QoS 2 for critical alerts |
| SN-08 | NTP time sync (precision timestamp) | 🔴 P0 | Syncs every hour |
| SN-09 | Local alarm: LED + Buzzer upon alert | 🔴 P0 | Visual + audio warning |
| SN-10 | Edge seismic pre-filtering (lightweight FFT) | 🟡 P1 | Reduces false positives |
| SN-11 | Wi-Fi Mesh fallback (ESP-NOW) | 🟡 P1 | Triggers if internet connection fails |
| SN-12 | OLED display for status & alerts | 🟡 P1 | Local information without dashboard |
| SN-13 | OTA firmware update via MQTT | 🟡 P1 | Updates without physical access |
| SN-14 | Deep sleep mode (power saving) | 🟢 P2 | If powered by battery |
| SN-15 | Lightweight Edge AI (TFLite Micro) | 🟢 P2 | On-device classification |
| SN-16 | Local SD Card logging | 🟢 P2 | Backup if connection is lost |

---

## 2. Actuator Node Features (ESP32)

| ID | Feature | Priority | Description |
|----|---------|----------|-------------|
| AC-01 | Wi-Fi connection + MQTT TLS to server | 🔴 P0 | Subscribes to alert topic |
| AC-02 | Open Solenoid Door Lock (emergency door) | 🔴 P0 | Failsafe: opens upon power loss |
| AC-03 | Close Gas Valve via Servo Motor | 🔴 P0 | Response < 2 seconds |
| AC-04 | Activate Buzzer alarm | 🔴 P0 | Audio warning |
| AC-05 | Activate LED Strobe | 🔴 P0 | Visual warning |
| AC-06 | Status reporting to server | 🟡 P1 | Execution confirmation |
| AC-07 | Manual override button | 🟡 P1 | Manually resets the actuator |
| AC-08 | Auto reset timer post-earthquake | 🟡 P1 | Closes door again after N minutes |
| AC-09 | OTA firmware update | 🟡 P1 | Remote updates |
| AC-10 | Sensor feedback (limit switch, etc.) | 🟢 P2 | Confirms actuator position |

---

## 3. Server — Consensus Engine

| ID | Feature | Priority | Description |
|----|---------|----------|-------------|
| CE-01 | Receive metrics from all nodes via MQTT | 🔴 P0 | Real-time ingestion |
| CE-02 | Time-window buffer (5 seconds) for correlation | 🔴 P0 | Synchronizes multi-node data |
| CE-03 | Consensus: nodes must agree | 🔴 P0 | Voting threshold ≥ 2/2 nodes |
| CE-04 | Calculate PGA (Peak Ground Acceleration) amplitude | 🔴 P0 | Estimates strength |
| CE-05 | Estimate magnitude from PGA | 🟡 P1 | Empirical seismology formula |
| CE-06 | Estimate epicenter (Δt triangulation) | 🟡 P1 | Requires ≥ 3 nodes for accuracy |
| CE-07 | Validate with BMKG API | 🟡 P1 | Reduces false positives |
| CE-08 | Validate with JMA API | 🟡 P1 | Cross-reference |
| CE-09 | Publish alert to actuator & sensor nodes | 🔴 P0 | MQTT QoS 2, retained |
| CE-10 | Scoring system (confidence level) | 🟡 P1 | 0-100% confidence score |
| CE-11 | Save events to database (PostgreSQL) | 🔴 P0 | Persistent logging |
| CE-12 | Anti-spam / alert cooldown | 🔴 P0 | Prevents alert flooding |
| CE-13 | Detect offline nodes | 🟡 P1 | Health monitoring |
| CE-14 | Real-time notifications to Dashboard | 🔴 P0 | WebSocket push |
| CE-15 | Frequency analysis (server-side FFT) | 🟡 P1 | Distinguishes P-wave vs S-wave |
| CE-16 | Machine Learning model (seismic classifier) | 🟢 P2 | Scikit-learn / TensorFlow |

---

## 4. Server — External API Integration

| ID | Feature | Priority | Description |
|----|---------|----------|-------------|
| EX-01 | Poll BMKG EEW endpoint | 🔴 P0 | Every 30 seconds |
| EX-02 | Poll JMA EEW endpoint | 🟡 P1 | Every 60 seconds |
| EX-03 | Parse & normalize BMKG data | 🔴 P0 | Standardizes format |
| EX-04 | Parse & normalize JMA data | 🟡 P1 | Standardizes format |
| EX-05 | Geofencing: filter events based on radius | 🟡 P1 | Only location-relevant events |
| EX-06 | Publish EEW to internal system | 🔴 P0 | Triggers alerts from external APIs |
| EX-07 | USGS Global earthquake feed | 🟢 P2 | Additional feed |
| EX-08 | Save external data to DB | 🟡 P1 | Historical reference |

---

## 5. Dashboard lindu.id

| ID | Feature | Priority | Description |
|----|---------|----------|-------------|
| DB-01 | Main page: "Geoshake-style" UI | 🔴 P0 | React frontend with Python/Flask backend |
| DB-02 | Map: Animated epicenters | 🔴 P0 | Leaflet.js / Mapbox integration |
| DB-03 | Nodes: PGA-based color-coded nodes | 🔴 P0 | Real-time visual status indication |
| DB-04 | Charts: Helicorder 24h mockup | 🔴 P0 | Continuous seismic recording visualization |
| DB-05 | Metrics: RMS & PGA metrics | 🔴 P0 | Live data streaming via WebSocket |
| DB-06 | Detail: Node Detail Modals | 🔴 P0 | Comprehensive per-node statistics |
| DB-07 | Alert log: warning history | 🔴 P0 | Table + filters |
| DB-08 | User authentication (login/logout) | 🟡 P1 | JWT auth |
| DB-09 | Push notification (browser/mobile) | 🟡 P1 | PWA notification |
| DB-10 | Export data CSV/PDF | 🟡 P1 | For academic reporting |
| DB-11 | Historical charts per node | 🟡 P1 | Zoom, pan, range |
| DB-12 | Configure thresholds via dashboard | 🟡 P1 | No need to reflash firmware |
| DB-13 | Multi-user / role management | 🟢 P2 | Admin, viewer |
| DB-14 | Mobile app (React Native / PWA) | 🟢 P2 | Smartphone application |
| DB-15 | Telegram/WhatsApp notification integration | 🟢 P2 | Send alerts to chat |

---

## 6. DevOps & Infrastructure

| ID | Feature | Priority | Description |
|----|---------|----------|-------------|
| DV-01 | Docker Compose for all services | 🔴 P0 | Easy deployment (PostgreSQL, APIs) |
| DV-02 | SSL/TLS certificate (Let's Encrypt) | 🔴 P0 | HTTPS + MQTTS |
| DV-03 | Nginx reverse proxy | 🔴 P0 | Load balancing |
| DV-04 | Automated database backup | 🟡 P1 | Daily cron job |
| DV-05 | Server monitoring (Grafana/Prometheus) | 🟡 P1 | Server health |
| DV-06 | GitHub Actions CI/CD | 🟡 P1 | Auto deploy on push |
| DV-07 | Environment variables management | 🔴 P0 | .env, secrets |
| DV-08 | Log aggregation (ELK / Loki) | 🟢 P2 | Centralized logging |

---

## MVP Scope (Phase 1)

Features with 🔴 P0 priority that must be completed for demo:

1. **SN**: Node sends accelerometer data (gravity vector) + receives alerts
2. **AC**: Actuator opens door + closes valve upon alert
3. **CE**: Server receives data from 2 nodes + performs basic consensus + publishes alert
4. **EX**: Polls BMKG + forwards to system
5. **DB**: Geoshake-style React dashboard + animated epicenters + helicorder + alert log


---

<!-- START OF 06_CONSENSUS_ALGORITHM.md -->
# 🧮 Consensus Algorithm — Lindu.id

## Basic Concept

The system uses **Spatial Seismic Consensus** to distinguish real earthquakes from local vibrations (vehicles, machinery, footsteps). The principle:

> **Real earthquake** = seismic waves detected by **MULTIPLE nodes** within a specific time frame with consistent frequency characteristics.

---

## Hardware & Infrastructure Stack

- **Hardware**: ESP32 microcontroller with LSM6DS3 accelerometer sensor.
- **Database**: PostgreSQL (Dockerized) for reliable, structured time-series and event data storage.
- **Frontend**: React Dashboard featuring a "Geoshake-style" UI (Animated epicenters, PGA-based color-coded nodes, Helicorder 24h mockup, RMS & PGA metrics, Node Detail Modals).

---

## Consensus Pipeline

```
Input: Streaming ESP32 + LSM6DS3 sensor data from Node 1 & Node 2
         │
         ▼
┌─────────────────────────────┐
│  1. TIME SYNCHRONIZATION    │
│     NTP-synced timestamps   │
│     Buffer: time_window=5s  │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  2. SIGNAL PROCESSING       │
│     STA/LTA per node        │
│     FFT frequency analysis  │
│     PGA calculation         │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  3. LOCAL DETECTION         │
│     Threshold crossing?     │
│     Node votes: YES/NO      │
└──────────────┬──────────────┘
               │
         ┌─────┴─────┐
         │           │
    ≥2/2 nodes  <2/2 nodes
    agree         agree
         │           │
         ▼           ▼
┌──────────────┐  ┌──────────┐
│ 4. CONSENSUS │  │  FALSE   │
│   REACHED    │  │ POSITIVE │
└──────┬───────┘  └──────────┘
       │
       ▼
┌─────────────────────────────┐
│  5. PARAMETER ESTIMATION    │
│     - Magnitude (PGA→Mw)   │
│     - Epicenter (Δt method) │
│     - Depth (if possible)   │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  6. EXTERNAL VALIDATION     │
│     - Check BMKG            │
│     - Check JMA             │
│     - Confidence boost      │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  7. SCORING & DECISION      │
│     Confidence Score 0-100% │
│     if score > threshold    │
│     → PUBLISH ALERT         │
│     → SAVE TO POSTGRESQL    │
└─────────────────────────────┘
```

---

## Step 1: Time Synchronization

All ESP32 nodes perform **NTP sync** every hour to the `pool.ntp.org` pool. Timestamp error tolerance between nodes: ≤ 50ms.

```python
# Time window for correlation
TIME_WINDOW = 5.0       # seconds — buffering readings from all nodes
NTP_TOLERANCE_MS = 50   # ms — clock drift tolerance
```

---

## Step 2: Signal Processing

### STA/LTA (Short-Term Average / Long-Term Average)

Standard seismology onset detection algorithm:

```python
def sta_lta(signal, sr=100, sta_len=1.0, lta_len=30.0):
    """
    signal : acceleration array (detrended)
    sr     : sample rate (Hz)
    sta_len: STA window (seconds)
    lta_len: LTA window (seconds)
    return : STA/LTA ratio array
    """
    sta_samples = int(sta_len * sr)
    lta_samples = int(lta_len * sr)
    
    sta = pd.Series(np.abs(signal)).rolling(sta_samples).mean()
    lta = pd.Series(np.abs(signal)).rolling(lta_samples).mean()
    
    ratio = sta / (lta + 1e-10)  # avoid division by zero
    return ratio
```

### PGA (Peak Ground Acceleration)

```python
def calculate_pga(accel_x, accel_y, accel_z):
    """
    Calculate PGA from 3-axis acceleration
    Return: PGA in g (gravity)
    """
    # Resultant horizontal acceleration
    horizontal = np.sqrt(accel_x**2 + accel_y**2)
    
    # Remove gravity from Z axis (detrend)
    accel_z_detrended = accel_z - 9.81
    
    # PGA = max resultant
    resultant = np.sqrt(accel_x**2 + accel_y**2 + accel_z_detrended**2)
    pga = np.max(np.abs(resultant))
    
    return pga / 9.81  # convert to g
```

### FFT Frequency Analysis

Distinguishing earthquakes (1-10 Hz) from non-seismic vibrations (machinery: 50Hz+, footsteps: 1-3Hz variable):

```python
def analyze_frequency(signal, sr=1600):
    """
    Dominant frequency analysis for vibration source classification
    Earthquake: dominant energy in 1-10 Hz
    Machinery/industry: 50Hz, 100Hz (harmonics)
    Vehicles: 10-30 Hz
    """
    freqs = np.fft.rfftfreq(len(signal), d=1/sr)
    fft_mag = np.abs(np.fft.rfft(signal))
    
    # Energy in the seismic band (1-10 Hz)
    seismic_mask = (freqs >= 1.0) & (freqs <= 10.0)
    total_energy = np.sum(fft_mag**2)
    seismic_energy = np.sum(fft_mag[seismic_mask]**2)
    
    seismic_ratio = seismic_energy / (total_energy + 1e-10)
    
    return {
        'dominant_freq': freqs[np.argmax(fft_mag)],
        'seismic_energy_ratio': seismic_ratio,
        'is_seismic_candidate': seismic_ratio > 0.3  # 30% energy in seismic band
    }
```

---

## Step 3: Local Detection (Per Node Vote)

```python
class NodeVote:
    STA_LTA_THRESHOLD = 3.5    # Ratio threshold for onset detection
    PGA_THRESHOLD_G = 0.01     # 0.01g ≈ MMI II (very weak)
    SEISMIC_ENERGY_THRESHOLD = 0.3  # 30% energy in seismic band
    
    def vote(self, readings: list[SensorReading]) -> bool:
        """
        Return True if this node detects a possible earthquake
        """
        # Condition 1: STA/LTA crosses the threshold
        sta_lta_ratio = max(self.sta_lta_values)
        cond1 = sta_lta_ratio > self.STA_LTA_THRESHOLD
        
        # Condition 2: PGA crosses the threshold
        pga = calculate_pga(readings)
        cond2 = pga > self.PGA_THRESHOLD_G
        
        # Condition 3: Dominant frequency is in the seismic range
        freq_analysis = analyze_frequency(readings)
        cond3 = freq_analysis['is_seismic_candidate']
        
        # Node votes YES only if at least 2 out of 3 conditions are met
        conditions_met = sum([cond1, cond2, cond3])
        return conditions_met >= 2
```

---

## Step 4 & 5: Node Grouping & Parameter Estimation

To strictly prevent false positives, the consensus algorithm groups multiple nodes using Haversine P-Wave velocity limits. Nodes that trigger outside the physical limits of seismic wave propagation (e.g., P-wave ~6 km/s) are rejected as anomalies.

### Magnitude from PGA (Atkinson & Boore, 2003)

```python
def estimate_magnitude(pga_g, distance_km=None):
    """
    Estimate magnitude from PGA using Ground Motion Prediction Equation (GMPE)
    
    Simplified formula (for quick estimation):
    log(PGA) = a + b*M - c*log(R) - d*R
    
    Inverse: M = (log(PGA) - a + c*log(R) + d*R) / b
    
    Coefficients from Boore & Atkinson 2008 (for Indonesia region):
    a = -2.991, b = 1.414, c = -1.475, d = -0.003
    """
    if distance_km is None:
        distance_km = 10.0  # Assumption if unknown
    
    # PGA in cm/s² (gal)
    pga_gal = pga_g * 980.665
    
    # Simple estimate using Wald et al. (1999)
    # log10(PGA) = 1.456 + 0.9515*M - 1.3228*log10(R) - 0.00369*R
    # PGA in cm/s²
    log_pga = np.log10(pga_gal)
    R = distance_km
    
    # Inverse to find M
    M = (log_pga - 1.456 + 1.3228 * np.log10(R) + 0.00369 * R) / 0.9515
    
    return round(M, 1)
```

### Epicenter Estimation (Δt Triangulation — 2 Nodes)

With 2 nodes, we can estimate a **hyperbola** of possible epicenter locations. The algorithm utilizes Haversine distances to validate wave velocities.

```python
def estimate_hypocenter_2node(
    node1_pos, node2_pos,   # (lat, lon)
    t1, t2,                 # arrival time (Unix timestamp)
    vp=6.0                  # P-wave velocity (km/s), typical for earth's crust
):
    """
    With 2 sensors, we can only obtain a HYPERBOLA of possible locations.
    3+ sensors are needed to get a single point (trilateration).
    
    Δt = t2 - t1 (arrival time difference)
    ΔR = Δt × Vp  (difference in distance from epicenter to node1 vs node2)
    
    |R1 - R2| = ΔR  → Hyperbola equation
    """
    dt = t2 - t1  # seconds
    delta_r_km = abs(dt) * vp  # km
    
    # Distance between nodes using Haversine
    d_km = haversine(node1_pos, node2_pos)
    
    # Parameter for the hyperbola
    a = delta_r_km / 2  # semi-major axis
    c = d_km / 2        # focal distance
    b = np.sqrt(c**2 - a**2) if c > a else 0
    
    # The node that receives it first is closer to the epicenter
    closer_node = node1_pos if t1 < t2 else node2_pos
    
    return {
        'method': 'hyperbola_2node',
        'delta_r_km': delta_r_km,
        'closer_node': closer_node,
        'hyperbola_a': a,
        'hyperbola_b': b,
        'note': 'Need 3rd node for point estimation'
    }
```

> **Note**: With only 2 nodes, the epicenter cannot be determined as a single point. Solutions:
> 1. Use BMKG/JMA data as a reference epicenter point.
> 2. Add a 3rd node in the future.
> 3. Use estimates based on relative amplitudes between nodes.

---

## Step 6: External Validation

```python
async def validate_with_external(event_candidate, tolerance_minutes=5):
    """
    Check if there are events from BMKG/JMA matching the local detection
    Match criteria: time ±5 minutes, magnitude ±1.5, location within 200km radius
    """
    bmkg_events = await bmkg_client.get_recent_events()
    jma_events = await jma_client.get_recent_events()
    
    external_match = None
    
    for event in bmkg_events + jma_events:
        time_diff = abs(event.time - event_candidate.time).seconds / 60
        mag_diff = abs(event.magnitude - event_candidate.magnitude)
        dist_km = haversine(event.epicenter, event_candidate.epicenter_est)
        
        if time_diff <= 5 and mag_diff <= 1.5 and dist_km <= 200:
            external_match = event
            break
    
    return external_match
```

---

## Step 7: Confidence Scoring

```python
def calculate_confidence(
    nodes_agreed: int,
    total_nodes: int,
    pga_values: list,
    freq_analysis: dict,
    external_match: bool,
    sta_lta_peak: float
) -> int:
    """
    Return: confidence score 0-100
    """
    score = 0
    
    # Node agreement (max 35 points)
    score += (nodes_agreed / total_nodes) * 35
    
    # PGA strength (max 20 points)
    avg_pga = np.mean(pga_values)
    if avg_pga > 0.05:   score += 20   # > 0.05g (MMI IV)
    elif avg_pga > 0.02: score += 12
    elif avg_pga > 0.01: score += 6
    
    # Seismic frequency signature (max 20 points)
    if freq_analysis['seismic_energy_ratio'] > 0.5: score += 20
    elif freq_analysis['seismic_energy_ratio'] > 0.3: score += 12
    
    # STA/LTA peak (max 10 points)
    if sta_lta_peak > 8.0: score += 10
    elif sta_lta_peak > 5.0: score += 7
    elif sta_lta_peak > 3.5: score += 4
    
    # External validation (max 15 points)
    if external_match: score += 15
    
    return min(int(score), 100)

# Alert thresholds
ALERT_THRESHOLD = {
    'WARNING': 40,    # Warning → information only
    'DANGER':  70,    # Danger → trigger actuators
}
```

---

## Alert Levels

| Level | Confidence | Magnitude Est. | Action |
|-------|-----------|----------------|------|
| SAFE | < 40% | - | None |
| WARNING | 40-70% | < 3.0 | Alert info to React Dashboard |
| DANGER | > 70% | ≥ 3.0 | Full alert + actuators |
| CRITICAL | > 85% or external confirm | ≥ 5.0 | Immediate mitigation |

---

## Step 8: Continuous Refinement & Feedback Loop

The Lindu.id system does not just make one-off decisions, but iteratively adjusts its calculations as new data arrives to improve accuracy:

### 1. Internal TDOA Correction (Real-Time Node Spreading)
When a local earthquake occurs, waves propagate gradually across sensors:
- **T+0 seconds:** First 3 nodes detect vibration. Server calculates initial epicenter via TDOA (~60% accuracy).
- **T+2 seconds:** 5 additional nodes shake. The server automatically **recalculates TDOA/Geiger** with the new timestamp data, factoring in Haversine P-Wave velocity limits.
- **Adjustment:** Epicenter and Magnitude are revised (Accuracy increases to ~95%), then the server broadcasts the corrected data to nodes that haven't shaken yet to update their *ETA Countdown*. The React Dashboard UI instantly updates the Geoshake-style animated epicenters and node colors.

### 2. External Validation (EEW vs Field Reality)
The system compares theoretical predictions from external APIs with physical arrival times in the field:
- EEW (JMA/BMKG) broadcasts: *"Earthquake at coordinate X, ETA to Jakarta is 30 seconds!"*
- The Jakarta node counts down. If the node physically shakes at **second 34**, the server records an **Error Margin = +4 seconds**.
- **Geological Research Value:** This delay becomes golden geological data indicating that the soil density profile (*Shear-wave velocity*) in the area is slower than standard (e.g., due to peat/soft soil). The system transforms from a mere alarm into an **Automatic Soil Mapping Tool**. Data is logged directly into PostgreSQL.

---

## Anti-False-Positive Measures

1. **Minimum 2/2 nodes must agree** (voting).
2. **Strict Node Grouping** — Uses Haversine P-Wave velocity limits in Python to group valid node triggers and discard impossible wave propagation times (false positives).
3. **Frequency signature check** — Energy in the 1-10 Hz band.
4. **Duration filter** — Minimum 2 seconds, maximum 120 seconds.
5. **Cooldown period** — 60 seconds minimum between alerts.
6. **External validation** — Correlation with BMKG/JMA.
7. **Temporal consistency** — Onset time must be reasonable with the physical distance between ESP32 nodes.

---

## React Dashboard UI & Monitoring

The system features a rich frontend for real-time monitoring:
- **Geoshake-Style UI**: Modern, interactive visual map.
- **Animated Epicenters**: Visual pulses representing estimated and confirmed earthquake epicenters.
- **Color-Coded Nodes**: ESP32 nodes change color dynamically based on real-time PGA levels.
- **Helicorder 24h Mockup**: A 24-hour visual drum recorder view of seismic activity.
- **Metrics Display**: Real-time RMS (Root Mean Square) and PGA metrics.
- **Node Detail Modals**: Clickable nodes revealing detailed time-series graphs and historical PostgreSQL data.


---

<!-- START OF 14_SYSTEM_EDGE_CASES.md -->
# 🏗️ Lindu.id — Comprehensive System Design Schema v2

> This document covers all design decisions that need to be confirmed before implementation begins.
> Changes after coding starts will be expensive — this review is critical.

---

## Open Questions (Needs Decision)

> [!IMPORTANT]
> **Q1 — Power:** USB-C without battery = no UPS. If an earthquake cuts power, all sensors die exactly when needed. Are we willing to add a super-capacitor or a small power bank as a 30-60 second buffer?
>
> **Q2 — Audio Speaker:** Should audio be offline-capable (stored in flash)? Or stream from the server? This determines the flash partitioning.
>
> **Q3 — Provisioning:** Do users have a smartphone during setup? This determines whether we use a BLE app, a WiFi captive portal, or both.
>
> **Q4 — Location Input:** Are GPS coordinates inputted manually by the user, or do we need a GPS chip in the device?
>
> **Q5 — "Anonymous" Deco:** Will all nodes be on the same network (one building, one Deco), or spread across different buildings with different networks?

---

## 1. Hardware Schema v2

### 1.1 ESP32 — Final Specifications

```
┌─────────────────────────────────────────────────────────────┐
│               ESP32-S3 (Recommended) or ESP32                │
│                                                              │
│  Flash     : 16 MB (QSPI)                                   │
│  PSRAM     : 8 MB OCTAL (ESP32-S3 N16R8 variant)           │
│  RAM SRAM  : 512 KB internal                                 │
│  WiFi      : 2.4 GHz 802.11 b/g/n                          │
│  BLE       : BLE 5.0 (for provisioning)                     │
│  USB       : Native USB-C (ESP32-S3) — Serial + JTAG        │
└─────────────────────────────────────────────────────────────┘
```

> [!TIP]
> **Select ESP32-S3-N16R8** (16MB Flash + 8MB PSRAM):
> - 16MB Flash is sufficient for firmware + audio files (WAV/MP3)
> - 8MB PSRAM for FFT buffers and audio decoding in RAM
> - Native USB-C (no separate CH340/CP2102 chip needed)
> - More powerful for TFLite Micro (future AI upgrade)

### 1.2 Flash Partition Layout (16MB)

```
Flash 16MB Layout:
┌──────────────────────────────────────┐
│  0x000000  Bootloader          32 KB │
│  0x008000  Partition Table      4 KB │
│  0x009000  NVS (WiFi,config)  512 KB │  ← SSID, password, location, keys, pose
│  0x089000  OTA_0 (firmware)  1984 KB │  ← Active firmware slot
│  0x269000  OTA_1 (firmware)  1984 KB │  ← OTA update slot
│  0x449000  SPIFFS/LittleFS   11.7 MB │  ← Audio files + data logs
│                               ~50 audio files @ 200KB each = ~10MB
└──────────────────────────────────────┘
```

### 1.3 Circuit Block Diagram

```
                    ┌──────────────────────────────────────────┐
                    │           ESP32-S3 N16R8                  │
                    │                                           │
USB-C 5V ──────────►│ 5V IN                                    │
(Power Adapter)     │    │                                      │
                    │  [AMS1117 3.3V LDO]                      │
                    │    │                                      │
LSM6DS3 ───I2C──►  │ GPIO 8/9 (SDA/SCL)    GPIO 12 ──► BUZZER │
                    │                       GPIO 13 ──► LED RED │
MAX98357A ──I2S──►  │ GPIO 4/5/6 (I2S)      GPIO 14 ──► LED GRN │
SPEAKER              │                       GPIO 15 ──► LED BLU │
                    │ GPIO 0 ──────────────────────► BOOT BTN  │
                    │ GPIO 1 ──────────────────────► SETUP BTN │
                    │                       GPIO 16 ──► OLED SDA│
                    │                       GPIO 17 ──► OLED SCL│
                    │                                           │
                    │ USB D+/D- ────────────────────► USB-C Port│
                    └──────────────────────────────────────────┘
```

### 1.4 Speaker & Audio System

```
ESP32-S3  ──I2S──►  MAX98357A (I2S Amplifier)  ──►  Speaker 4Ω 3W
          (GPIO 4=BCLK, GPIO 5=WCLK, GPIO 6=DATA)

Audio Files in SPIFFS (LittleFS):
/audio/
├── boot_ok.wav          (2s) "Lindu ready"
├── wifi_connected.wav   (2s) "WiFi connected"
├── wifi_failed.wav      (3s) "WiFi failed, entering setup mode"
├── p_wave_detected.wav  (3s) "Early warning, possible earthquake"
├── s_wave_warning.wav   (5s) "DANGER! Earthquake detected! ..."
├── danger_full.wav      (8s) Full alarm + evacuation instructions
├── all_clear.wav        (3s) "Safe, earthquake has passed"
├── node_offline.wav     (3s) "Attention: sensor disconnected"
└── self_test.wav        (2s) "System test successful"
```

> [!NOTE]
> **Audio Format:** WAV 16-bit 22050Hz Mono → ~44KB/second
> Total ~50s audio content ≈ **2.2MB** — extremely safe within 11.7MB SPIFFS

### 1.5 Power Design — USB-C without Battery

```
USB-C 5V/2A ──► [Fuse 2A] ──► [TVS Diode] ──► [AMS1117-3.3] ──► ESP32
                                          └───► 12V Boost?       └──► Sensor
                                                (if relay needed)    └──► Speaker Amp

⚠ CRITICAL WEAKNESS: Power outage = system dies exactly when an earthquake occurs!

MINIMUM RECOMMENDATION (without a full battery):
USB-C 5V ──► [Super-capacitor 10F/5.5V] ──► [Buck-Boost 3.3V] ──► ESP32
             Cost: ~$1.50
             Buffer time: ~30-45 seconds @ 150mA
             Sufficient for: sending last alert + graceful shutdown
```

| Power Option | Cost | Buffer | Pros | Cons |
|-----------|-------|--------|-----------|------------|
| USB-C only | $0 | 0 seconds | Simple | Dies during earthquake if power cuts |
| + Supercap 10F | ~$1.50 | 30-45 seconds | Cheap, compact | Not for long-term |
| + Power bank 5000mAh | ~$5.00 | 4-8 hours | Safest | Needs routine recharge |
| + UPS module 18650 | ~$4.00 | 4-6 hours | Integrated | Larger size |

---

## 2. Node Discovery Design

### 2.1 Problem: TP-Link Deco "AP Isolation"

```
Problem with Deco (and all modern mesh routers):
┌──────────────────────────────────────────────────────┐
│  TP-Link Deco Network                                 │
│                                                       │
│  [Node 1] ──WiFi──► [Deco AP] ──Router──► Internet  │
│  [Node 2] ──WiFi──► [Deco AP]                        │
│                                                       │
│  ✗ Node 1 CANNOT see Node 2 directly                │
│    (AP Isolation / Client Isolation active by default)│
│  ✗ UDP Broadcast from Node 1 doesn't reach Node 2    │
│  ✗ mDNS/Bonjour does not work between nodes          │
└──────────────────────────────────────────────────────┘
```

**Chosen Solution: 2-Layer Discovery**

```
Layer 1: Server-side grouping (primary, internet)
  → All nodes report to mqtt.lindu.id
  → Server groups nodes based on:
     a. WiFi BSSID (Same AP MAC address) ← most accurate
     b. Configured location name
     c. GPS coordinates within N meters radius

Layer 2: ESP-NOW peer-to-peer (fallback, no-internet)
  → ESP-NOW operates on raw 802.11 layer, BYPASSING AP isolation
  → Node broadcasts ESP-NOW packet → other nodes within ~200m respond
  → Auto-discovery without router, without internet
```

### 2.2 ESP-NOW Discovery Protocol

```
When internet is available:
  Node ──MQTT──► Server ──► Server knows all peers in the same SSID/location

When internet is down (fallback):
  Node 1 broadcasts ESP-NOW: "LINDU_HELLO|node1|lat=-6.200|lon=106.816|pose=Flat"
  Node 2 receives → saves Node 1 as peer
  Node 2 replies: "LINDU_ACK|node2|lat=-6.195|lon=106.820|pose=Wall"
  
  After discovery:
  Node 1 detects quake → broadcasts ESP-NOW: "LINDU_QUAKE|ts=...|pga=...|rms=..."
  Node 2 receives → executes local consensus
  → Triggers local alarm if they agree
```

### 2.3 WiFi BSSID Grouping (Server-side)

```python
# In every MQTT status message, node sends:
{
  "node_id": "node1",
  "wifi_ssid": "MyOfficeWiFi",
  "wifi_bssid": "AA:BB:CC:DD:EE:FF",  # Connected AP MAC address
  "wifi_rssi": -65,
  "location_id": "building_a_fl1",    # configured during setup
  "pose": "Flat",                     # Node orientation
  "tilt_angle": 2.5                   # Node tilt angle
}

# Server logic:
def find_peer_nodes(reporting_node):
    # Priority 1: same location_id (most explicit)
    peers_by_location = db.query(nodes, location_id=reporting_node.location_id)
    
    # Priority 2: same WiFi BSSID (same physical AP)
    peers_by_bssid = db.query(nodes, wifi_bssid=reporting_node.wifi_bssid)
    
    # Priority 3: GPS radius < 500m
    peers_by_gps = db.query(nodes, 
        lat≈reporting_node.lat, lon≈reporting_node.lon, radius=500)
    
    return merge_unique(peers_by_location, peers_by_bssid, peers_by_gps)
```

### 2.4 Deco "Anonymous" / Client Isolation Handling

```
If AP Isolation is ACTIVE (Deco default):
  ✓ MQTT to internet → still works (through router to internet)
  ✗ Local UDP broadcast → fails
  ✗ mDNS → fails
  ✓ ESP-NOW → STILL WORKS (bypasses AP routing table)

Strategy:
  - ALWAYS use ESP-NOW for local mesh (regardless of AP settings)
  - Use MQTT server as primary coordination
  - mDNS/UDP only as a "nice to have" if AP isolation is OFF

How to detect AP Isolation from firmware:
  - Try sending a UDP broadcast to 255.255.255.255
  - If no response within 500ms → assume AP Isolation is active
  - Switch to ESP-NOW mode automatically
```

---

## 3. First-Time Setup / Provisioning Flow

### 3.1 State Machine ESP32

```
Power ON
    │
    ▼
[Check NVS]
    │
    ├── NVS empty / SETUP button pressed ──► [SETUP MODE]
    │
    └── NVS has data ──────────────────────► [NORMAL MODE]


┌─────────────────────────────────────────────────────────┐
│                     SETUP MODE                          │
│                                                         │
│  1. ESP32 creates WiFi AP: "LINDU-Setup-XXXX"          │
│     Password: "lindu1234" (default)                     │
│     LED: BLUE flashing slowly                           │
│                                                         │
│  2. User connects to AP "LINDU-Setup-XXXX"             │
│     Browser auto-redirects to 192.168.4.1              │
│     (Captive Portal)                                    │
│                                                         │
│  3. Web form appears:                                   │
│     ├── WiFi SSID (scan + pick from list)              │
│     ├── WiFi Password                                   │
│     ├── Location Name: "Server Room Floor 2"           │
│     ├── Node ID: "node1" (auto or manual)              │
│     ├── Latitude: -6.200000                            │
│     ├── Longitude: 106.816000                          │
│     ├── Timezone: "Asia/Jakarta"                       │
│     ├── Node Pose: [Wall / Flat]                       │
│     └── [SAVE & RESTART]                               │
│                                                         │
│  4. ESP32 tests WiFi connection                        │
│     ├── Success → save to NVS → RESTART to NORMAL      │
│     └── Failed → back to AP mode + error message       │
└─────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────┐
│                    NORMAL MODE                          │
│                                                         │
│  1. Connect to WiFi (from NVS)                         │
│     └── Failed 3x → enter SETUP MODE automatically    │
│                                                         │
│  2. Sync NTP                                           │
│  3. Connect MQTT (mqtt.lindu.id:8883 TLS)             │
│  4. Register node to server                            │
│  5. Start LSM6DS3 sampling                             │
│  6. ESP-NOW discovery broadcast                        │
│  7. RUNNING → normal loop                             │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Captive Portal UI (Web)

```html
<!-- Setup page design that appears in browser -->

LINDU.ID — Node Setup
══════════════════════

WiFi Network:  [▼ Drop-down scan: MyOffice, HomeWiFi, ...]
WiFi Password: [••••••••••••]

Node Location: [Server Room Floor 2            ]
Node ID:       [node1          ] (auto: lindu-ABC123)

Coordinates:   [-6.200000 ] [ 106.816000 ]
               [📍 Use Browser GPS]  ← if on smartphone

Timezone:      [▼ Asia/Jakarta (WIB)]
Pose:          [▼ Flat / Wall]

[Test WiFi Connection]    [Save & Restart]

Status: ○ Untested
```

### 3.3 Provisioning via BLE (Alternative/Addition)

```
If using ESP-IDF BLE WiFi Provisioning:
  - User doesn't need to join "LINDU-Setup" AP
  - User installs "ESP BLE Prov" app (Espressif official)
  - App scans BLE → finds "LINDU_node1"
  - App sends SSID+password via encrypted BLE
  - ESP32 saves to NVS, restarts normally

Pros: User doesn't need to switch WiFi on smartphone
Cons: Requires a custom app to set coordinates/location/pose
```

> [!NOTE]
> **Recommendation:** Implement **both** — WiFi Captive Portal as primary (zero-app), BLE as secondary/recovery. Captive Portal is more user-friendly for non-technical users.

### 3.4 Re-provisioning & Factory Reset

```cpp
// Hardware button behavior:
// SETUP button (GPIO 1):
//   Short press (< 3s): show IP address + status on OLED
//   Long press (3-10s): re-enter SETUP MODE (re-configure WiFi)
//   Very long press (>10s): FACTORY RESET — erase all NVS data

// LED feedback during factory reset:
// 10s → Red LED flashes rapidly → reset → reboot to SETUP MODE
```

---

## 4. Scenario 5 & 6 Design

### Scenario 5: 1 Node Only in Radius (Standalone Full)

```
Context: Deployment in a remote area / limited budget.
Only 1 ESP32 + sensor. No neighbor nodes.

Decision Tree:
         ┌─────────────────────────────────┐
         │   Local detects PGA > 0.01g    │
         └─────────────┬───────────────────┘
                       │
           ┌───────────▼───────────┐
           │  Internet available?  │
           └──────┬────────┬───────┘
                 YES       NO
                  │         │
    ┌─────────────▼┐       ┌▼─────────────────┐
    │ Wait BMKG   │       │ Standalone alarm  │
    │ confirmation│       │ direct (without   │
    │ (30-90s)    │       │ validation)       │
    └──────┬──────┘       └────────┬──────────┘
           │                       │
    ┌──────▼──────────────┐       │
    │  BMKG confirms?     │       │
    └──────┬──────┬───────┘       │
          YES    NO               │
           │      │               │
    DANGER  WARNING            WARNING
    level   level              level
    alert   (possible          (high FP risk,
            false alarm)        document this)
```

**Specific 1-node behavior:**
- Alert level max = **WARNING** (never DANGER without confirmation)
- BMKG/JMA becomes a mandatory validator
- Actuator: buzzer + LED active on WARNING
- Gas valve + door lock: only active on BMKG confirm (promoted to DANGER)
- Audio: play `p_wave_detected.wav` first → wait → `s_wave_warning.wav` if confirmed

### Scenario 6: 3 Nodes → 1 Node Drops Mid-Event (Hot Failover)

```
T+0.0s  Earthquake starts
T+2.2s  P-wave: Node 1 detects
T+2.3s  P-wave: Node 2 detects  
T+2.4s  P-wave: Node 3 detects ← BUT power cuts here due to quake!
                                   Node 3 sends "offline" LWT to broker

T+2.4s  Server receives: Node 3 offline (LWT message)
T+2.5s  Consensus Engine: update active_nodes = [node1, node2]
         Recalculate: need 2/2 (majority of remaining nodes)
         Node 1 + Node 2 = 2/2 → CONSENSUS REACHED ✓

T+2.7s  Alert published with notes: "1 node dropped during event"
T+2.9s  Actuator executes

Confidence adjustment:
  Base: 73% (3-node)
  Penalty: -10% (1 node dropped mid-event → incomplete data)
  Result: 63% → still above DANGER threshold (70%)? 
  
  → if < 70%: DANGER downgraded to WARNING
  → External BMKG check initiated immediately
  → If BMKG confirms: promoted back to DANGER
```

---

## 5. Complete System Architecture v2

```
┌────────────────────────────────────────────────────────────────────────┐
│                    LINDU.ID SYSTEM v2                                   │
└────────────────────────────────────────────────────────────────────────┘

EDGE LAYER:
┌────────────────────┐   ┌────────────────────┐   ┌────────────────────┐
│  SENSOR NODE 1     │   │  SENSOR NODE 2     │   │  ACTUATOR NODE     │
│  ESP32-S3 N16R8    │   │  ESP32-S3 N16R8    │   │  ESP32-S3 N16R8   │
│  LSM6DS3           │   │  LSM6DS3           │   │  Servo (gas valve) │
│  MAX98357A+Speaker │   │  MAX98357A+Speaker │   │  Solenoid Door     │
│  OLED 0.96"        │   │  OLED 0.96"        │   │  MAX98357A+Speaker │
│  USB-C 5V          │   │  USB-C 5V          │   │  USB-C 5V          │
│  [Supercap opt.]   │   │  [Supercap opt.]   │   │  [Supercap opt.]  │
└────────┬───────────┘   └────────┬───────────┘   └────────┬───────────┘
         │ WiFi MQTT TLS          │ WiFi MQTT TLS           │ WiFi MQTT TLS
         │ + ESP-NOW (mesh)       │ + ESP-NOW (mesh)        │
         └──────────────┬─────────┘                         │
                        │                                   │
              ┌─────────▼──────────────────────────────────┘
              │         mqtt.lindu.id (Server)
              │
         ┌────┴────────────────────────────────────────────┐
         │           SERVER APPLICATIONS                     │
         │                                                   │
         │  ┌─────────────┐  ┌────────────┐  ┌──────────┐  │
         │  │ MQTT Broker │  │ Consensus  │  │ Dashboard│  │
         │  │ (Mosquitto) │  │ Engine v2  │  │ API      │  │
         │  │             │  │            │  │ (React/  │  │
         │  │ - TLS 8883  │  │ - Hot      │  │  FastAPI)│  │
         │  │ - ACL       │  │   failover │  │ - Geoshake│ │
         │  │ - LWT       │  │ - Dynamic  │  │   style  │  │
         │  │   handling  │  │   quorum   │  │   UI     │  │
         │  └─────────────┘  └────────────┘  └──────────┘  │
         │                                                   │
         │  ┌────────────────────────────────────────────┐  │
         │  │ DATABASE (PostgreSQL - Dockerized)          │  │
         │  │ Stores node states, events, and metrics     │  │
         │  └────────────────────────────────────────────┘  │
         │                                                   │
         │  ┌────────────────────────────────────────────┐  │
         │  │ API INTEGRATOR                              │  │
         │  │ BMKG polling (60s) + JMA WebSocket (real)  │  │
         │  └────────────────────────────────────────────┘  │
         └───────────────────────────────────────────────────┘

NODE DISCOVERY LAYER:
  Primary:   MQTT server grouping (by BSSID + location_id + GPS)
  Fallback:  ESP-NOW peer-to-peer (bypass AP isolation, 200m range)
  Detection: UDP probe → if no response → switch to ESP-NOW auto
```

---

## 6. NVS Config Schema (Data Stored in Flash)

```cpp
// Namespace: "lindu-cfg" in NVS (encrypted)
struct LinduConfig {
    // WiFi
    char wifi_ssid[64];
    char wifi_password[64];
    
    // Identity
    char node_id[32];          // "node1", "actuator1", etc.
    char node_role[16];        // "sensor" | "actuator"
    char location_id[64];      // "building_a_fl1" — for grouping
    char location_name[128];   // "Server Room Floor 1 Building A"
    char pose[16];             // "Flat" or "Wall"
    
    // GPS (manual input)
    float lat;                 // -6.200000
    float lon;                 // 106.816000
    int   altitude_m;          // 10
    
    // Server
    char mqtt_host[128];       // "mqtt.lindu.id"
    int  mqtt_port;            // 8883
    char mqtt_user[64];        // username from provisioning
    char mqtt_pass[64];        // password from provisioning
    
    // Behavior thresholds (configurable, defaults built-in)
    float pga_threshold_g;     // default: 0.01g
    float sta_lta_threshold;   // default: 3.5
    bool  audio_enabled;       // default: true
    int   audio_volume;        // 0-100, default: 80
    bool  supercap_present;    // default: false
    
    // Timezone
    char timezone[32];         // "WIB-7" (POSIX format)
    
    // Provisioning status
    bool  provisioned;         // false = not setup
    char  firmware_version[16];
    uint32_t setup_timestamp;  // when last configured
};
```

---

## 7. LED + Audio State Machine

```
State                  LED Pattern              Audio
─────────────────────  ──────────────────────   ──────────────────────
BOOT                   All ON 1 second          —
SETUP_MODE             Blue flash 1Hz           "Entering setup mode..."
WIFI_CONNECTING        Blue flash 5Hz           —
WIFI_CONNECTED         Blue ON 3 seconds        "WiFi connected"
MQTT_CONNECTING        Green flash 5Hz          —
RUNNING (normal)       Green ON, flash 1/30s    —
P_WAVE_DETECTED        Yellow fast              "Early warning..."
S_WAVE_WARNING         Red solid                "DANGER! Earthquake!"
DANGER_FULL            Red strobe 4Hz           Alarm + instructions
ALL_CLEAR              Green flash 3x           "Safe"
NODE_OFFLINE_WARN      Yellow 1Hz               "Sensor disconnected"
ERROR                  Red + White alt.         —
FACTORY_RESET          All flashing 10Hz        —
```

---

## 8. Recommended Design Decisions

| Aspect | Recommendation | Rationale |
|-------|-------------|--------|
| MCU | ESP32-S3 N16R8 | Native USB-C, 16MB flash, 8MB PSRAM for audio |
| Audio | MAX98357A + 4Ω 3W speaker | I2S quality, stereo capable, +$2.50 |
| Power | USB-C + Supercap 10F ($1.50) | Minimal safety buffer 30-45 seconds |
| Provisioning | WiFi Captive Portal primary + BLE optional | User-friendly, no-app option |
| Discovery | ESP-NOW + Server BSSID grouping | Bypasses AP isolation, offline capable |
| Coordinates | Manual input on web form + GPS browser | No extra GPS chip needed |
| Audio format | WAV 16-bit 22050Hz mono in SPIFFS | Simple decode, sufficient for speech |
| Alert logic | 1-node = WARNING max; 2+ nodes = DANGER capable | Minimizes false positives |
| Hot failover | Dynamic quorum adjustment on node drop | Maintains operation |


---
