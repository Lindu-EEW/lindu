
<!-- START OF 09_DASHBOARD.md -->
# 📊 Dashboard Design — lindu.id

## 1. Frontend Architecture (React Dashboard & Zero-Latency WebSockets)

Unlike traditional web applications that utilize a Request-Response pattern via REST APIs, the Lindu.id Dashboard is built as a **React Dashboard** utilizing a **Zero-Latency MQTT WebSockets** architecture.

This means the React frontend application on the client-side (Browser) establishes a direct connection to the **Mosquitto MQTT Broker (Port 9001)**. 

**Advantages of this Architecture:**
1. **Lightning Fast:** When the Python server issues an `ALARM_ON` command, the message reaches the Browser and the Siren Actuators at the **exact same millisecond**. There is no API intermediary. The **Consensus algorithm in Python strictly prevents false positives and groups multiple nodes using Haversine P-Wave velocity limits** before triggering this alarm.
2. **Highly Efficient:** It relies directly on MQTT for real-time telemetry, making the React application highly responsive.

---

## 2. Key Dashboard Features (Ops Center)

The React Dashboard now features a comprehensive **"Geoshake-style" UI** designed for professional seismic monitoring.

### A. Geoshake-Style UI & Command Center
Utilizes a dark mode map interface (e.g., CartoDB Dark Matter) so that emergency indicator colors (Red/Orange/Green) are highly contrasting and easily visible to monitoring personnel. Key features include **Animated epicenters**, **PGA-based color-coded nodes**, and a **Helicorder 24h mockup**.

### B. Live Node Tracking & Detail Modals
*   The browser subscribes to the `lindu/sensor/+/status` topic.
*   **Bright Green:** ESP32 with LSM6DS3 sensor node is online and healthy.
*   **Faded Red:** Node is offline. If multiple ESP32 nodes in a city suddenly go offline simultaneously following an earthquake, authorities can infer a severe power/internet blackout caused by the event.
*   **Node Detail Modals:** Clicking a sensor node opens detailed modals displaying the latest **RMS & PGA metrics** in real-time, sourced from the `lindu/sensor/+/event` topic.

### C. JMA-Style S-Wave Animation & Animated Epicenters
*   The browser subscribes to the global alarm topic `lindu/actuator/cmd/all`.
*   If an `ALARM_ON` command is received, the screen immediately flashes red (Emergency Flash Effect).
*   The system focuses the camera on the epicenter and renders **Animated epicenters** with expanding red circles (CSS Animation) corresponding to the `radius_km` danger zone reported by the server.

### D. "Time Machine" (Playback Timeline Slider)
*   The system stores every incoming alarm in local memory (`quakeDatabase`).
*   A playback slider `<input type="range">` is available at the bottom of the screen.
*   Dragging the slider to the left removes future events and redraws historical earthquake points, allowing users to visually replay the sequence of seismic events.
*   *(Note: Currently utilizing a mockup array. In Phase 2, historical data will be injected via FastAPI from the **PostgreSQL (Dockerized)** database).*

---

## 3. MQTT Topics Monitored by the Frontend

| Topic | Function | Payload |
|-------|----------|---------|
| `lindu/sensor/+/status` | Updates ESP32 sensor node map pin location and color (Online/Offline) | `{"node_id": "...", "status": "online", "lat": -6.2, "lon": 106.8}` |
| `lindu/sensor/+/event` | Updates numerical metrics (RMS & PGA) within the Node Detail Modals | `{"node_id": "...", "pga": 0.05, "sta_lta": 5.2}` |
| `lindu/actuator/cmd/all`| Triggers the red screen animation and Hazard Radius Map | `{"cmd": "ALARM_ON", "epi_lat": -6.9, "epi_lon": 107.6, "radius_km": 150, "desc": "Earthquake..."}` |

---

## 4. How to Run

Since it runs in Docker:
1. Start the main system: `docker-compose up -d --build`
2. Open in browser: `http://localhost` (if local) or `http://<YOUR-VPS-IP>` (if on a VPS).
3. To test a manual alarm injection (Simulation):
   ```bash
   mosquitto_pub -h localhost -p 1883 -t "lindu/actuator/cmd/all" -m '{"cmd": "ALARM_ON", "epi_lat": -6.82, "epi_lon": 107.14, "radius_km": 150, "desc": "Thesis Trial"}'
   ```


---

<!-- START OF 15_SIMULATION_REPORT.md -->
# 🌋 M5.9 Earthquake Simulation Report — Lindu.id

> **Scenario:** M5.9 Earthquake, 12km depth, epicenter 5.8km from the sensor  
> **Simulation Duration:** 360 seconds (5 minutes of shaking + 1 minute coda)  
> **Sensor Sample Rate:** 104 Hz (Standard LSM6DS3 seismic rate)

---

## Earthquake Physics Parameters

| Parameter | Value |
|-----------|-------|
| Magnitude | **M 5.9** (Richter/Mw) |
| Epicenter | -6.150°S, 106.800°E |
| Depth | 12 km (shallow crustal) |
| Seismic Moment | 7.94 × 10¹⁷ N·m |
| Shaking Duration | ~28 seconds (S-wave + coda) |
| Total Shake | ~5 minutes (including surface waves) |

### Wave Arrival Times per Node

| Node | Distance | P-wave Arrival | S-wave Arrival | Predicted PGA | MMI |
|------|----------|----------------|----------------|---------------|-----|
| Node 1 (Building A) | 5.8 km | T + **2.22s** | T + **3.81s** | 1.690g | X+ |
| Node 2 (Building B) | 5.5 km | T + **2.20s** | T + **3.77s** | 1.715g | X+ |
| Node 3 (Building C) | 6.3 km | T + **2.26s** | T + **3.87s** | 1.661g | X+ |
| Actuator | 5.8 km | — | T + **3.81s** | 1.690g | X+ |

> **S-P interval:** ~1.58s → early warning window before main shaking

---

## Simulation Waveforms (3 Nodes)

![Acceleration waveform and STA/LTA ratio M5.9](/Users/likotjhang/.gemini/antigravity/brain/a862d96c-2e98-45da-ab7b-39956704063d/waveforms_M59.png)

*Left graph: PGA & RMS (g) per node streamed via MQTT — dashed red line = detection threshold (0.01g)*  
*Right graph: STA/LTA ratio — solid red line = trigger threshold (3.5)*  
*Orange line = P-wave arrival, solid red = S-wave arrival (destructive phase)*  
*Note: These waveforms can now be visualized dynamically on our React Dashboard using the Geoshake-style UI (Helicorder 24h mockup, RMS & PGA metrics).*

---

## Scenario Comparison

![Confidence, consensus time, and actuator time comparison](/Users/likotjhang/.gemini/antigravity/brain/a862d96c-2e98-45da-ab7b-39956704063d/scenario_comparison.png)

---

## Results of 4 Test Cases

### 🔴 Scenario 1 — No Internet (Wi-Fi Mesh Fallback)

**Condition:** ISP down, nodes communicate via ESP-NOW, no NTP sync

| Metric | Result | Status |
|--------|--------|--------|
| Alert Level | WARNING | ✓ |
| Confidence | 49% | ✗ (target ≥55%) |
| Magnitude Est | M 5.5 (error: 0.4) | ✓ |
| Time to Consensus | 340ms | ✓ <500ms |
| Time to Actuator | 490ms | ✓ <3000ms |
| Before S-wave? | **+1.08s earlier** | ✓ |
| Epicenter | N/A (2-node, no triangulation) | — |

**Clock Sync (Critical!):**
- Node 1 offset: **+250ms** (no NTP)  
- Node 2 offset: **-341ms** (no NTP)  
- Inter-node skew: **~591ms** → TDOA error ±2.1km
- Inaccurate triangulation without NTP

**Verdict:** ⚠️ **PARTIAL FAIL** — alert sent and actuator triggered, but confidence is below ideal due to lack of external validation & high clock skew. All simulation results stored locally, later synced to PostgreSQL.

---

### 🟢 Scenario 2 — 2 Nodes + Internet (Baseline)

**Condition:** 2 active nodes, internet available, NTP synced, active BMKG polling

| Metric | Result | Status |
|--------|--------|--------|
| Alert Level | **DANGER** | ✓ |
| Confidence | **73%** | ✓ ≥70% |
| Magnitude Est | M 5.5 (error: 0.4) | ✓ |
| Time to Consensus | **250ms** | ✓ <500ms |
| Time to Actuator | **400ms** | ✓ <2000ms |
| Before S-wave? | **+1.10s earlier** | ✓ |
| Epicenter Error | ±5.2km | Rough (2-node) |

**Clock Sync:**
- Node 1: **+3.0ms** (NTP excellent)
- Node 2: **-2.0ms** (NTP excellent)
- Skew: **4.9ms** → TDOA error only ±0.02km ✓

**Actuator Timeline:**
```
T+2.20s  P-wave detected by node2
T+2.22s  P-wave detected by node1
T+2.47s  Consensus reached → MQTT alert published
T+2.62s  Actuator receives command
T+2.72s  ✓ Alarm ACTIVATED
T+2.92s  ✓ Gas valve CLOSED
T+3.42s  ✓ Door lock OPENED
T+3.77s  ← S-wave arrives (destructive phase)
          → WARNING 1.10s BEFORE S-wave! ✓
```

**Verdict:** ✅ **PASS** — System functions optimally. All actuators activate before the S-wave arrives. Data safely logged to Dockerized PostgreSQL.

---

### 🟢 Scenario 3 — Internet + 3 Active Nodes (Best Case)

**Condition:** 3 active sensor nodes, internet, NTP, BMKG + TDOA triangulation

| Metric | Result | Status |
|--------|--------|--------|
| Alert Level | **DANGER** | ✓ |
| Confidence | **73%** | ✗ (target ≥80%, needs tuning) |
| Magnitude Est | M 5.5 (error: 0.4) | ✓ |
| Time to Consensus | **250ms** | ✓ <500ms |
| Time to Actuator | **400ms** | ✓ <1500ms |
| Before S-wave? | **+1.17s earlier** | ✓ |
| Epicenter Error | **±2.8–3.9km** | ✓ Much more accurate |

**Clock Sync:**
- All nodes: ±3–6ms (NTP excellent)
- Max skew: <10ms → Precision TDOA ±0.04km ✓

**Improvement vs Scenario 2:**
- Epicenter error reduced from ±5.2km → **±2.8-3.9km** (40% more accurate)
- Full TDOA triangulation active
- BMKG validation + 3-node majority voting

**Verdict:** ✅ **PASS (functional)** — Alert and actuators work perfectly. Confidence 73% vs 80% target → need to calibrate scoring weights for the 3-node case.

---

### 🟡 Scenario 4 — Internet + 1 Node Only (Degraded)

**Condition:** Node 2 offline (power failure), only Node 1 active

| Metric | Result | Status |
|--------|--------|--------|
| Alert Level | **WARNING** | ✓ |
| Confidence | **43%** | ✓ ≥30% |
| Magnitude Est | M 5.5 (error: 0.4) | ✓ |
| Time to Consensus | **250ms** | ✓ |
| Time to Actuator | **400ms** | ✓ |
| Before S-wave? | **+1.19s earlier** | ✓ |
| Triangulation | ❌ Not available | — |

**System Behavior:**
- Single-node detection → confidence capped ~43%
- Alert level: WARNING (not DANGER) — safe, no full trigger
- BMKG validation (+15 confidence points) is crucial in this scenario
- Actuator still operates despite WARNING level alert

**Verdict:** ✅ **PASS** — System is degraded but still functional. Warning sent over 1 second before S-wave.

---

## Comparative Summary

| Sc | Scenario | Conf | Level | Mag Est | Consensus | Actuator | Epi Error | Verdict |
|----|----------|------|-------|---------|-----------|----------|-----------|---------|
| 1 | No Internet (Mesh) | 49% | WARNING | M5.5 | 340ms | 490ms | N/A | ⚠️ PARTIAL |
| 2 | 2 Nodes + Internet | 73% | **DANGER** | M5.5 | **250ms** | **400ms** | ±5.2km | ✅ PASS |
| 3 | 3 Nodes + Internet | 73% | **DANGER** | M5.5 | **250ms** | **400ms** | **±3.9km** | ✅ PASS |
| 4 | 1 Node + Internet | 43% | WARNING | M5.5 | 250ms | 400ms | N/A | ✅ PASS |

> **All scenarios:** actuators operate **before the S-wave arrives** ✓  
> **Critical metric:** time between alert and S-wave = **+1.08 – +1.19 seconds**

---

## Time Synchronization (Clock Sync) Analysis

This is the **most critical factor** affecting triangulation accuracy:

```
┌─────────────────────────────────────────────────────────────────┐
│ Condition           │ Clock Skew  │ TDOA Error  │ Recommendation  │
├─────────────────────┼─────────────┼─────────────┼───────────────┤
│ With NTP (Sc 2-4)   │ < ±10ms     │ ±0.04km     │ ✓ Use           │
│ No NTP, idle <1hr   │ ±50-200ms   │ ±0.6km      │ ⚠ Still OK     │
│ No NTP, idle 2+ hrs │ ±200-600ms  │ ±2.1km      │ ✗ Avoid         │
│ GPS PPS (upgrade)   │ < ±1ms      │ ±0.004km    │ ✓✓ Best         │
└─────────────────────┴─────────────┴─────────────┴───────────────┘
```

**Impact of clock skew on detection:**
- Node 1 S-P interval (true): **1.588s**
- Sc.1 clock skew (591ms): distance error **±2.07km (35.5%)** ❌
- Sc.2 clock skew (4.9ms): distance error **±0.02km (0.3%)** ✅

---

## Findings & Recommendations

### ✅ What Works Well
1. **P-wave detection** successful in all scenarios — even the worst case
2. **Actuator is always faster than the S-wave** — margin of 1–1.2 seconds
3. **NTP clock sync** provides excellent TDOA accuracy (±0.02km)
4. **Magnitude estimation** is accurate: M5.5 estimate vs M5.9 true (only 0.4 error)
5. **Consensus time** consistently 250-340ms — well below the 500ms target

### ⚠️ Issues to Address

| Issue | Impact | Solution |
|-------|--------|--------|
| No-Internet scenario: confidence 49% (target 55%) | WARNING instead of DANGER | Increase voting weight for nodes without external validation |
| 3-Node scenario: confidence 73% (target 80%) | Needs tuning | Increase 3-node agreement weight in scoring |
| PGA at trigger = P-wave (small) | Magnitude underestimated at trigger | Use rolling peak PGA during the consensus window |
| No NTP: clock skew up to 591ms | TDOA error ±2km | Implement the clock sync solutions below |

### 🔧 Clock Error Minimization Solutions (Priority)

1. **NTP on every WiFi reconnect** (not just hourly)  
   → Eliminates drift after internet returns
   
2. **Save UTC in RTC chip or NVS before sleep**  
   → ESP32 RTC drift is only ±5ppm vs crystal ±50ppm
   
3. **MQTT time broadcast** `lindu/system/time` from server  
   → Nodes can sync via MQTT if ISP blocks NTP
   
4. **Send `clock_confidence` in every MQTT payload**  
   → Server assigns lower weight to nodes with high skew
   
5. **30-second buffer window + timestamp tolerance**  
   → Accept detections from nodes with clock offsets up to ±2 seconds
   
6. **(Upgrade) GPS NEO-6M module** ~$5.00/node  
   → Sub-millisecond accuracy, eliminates all clock issues

---

## Simulation Files

| File | Description |
|------|-----------|
| [`earthquake_simulator.py`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/simulation/earthquake_simulator.py) | Earthquake physics: PGA, GMPE, waveform generator |
| [`consensus_engine_sim.py`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/simulation/consensus_engine_sim.py) | Consensus engine + time sync simulator |
| [`run_simulation.py`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/simulation/run_simulation.py) | Runner: 4 scenarios + report + plot |

**How to run:**
```bash
cd simulation/
python3 run_simulation.py           # all scenarios + plot
python3 run_simulation.py --no-plot # without chart
python3 run_simulation.py --scenario 3  # specific scenario only
```


---
