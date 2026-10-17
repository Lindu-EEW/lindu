#!/usr/bin/env python3
"""
Lindu-EEW: 1,000 Earthquake Episodes Dataset Generator for AI Prediction
Generates exactly 1,000 True Earthquake Episodes + 500 Control Disturbance Episodes.

Features per Episode:
1. Seismological Parameters:
   - episode_id: EQ_EP_0001 to EQ_EP_1000 (and DISTURB_EP_0001 to DISTURB_EP_0500)
   - category: MULTI_NODE_EARTHQUAKE vs LOCAL_DISTURBANCE
   - magnitude: M3.0 to M7.8 (or 0.0 for disturbance)
   - depth_km: 5.0 to 120.0 km
   - epicentral_dist_km: 15.0 to 500.0 km
   - p_to_s_lead_time_sec: Theoretical & physical P-to-S interval based on Omori's law:
     t_lead = R * (1/Vs - 1/Vp) where Vp=6.0 km/s, Vs=3.5 km/s (~0.119 s/km)
   - peak_pga: Peak Ground Acceleration at building (in g)
   - peak_rms: Root Mean Square acceleration (in g)
   - dominant_freq_hz: Frequency via ZCR (0.8 - 5.5 Hz for quakes vs 18-50 Hz for shocks)
   - total_duration_sec: Shaking duration (10 - 95 seconds)

2. Multi-Station Sensor Readings:
   - node_a_pga, node_b_pga, node_c_pga (accelerations across all 3 nodes)
   - nodes_consensus_count: 2 or 3 for earthquakes, 1 for local disturbances

3. Hardware Solenoid Actuator Logs:
   - solenoid_valve_status: "DISABLED" (Shutoff) vs "ENABLED" (Open)
   - solenoid_door_status: "UNLOCKED" (if occupants present) vs "LOCKED" (secure)
   - valve_latency_ms: Milliseconds to shutoff gas line (118 - 175 ms)
   - door_latency_ms: Milliseconds to unlock door latch (135 - 210 ms)
   - solenoid_log: Structured execution log formatted for tb_node_logs
"""

import csv
import json
import math
import os
import random
from datetime import datetime, timezone, timedelta

SEED = 42
random.seed(SEED)

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOG_CSV = os.path.join(OUTPUT_DIR, "earthquake_1000_episodes_catalog.csv")
CATALOG_JSON = os.path.join(OUTPUT_DIR, "earthquake_1000_episodes_catalog.json")

def generate_earthquake_episode(ep_id, base_time):
    # Tier distribution across 1,000 earthquakes:
    # 1-300: Minor (300)
    # 301-700: Moderate (400)
    # 701-900: Strong (200)
    # 901-1000: Severe (100)
    if ep_id <= 300:
        tier = "minor_earthquake"
        mag = round(random.uniform(3.0, 4.4), 1)
        dist_km = random.uniform(15.0, 85.0)
        depth_km = random.uniform(5.0, 25.0)
        pga_base = random.uniform(0.025, 0.075)
        freq_hz = round(random.uniform(1.8, 6.2), 1)
        duration_s = round(random.uniform(12.0, 28.0), 1)
        sta_lta = round(random.uniform(3.1, 5.8), 2)
    elif ep_id <= 700:
        tier = "moderate_earthquake"
        mag = round(random.uniform(4.5, 5.9), 1)
        dist_km = random.uniform(25.0, 180.0)
        depth_km = random.uniform(10.0, 45.0)
        pga_base = random.uniform(0.075, 0.220)
        freq_hz = round(random.uniform(1.2, 4.8), 1)
        duration_s = round(random.uniform(22.0, 50.0), 1)
        sta_lta = round(random.uniform(5.5, 14.5), 2)
    elif ep_id <= 900:
        tier = "strong_earthquake"
        mag = round(random.uniform(6.0, 6.9), 1)
        dist_km = random.uniform(30.0, 320.0)
        depth_km = random.uniform(10.0, 80.0)
        pga_base = random.uniform(0.220, 0.950)
        freq_hz = round(random.uniform(0.9, 3.5), 1)
        duration_s = round(random.uniform(40.0, 75.0), 1)
        sta_lta = round(random.uniform(10.0, 20.0), 2)
    else:
        tier = "severe_earthquake"
        mag = round(random.uniform(7.0, 7.8), 1)
        dist_km = random.uniform(20.0, 480.0)
        depth_km = random.uniform(10.0, 120.0)
        pga_base = random.uniform(0.750, 3.500)
        freq_hz = round(random.uniform(0.6, 2.4), 1)
        duration_s = round(random.uniform(60.0, 120.0), 1)
        sta_lta = round(random.uniform(15.0, 20.0), 2)

    # Physical P-to-S lead time (Omori's law): t_lead = R * (1/Vs - 1/Vp)
    # Vp = 6.0 km/s, Vs = 3.5 km/s -> factor = 0.119 s/km
    hypo_dist = math.sqrt(dist_km**2 + depth_km**2)
    p_to_s_lead_sec = round(max(2.5, min(65.0, hypo_dist * 0.119 + random.uniform(-1.0, 1.5))), 2)

    # Multi-node sensor coupling across 3 nodes
    node_a_pga = round(pga_base * random.uniform(0.92, 1.08), 5)
    node_b_pga = round(pga_base * random.uniform(0.90, 1.10), 5)
    node_c_pga = round(pga_base * random.uniform(0.88, 1.06), 5)
    peak_pga = max(node_a_pga, node_b_pga, node_c_pga)
    peak_rms = round(peak_pga * random.uniform(0.48, 0.65), 5)
    nodes_count = 3 if peak_pga >= 0.04 else random.choice([2, 3])

    # Environmental & Occupancy
    occupancy_recent = random.random() < 0.75
    gas_leak_prob = 0.04 if mag < 5.0 else (0.16 if mag < 6.5 else 0.35)
    has_gas_leak = random.random() < gas_leak_prob
    gas_raw = random.randint(2200, 3900) if has_gas_leak else random.randint(300, 520)

    # Solenoid Actuation
    solenoid_valve_status = "DISABLED"
    solenoid_valve_relay = 0 # Power cut to fail-safe NC valve
    valve_latency_ms = random.randint(118, 175)

    if occupancy_recent:
        solenoid_door_status = "UNLOCKED"
        solenoid_door_relay = 1 # Energized to release latch
        door_latency_ms = random.randint(135, 208)
        door_desc = f"Door UNLOCKED in {door_latency_ms}ms (Occupants detected for egress)"
    else:
        solenoid_door_status = "LOCKED"
        solenoid_door_relay = 0
        door_latency_ms = 0
        door_desc = "Door KEPT LOCKED (No occupants, anti-trespass safe)"

    e2e_latency_ms = max(valve_latency_ms, door_latency_ms) + random.randint(130, 240)
    onset_time = base_time + timedelta(seconds=ep_id * 35)
    iso_time = onset_time.strftime("%Y-%m-%d %H:%M:%S+00")

    solenoid_log = (
        f"[ALARM][SOLENOID] Quake M{mag} confirmed by {nodes_count}-Node Consensus | "
        f"Dist={dist_km:.1f}km, LeadTime={p_to_s_lead_sec}s | "
        f"PGA={peak_pga:.4f}g, Freq={freq_hz:.1f}Hz | "
        f"Gas Solenoid Valve SHUTOFF in {valve_latency_ms}ms | "
        f"{door_desc} | Total E2E Latency={e2e_latency_ms}ms"
    )

    return {
        "episode_id": f"EQ_EP_{ep_id:04d}",
        "category": "MULTI_NODE_EARTHQUAKE",
        "subtype": tier,
        "is_earthquake": 1,
        "onset_time": iso_time,
        "magnitude": mag,
        "depth_km": round(depth_km, 1),
        "epicentral_dist_km": round(dist_km, 1),
        "p_to_s_lead_time_sec": p_to_s_lead_sec,
        "duration_sec": duration_s,
        "peak_pga": peak_pga,
        "peak_rms": peak_rms,
        "sta_lta": sta_lta,
        "dominant_freq_hz": freq_hz,
        "node_a_pga": node_a_pga,
        "node_b_pga": node_b_pga,
        "node_c_pga": node_c_pga,
        "nodes_consensus_count": nodes_count,
        "gas_raw": gas_raw,
        "gas_alert": 1 if has_gas_leak else 0,
        "occupancy_recent": 1 if occupancy_recent else 0,
        "solenoid_valve_status": solenoid_valve_status,
        "solenoid_valve_relay": solenoid_valve_relay,
        "solenoid_door_status": solenoid_door_status,
        "solenoid_door_relay": solenoid_door_relay,
        "valve_latency_ms": valve_latency_ms,
        "door_latency_ms": door_latency_ms,
        "e2e_latency_ms": e2e_latency_ms,
        "solenoid_log": solenoid_log
    }

def generate_disturbance_episode(dist_id, base_time):
    types = ["heavy_stomp", "table_desk_shake", "door_slam_shock", "floor_impact", "road_traffic_vibration"]
    stype = random.choice(types)

    if stype == "heavy_stomp":
        # Empirically measured from live node tests (Oct 16-17): stomps produce high PGA (0.4g - 3.5g+, occasionally 7.8g) at 16-32 Hz
        pga_base = random.choice([
            random.uniform(0.35, 1.80),
            random.uniform(0.80, 3.20),
            random.uniform(2.50, 7.80) if random.random() < 0.08 else random.uniform(0.50, 2.20)
        ])
        freq_hz = round(random.uniform(16.0, 32.0), 1)
        dur = round(random.uniform(0.2, 0.8), 1)
        sta_lta = round(random.uniform(6.0, 20.0), 2)
    elif stype == "table_desk_shake":
        pga_base = random.uniform(0.15, 1.20)
        freq_hz = round(random.uniform(3.0, 6.5), 1)
        dur = round(random.uniform(1.5, 6.5), 1)
        sta_lta = round(random.uniform(4.0, 15.0), 2)
    elif stype == "door_slam_shock":
        pga_base = random.uniform(0.25, 2.20)
        freq_hz = round(random.uniform(24.0, 52.0), 1)
        dur = round(random.uniform(0.15, 0.6), 1)
        sta_lta = round(random.uniform(5.0, 18.0), 2)
    elif stype == "floor_impact":
        pga_base = random.uniform(0.20, 2.80)
        freq_hz = round(random.uniform(28.0, 58.0), 1)
        dur = round(random.uniform(0.1, 0.5), 1)
        sta_lta = round(random.uniform(4.0, 16.0), 2)
    else: # road_traffic
        pga_base = random.uniform(0.025, 0.08)
        freq_hz = round(random.uniform(16.0, 32.0), 1)
        dur = round(random.uniform(5.0, 18.0), 1)
        sta_lta = round(random.uniform(2.5, 5.5), 2)

    # Localized to ONE node (Neighboring nodes remain at ambient baseline 0.003 - 0.012g as verified overnight)
    chosen_node = random.choice(["node_a", "node_b", "node_c"])
    node_a_pga = round(pga_base if chosen_node == "node_a" else random.uniform(0.003, 0.012), 5)
    node_b_pga = round(pga_base if chosen_node == "node_b" else random.uniform(0.003, 0.012), 5)
    node_c_pga = round(pga_base if chosen_node == "node_c" else random.uniform(0.003, 0.012), 5)
    peak_pga = max(node_a_pga, node_b_pga, node_c_pga)
    # Impulsive transient shocks have very low RMS energy relative to spike PGA
    peak_rms = round(peak_pga * random.uniform(0.12, 0.28), 5)

    onset_time = base_time + timedelta(seconds=1000 * 35 + dist_id * 20)
    iso_time = onset_time.strftime("%Y-%m-%d %H:%M:%S+00")

    solenoid_log = (
        f"[FILTER][REJECTED] {stype.replace('_', ' ').title()} (PGA={peak_pga:.4f}g, Freq={freq_hz:.1f}Hz) | "
        f"Consensus Check: FAILED (Single-node only) | Solenoid Actuators Safe (Valve OPEN, Door LOCKED)"
    )

    return {
        "episode_id": f"DISTURB_EP_{dist_id:04d}",
        "category": "LOCAL_DISTURBANCE",
        "subtype": stype,
        "is_earthquake": 0,
        "onset_time": iso_time,
        "magnitude": 0.0,
        "depth_km": 0.0,
        "epicentral_dist_km": 0.0,
        "p_to_s_lead_time_sec": 0.0,
        "duration_sec": dur,
        "peak_pga": peak_pga,
        "peak_rms": peak_rms,
        "sta_lta": sta_lta,
        "dominant_freq_hz": freq_hz,
        "node_a_pga": node_a_pga,
        "node_b_pga": node_b_pga,
        "node_c_pga": node_c_pga,
        "nodes_consensus_count": 1,
        "gas_raw": random.randint(320, 480),
        "gas_alert": 0,
        "occupancy_recent": 1 if random.random() < 0.65 else 0,
        "solenoid_valve_status": "ENABLED",
        "solenoid_valve_relay": 1,
        "solenoid_door_status": "LOCKED",
        "solenoid_door_relay": 0,
        "valve_latency_ms": 0,
        "door_latency_ms": 0,
        "e2e_latency_ms": 0,
        "solenoid_log": solenoid_log
    }

def main():
    print("=" * 75)
    print("  LINDU-EEW: Generating 1,000 Earthquake Episodes Dataset")
    print("=" * 75)

    base_time = datetime(2026, 10, 1, 0, 0, 0, tzinfo=timezone.utc)
    episodes = []

    # 1. Generate exactly 1,000 true earthquake episodes
    for i in range(1, 1001):
        episodes.append(generate_earthquake_episode(i, base_time))
    print(f"[OK] Generated exactly 1,000 True Earthquake Episodes.")

    # 2. Generate 500 control disturbance episodes for negative training
    for j in range(1, 501):
        episodes.append(generate_disturbance_episode(j, base_time))
    print(f"[OK] Generated 500 Control Disturbance Episodes (Stomps, Shakes, Door Slams).")

    # Shuffle dataset
    random.shuffle(episodes)

    # Export CSV
    headers = list(episodes[0].keys())
    with open(CATALOG_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(episodes)
    print(f"[OK] Exported Catalog CSV: {CATALOG_CSV} ({len(episodes)} total episodes)")

    # Export JSON
    with open(CATALOG_JSON, "w", encoding="utf-8") as f:
        json.dump(episodes, f, indent=2)
    print(f"[OK] Exported Catalog JSON: {CATALOG_JSON}")

    # Summary
    eq_eps = [e for e in episodes if e["is_earthquake"] == 1]
    avg_lead = sum(e["p_to_s_lead_time_sec"] for e in eq_eps) / len(eq_eps)
    max_pga = max(e["peak_pga"] for e in eq_eps)

    print("\n--- 1,000 Earthquake Episodes Summary ---")
    print(f"  • Total Earthquake Episodes:     1,000 episodes")
    print(f"  • Control Disturbance Episodes:    500 episodes")
    print(f"  • Combined Training Episodes:    1,500 episodes")
    print(f"  • Average P-to-S Lead Time:       {avg_lead:.2f} seconds")
    print(f"  • Maximum Ground Acceleration:    {max_pga:.4f} g")

    print("\n1,000 Earthquake Episodes Dataset generated successfully.")

if __name__ == "__main__":
    main()
