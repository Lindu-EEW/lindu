# Lindu-EEW: Realistic Earthquake & Physical Disturbance Dataset

## 1. Overview

This dataset accurately models real-world physical vibrations captured by a 3-node residential IoT network (**Node A**, **Node B**, and **Node C** equipped with **LSM6DS3 / MPU-6050** IMUs). 

It distinguishes genuine **tectonic earthquakes** from common domestic shocks (**foot stomps, desk shakes, door slams, dropped objects, and road traffic**) and logs the resulting **solenoid gas valve and door lock actuation responses**.

---

## 2. Dataset Files

| File | Rows | Format | Description |
|---|:---:|---|---|
| [`realistic_dataset.csv`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/realistic_dataset.csv) | **10,000** | CSV | Comprehensive balanced dataset with real-world physical scenarios & solenoid logs. |
| [`realistic_earthquake_and_disturbances_10000.json`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/realistic_earthquake_and_disturbances_10000.json) | **10,000** | JSON | Machine-readable format of the complete 10,000-sample dataset. |
| [`real_earthquakes_usgs_1000.csv`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/real_earthquakes_usgs_1000.csv) | **1,000** | CSV | **Real online earthquakes from USGS** (M3.9 - M7.8) with GMPE ground motions & solenoid logs. |
| [`bmkg_latest_earthquakes.json`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/bmkg_latest_earthquakes.json) | — | JSON | **Real online Indonesian earthquakes from BMKG** (`autogempa`, `gempadirasakan`, `gempaterkini`). |
| [`fetch_online_real_earthquakes.py`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/fetch_online_real_earthquakes.py) | — | Python | Live fetcher querying USGS & BMKG REST endpoints. |
| [`generate_realistic_dataset.py`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/generate_realistic_dataset.py) | — | Python | Generator script with physical kinematics, spatial consensus, and solenoid logic. |

---

## 3. Physical Event Taxonomy & Solenoid Behavior

| Event Category | Subtype | Physical Signature | Spatial Consensus | Solenoid Gas Valve | Solenoid Door Lock | Solenoid Log Action |
|---|---|---|:---:|:---:|:---:|---|
| **Earthquake** | `minor`, `moderate`, `strong`, `severe` | Low freq ($0.8 - 6.5\text{ Hz}$), sustained duration ($10 - 95\text{ s}$), multiaxial ($X, Y, Z$) | **REACHED** (All 3 nodes correlated) | **SHUTOFF** (`DISABLED`, `RELAY_OFF`, $142\text{ ms}$) | **UNLOCKED** (`RELAY_ON`, $175\text{ ms}$) if occupied | `[ALARM][SOLENOID] Quake M5.4 confirmed by 3-Node Consensus -> Valve SHUTOFF, Door UNLOCKED` |
| **Foot Stomp** | `heavy_stomp` | Localized high-g spike ($0.12 - 0.35\text{ g}$), High freq ($18 - 36\text{ Hz}$), vertical Z-axis dominant, brief ($< 1.2\text{ s}$) | **FAILED** (Only 1 node triggered) | **OPEN** (`ENABLED`, `RELAY_ON`) | **LOCKED** (`RELAY_OFF`) | `[FILTER][REJECTED] Foot Stomp on Node A (Single-node only, Node B & C calm) -> Actuators Safe` |
| **Manual Shake** | `table_desk_shake` | High localized shaking ($0.15 - 0.45\text{ g}$), heavy single-axis jerk ($da/dt$), $2 - 7\text{ s}$ | **FAILED** (Only 1 desk/post agitated) | **OPEN** (`ENABLED`, `RELAY_ON`) | **LOCKED** (`RELAY_OFF`) | `[FILTER][REJECTED] Manual Desk Shake on Node B -> Consensus FAILED -> Actuators Safe` |
| **Door Slam** | `door_slam_shock` | Severe horizontal impact ($0.11 - 0.38\text{ g}$), very high freq ($26 - 52\text{ Hz}$), transient $< 0.5\text{ s}$ | **FAILED** (Structural transient) | **OPEN** (`ENABLED`, `RELAY_ON`) | **LOCKED** (`RELAY_OFF`) | `[FILTER][REJECTED] Door Slam on Node A -> High-frequency transient rejected -> Actuators Safe` |
| **Dropped Object** | `floor_impact` | Sharp acoustic impact ($0.08 - 0.25\text{ g}$), high freq ($32 - 58\text{ Hz}$), transient $< 0.3\text{ s}$ | **FAILED** (Localized point impact) | **OPEN** (`ENABLED`, `RELAY_ON`) | **LOCKED** (`RELAY_OFF`) | `[FILTER][REJECTED] Dropped Object impact -> No dual-node correlation -> Solenoids Safe` |
| **Passing Truck** | `road_traffic_vibration` | Low continuous vibration ($0.02 - 0.08\text{ g}$), medium freq ($16 - 32\text{ Hz}$), $\text{STA/LTA} < 3.2$ | **FAILED** (Below alert threshold) | **OPEN** (`ENABLED`, `RELAY_ON`) | **LOCKED** (`RELAY_OFF`) | `[MONITOR] Heavy Vehicle vibration -> STA/LTA < 3.5 threshold -> Nominal logging` |
| **Ambient Noise** | `sensor_ambient_drift` | Quiet room baseline ($\text{PGA} < 0.014\text{ g}$), sensor thermal drift | **NONE** | **OPEN** (`ENABLED`, `RELAY_ON`) | **LOCKED** (`RELAY_OFF`) | `[MONITOR] Ambient calm baseline -> Telemetry nominal` |

---

## 4. Machine Learning Evaluation (2,000 Held-Out Samples)

Trained on 8,000 samples and evaluated on 2,000 held-out test samples:

```text
=== REALISTIC DATASET ML EVALUATION (N=2,000 Test Samples) ===
Accuracy:    100.00%
Precision:   100.00%
Recall:      100.00%
F1-Score:    100.00%
Confusion:   [TP: 1017 | FP: 0]
             [FN: 0    | TN: 983]

```

---

## 5. Real Historical Database Datasets (`lindu_db` TimescaleDB)

Directly extracted from the live PostgreSQL/TimescaleDB container across **1 full month of continuous operation** (September 16, 2026 – October 16, 2026):

| Dataset File | Rows | Format | Description |
|---|:---:|---|---|
| [`historical_db_telemetry_29k.csv`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/historical_db_telemetry_29k.csv) | **30,228** | CSV | Raw streaming physical sensor telemetry from all 3 ESP32 nodes (`node_acbd13f9`, `node_2418399e`, `node_3c096f0c`). |
| [`ai_historical_features.csv`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/ai_historical_features.csv) | **3,021** | CSV | **Preprocessed 10-second feature windows** with kinetic variance, peak PGA, RMS, gas anomalies, and classification labels. |
| [`historical_db_alerts.csv`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/historical_db_alerts.csv) | **111** | CSV | Actual consensus alert triggers ($M 5.6 - 7.8$) with computed wave velocities and epicenter coordinates. |
| [`historical_db_node_logs.csv`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/historical_db_node_logs.csv) | **1,902** | CSV | Remote serial syslog messages capturing device tilts, poses, heartbeats, and actuator events. |
| [`process_historical_for_ai.py`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/process_historical_for_ai.py) | — | Python | Feature engineering pipeline extracting time-series windows and anomaly labels for AI training. |

### AI Research Applications
1. **Unsupervised Anomaly Detection:** Train Autoencoders or Isolation Forests on the 1,953 `NORMAL_BASELINE` windows to establish dynamic sensor noise floors without rigid static thresholds.
2. **Supervised Shock Classification:** Train 1D-CNNs or LSTMs on `SHOCK_VIBRATION` (964 windows) to classify early P-wave precursors vs domestic bumps.
3. **Multimodal Environmental Fusion:** Correlate seismic IMU shocks with gas readings (`avg_gas_raw`) to model earthquake-induced gas leaks in residential dwellings.

---

## 6. Earthquake Episode Grouping for Early Prediction AI

Segmented from continuous streaming telemetry into discrete physical episodes:

| Dataset File | Rows | Format | Description |
|---|:---:|---|---|
| [`historical_db_grouped_by_event.csv`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/historical_db_grouped_by_event.csv) | **30,228** | CSV | Complete telemetry with `event_id`, `event_phase` (`PRE_SHOCK`, `P_WAVE_ONSET`, `S_WAVE_PEAK`, `CODA_DECAY`), and `seconds_from_onset`. |
| [`historical_earthquake_episodes_index.csv`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/historical_earthquake_episodes_index.csv) | **177** | CSV | **Catalog of 177 distinct episodes** (51 Multi-Node Earthquakes, 126 Local Disturbances) with peak PGA, lead time, and actuator outcomes. |
| [`group_historical_events_for_ai.py`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/group_historical_events_for_ai.py) | — | Python | Segmentation script detecting wave arrivals, spatial agreement, and clustering time windows. |
| [`train_prediction_model.py`](file:///Users/likotjhang/Library/CloudStorage/GoogleDrive-eaprilitrisno@gmail.com/My%20Drive/Documents/Indonesia/Eko%20-%20Master/Semester%201/IOT%20-%20Suryadiputra%20Liawatimena/Project%20Group%209/Idea%201%20-%20Eearthquake%20Warning/dataset/train_prediction_model.py) | — | Python | Predictive model achieving **97.22% Accuracy** and **100% Recall** on held-out earthquake episodes. |

