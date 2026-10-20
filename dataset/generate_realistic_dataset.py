#!/usr/bin/env python3
"""
Lindu-EEW: Realistic Multi-Event & Solenoid Actuation Dataset Generator
Generates realistic physical scenarios:
- Real Earthquakes (Minor, Moderate, Strong, Severe, Megathrust)
- Foot Stomps (Human jumping/heavy stomping near node)
- Manual Table/Post Shakes (Manual hand agitation/bump)
- Door Slams (Structural impact shock from slamming door)
- Dropped Objects (Heavy object impact on floor)
- Passing Trucks (Road traffic & construction vibration)
- Ambient Noise (Quiet baseline & sensor thermal jitter)

Includes:
- Multi-node spatial consensus (Node A, Node B, Node C)
- Realistic IMU physics (PGA, STA/LTA, Frequency Hz, RMS, 3-axis dyn)
- Solenoid Valve & Door Lock hardware relay states and latencies
- Formatted syslog messages matching tb_node_logs
"""

import argparse
import csv
import json
import math
import os
import random
from datetime import datetime, timezone, timedelta

SEED = 42
random.seed(SEED)

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

NODES = [
    {"node_id": "node_acbd13f9", "name": "Node A (Living Room)", "role": "sensor_actuator", "lat": 35.5402, "lon": 139.5178},
    {"node_id": "node_2418399e", "name": "Node B (Kitchen/Gas)",  "role": "sensor_actuator", "lat": 35.5406, "lon": 139.5182},
    {"node_id": "node_3c096f0c", "name": "Node C (Hallway)",      "role": "sensor_only",     "lat": 35.5398, "lon": 139.5174}
]

EVENT_PROFILES = [
    ("earthquake", 0.50),     # 50% Real Earthquakes (Minor, Moderate, Strong, Severe)
    ("stomp", 0.12),          # 12% Human foot stomps / jumping
    ("manual_shake", 0.10),   # 10% Manual table / mounting post shaking
    ("door_slam", 0.10),      # 10% Heavy door slam shocks
    ("dropped_object", 0.06), #  6% Dropped pan / tool / heavy item
    ("passing_truck", 0.06),  #  6% Heavy road traffic / truck vibration
    ("ambient_noise", 0.06)   #  6% Normal quiet room baseline
]

def generate_sample(sample_id, event_type, base_time):
    g = 9.80665
    target_node = random.choice(NODES)
    node_id = target_node["node_id"]
    timestamp = base_time + timedelta(seconds=sample_id * 10)
    iso_time = timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    # Environmental & Occupant defaults
    gas_raw = random.randint(300, 480)
    gas_alert = False
    occupancy_recent = random.random() < 0.70
    motion_detected = occupancy_recent and (random.random() < 0.55)

    if event_type == "earthquake":
        # Sub-tier distribution
        sub_r = random.random()
        if sub_r < 0.35:
            subtype = "minor_earthquake"
            mag = round(random.uniform(3.0, 4.4), 1)
            pga = random.uniform(0.025, 0.075)
            sta_lta = random.uniform(3.1, 5.8)
            freq_hz = random.uniform(1.8, 6.5)
            duration_s = random.uniform(10.0, 24.0)
            mmi = random.choice(["III", "IV"])
        elif sub_r < 0.75:
            subtype = "moderate_earthquake"
            mag = round(random.uniform(4.5, 5.9), 1)
            pga = random.uniform(0.075, 0.220)
            sta_lta = random.uniform(5.5, 14.5)
            freq_hz = random.uniform(1.2, 5.0)
            duration_s = random.uniform(18.0, 45.0)
            mmi = random.choice(["V", "VI"])
        elif sub_r < 0.93:
            subtype = "strong_earthquake"
            mag = round(random.uniform(6.0, 6.9), 1)
            pga = random.uniform(0.220, 0.550)
            sta_lta = random.uniform(12.0, 24.0)
            freq_hz = random.uniform(0.9, 3.8)
            duration_s = random.uniform(35.0, 65.0)
            mmi = random.choice(["VII", "VIII"])
        else:
            subtype = "severe_earthquake"
            mag = round(random.uniform(7.0, 7.8), 1)
            pga = random.uniform(0.550, 0.920)
            sta_lta = random.uniform(22.0, 36.0)
            freq_hz = random.uniform(0.6, 2.5)
            duration_s = random.uniform(55.0, 95.0)
            mmi = "IX"

        # Tectonic waves spread across ALL nodes (Spatial Consensus REACHED)
        nodes_triggered = random.choice([2, 3]) if pga < 0.04 else 3
        consensus_reached = True
        node_a_pga = pga * random.uniform(0.88, 1.12)
        node_b_pga = pga * random.uniform(0.85, 1.15)
        node_c_pga = pga * random.uniform(0.82, 1.10)

        # Multiaxial ground acceleration
        ax = (pga * g * random.uniform(0.4, 0.7)) * random.choice([-1, 1])
        ay = (pga * g * random.uniform(0.4, 0.7)) * random.choice([-1, 1])
        az = (pga * g * random.uniform(0.25, 0.45)) * random.choice([-1, 1])
        rms = pga * random.uniform(0.45, 0.68)

        # Gas leak secondary hazard simulation
        leak_chance = 0.05 if mag < 5.0 else (0.18 if mag < 6.5 else 0.35)
        if random.random() < leak_chance:
            gas_raw = random.randint(2200, 3950)
            gas_alert = True

        # Solenoid Actuators FIRE
        solenoid_valve_status = "DISABLED"
        solenoid_valve_relay = 0 # RELAY_OFF: cuts power to shut NC valve
        valve_latency_ms = random.randint(118, 175)

        if occupancy_recent:
            solenoid_door_status = "UNLOCKED"
            solenoid_door_relay = 1 # RELAY_ON: energizes solenoid to retract latch
            door_latency_ms = random.randint(135, 210)
            door_desc = f"Door UNLOCKED in {door_latency_ms}ms (Occupants detected for egress)"
        else:
            solenoid_door_status = "LOCKED"
            solenoid_door_relay = 0
            door_latency_ms = 0
            door_desc = "Door KEPT LOCKED (No occupants, security preserved)"

        e2e_latency_ms = max(valve_latency_ms, door_latency_ms) + random.randint(130, 240)
        gas_txt = f"Gas Leak DETECTED ({gas_raw} ppm)" if gas_alert else "Gas Normal"

        solenoid_log = (
            f"[ALARM][SOLENOID] Quake M{mag} confirmed by {nodes_triggered}-Node Consensus | "
            f"PGA={pga:.4f}g (Low-Freq={freq_hz:.1f}Hz) | "
            f"Solenoid Gas Valve SHUTOFF in {valve_latency_ms}ms (RELAY_OFF, {gas_txt}) | "
            f"{door_desc} | E2E Latency={e2e_latency_ms}ms"
        )
        is_earthquake = 1

    elif event_type == "stomp":
        subtype = "heavy_stomp"
        mag = 0.0
        mmi = "NONE"
        # Localized vertical impact
        pga = random.uniform(0.120, 0.340)
        sta_lta = random.uniform(3.8, 8.5)
        freq_hz = random.uniform(18.0, 36.0) # High frequency!
        duration_s = random.uniform(0.3, 1.2) # Short pulse!

        # Localized to ONE node only (No Consensus!)
        nodes_triggered = 1
        consensus_reached = False
        node_a_pga = pga if node_id == "node_acbd13f9" else random.uniform(0.0010, 0.0035)
        node_b_pga = pga if node_id == "node_2418399e" else random.uniform(0.0010, 0.0035)
        node_c_pga = pga if node_id == "node_3c096f0c" else random.uniform(0.0010, 0.0035)

        # Dominant vertical Z axis
        ax = random.gauss(0, 0.03)
        ay = random.gauss(0, 0.03)
        az = (pga * g * random.uniform(0.85, 0.98)) * random.choice([-1, 1])
        rms = pga * random.uniform(0.20, 0.35)

        # Actuators do NOT trip (False alarm rejected)
        solenoid_valve_status = "ENABLED"
        solenoid_valve_relay = 1 # Normal open
        solenoid_door_status = "LOCKED"
        solenoid_door_relay = 0
        valve_latency_ms = 0
        door_latency_ms = 0
        e2e_latency_ms = 0

        solenoid_log = (
            f"[FILTER][REJECTED] Heavy Foot Stomp on {target_node['name']} (PGA={pga:.4f}g, Freq={freq_hz:.1f}Hz) | "
            f"Spatial Consensus: REJECTED (Single-node only, neighboring nodes calm) | "
            f"Solenoid Gas Valve kept OPEN, Door kept LOCKED (False Alarm Prevented)"
        )
        is_earthquake = 0

    elif event_type == "manual_shake":
        subtype = "table_desk_shake"
        mag = 0.0
        mmi = "NONE"
        # High acceleration from manual human shaking
        pga = random.uniform(0.150, 0.950)
        sta_lta = random.uniform(4.0, 11.0)
        freq_hz = random.uniform(2.5, 6.0) # Can match arm speed, but single-node only!
        duration_s = random.uniform(1.5, 7.5)

        # Localized to ONE desk/post
        nodes_triggered = 1
        consensus_reached = False
        node_a_pga = pga if node_id == "node_acbd13f9" else random.uniform(0.0010, 0.0035)
        node_b_pga = pga if node_id == "node_2418399e" else random.uniform(0.0010, 0.0035)
        node_c_pga = pga if node_id == "node_3c096f0c" else random.uniform(0.0010, 0.0035)

        # Erratic manual shaking, heavy jerk
        ax = (pga * g * random.uniform(0.7, 0.95)) * random.choice([-1, 1])
        ay = (pga * g * random.uniform(0.2, 0.4)) * random.choice([-1, 1])
        az = (pga * g * random.uniform(0.1, 0.3)) * random.choice([-1, 1])
        rms = pga * random.uniform(0.35, 0.50)

        solenoid_valve_status = "ENABLED"
        solenoid_valve_relay = 1
        solenoid_door_status = "LOCKED"
        solenoid_door_relay = 0
        valve_latency_ms = 0
        door_latency_ms = 0
        e2e_latency_ms = 0

        solenoid_log = (
            f"[FILTER][REJECTED] Manual Desk Shake on {target_node['name']} (PGA={pga:.4f}g) | "
            f"Consensus Check: FAILED (Other nodes silent: Node A={node_a_pga:.3f}g, Node B={node_b_pga:.3f}g) | "
            f"Actuators SAFE: Solenoid Valve OPEN, Door LOCKED"
        )
        is_earthquake = 0

    elif event_type == "door_slam":
        subtype = "door_slam_shock"
        mag = 0.0
        mmi = "NONE"
        pga = random.uniform(0.110, 0.380)
        sta_lta = random.uniform(3.5, 9.8)
        freq_hz = random.uniform(26.0, 52.0) # High frequency wall vibration!
        duration_s = random.uniform(0.2, 0.7) # Very brief!

        nodes_triggered = 1
        consensus_reached = False
        node_a_pga = pga if node_id == "node_acbd13f9" else random.uniform(0.0010, 0.0035)
        node_b_pga = pga if node_id == "node_2418399e" else random.uniform(0.0010, 0.0035)
        node_c_pga = pga if node_id == "node_3c096f0c" else random.uniform(0.0010, 0.0035)

        ax = (pga * g * random.uniform(0.8, 0.98)) * random.choice([-1, 1])
        ay = (pga * g * random.uniform(0.1, 0.3)) * random.choice([-1, 1])
        az = (pga * g * random.uniform(0.1, 0.25)) * random.choice([-1, 1])
        rms = pga * random.uniform(0.16, 0.28)

        solenoid_valve_status = "ENABLED"
        solenoid_valve_relay = 1
        solenoid_door_status = "LOCKED"
        solenoid_door_relay = 0
        valve_latency_ms = 0
        door_latency_ms = 0
        e2e_latency_ms = 0

        solenoid_log = (
            f"[FILTER][REJECTED] Door Slam on {target_node['name']} (PGA={pga:.4f}g, High-Freq={freq_hz:.1f}Hz) | "
            f"Spectral & Consensus Check: Structural Transient Rejected | "
            f"Solenoids unaffected (Valve OPEN, Door LOCKED)"
        )
        is_earthquake = 0

    elif event_type == "dropped_object":
        subtype = "floor_impact"
        mag = 0.0
        mmi = "NONE"
        pga = random.uniform(0.080, 0.250)
        sta_lta = random.uniform(2.8, 6.5)
        freq_hz = random.uniform(32.0, 58.0)
        duration_s = random.uniform(0.15, 0.5)

        nodes_triggered = 1
        consensus_reached = False
        node_a_pga = pga if node_id == "node_acbd13f9" else random.uniform(0.0010, 0.0035)
        node_b_pga = pga if node_id == "node_2418399e" else random.uniform(0.0010, 0.0035)
        node_c_pga = pga if node_id == "node_3c096f0c" else random.uniform(0.0010, 0.0035)

        ax = random.gauss(0, 0.04)
        ay = random.gauss(0, 0.04)
        az = (pga * g * random.uniform(0.8, 0.95)) * random.choice([-1, 1])
        rms = pga * random.uniform(0.14, 0.25)

        solenoid_valve_status = "ENABLED"
        solenoid_valve_relay = 1
        solenoid_door_status = "LOCKED"
        solenoid_door_relay = 0
        valve_latency_ms = 0
        door_latency_ms = 0
        e2e_latency_ms = 0

        solenoid_log = (
            f"[FILTER][REJECTED] Dropped Object impact (PGA={pga:.4f}g, Freq={freq_hz:.1f}Hz) | "
            f"No dual-node correlation | Solenoids safe"
        )
        is_earthquake = 0

    elif event_type == "passing_truck":
        subtype = "road_traffic_vibration"
        mag = 0.0
        mmi = "NONE"
        pga = random.uniform(0.025, 0.080)
        sta_lta = random.uniform(1.8, 3.2)
        freq_hz = random.uniform(16.0, 32.0)
        duration_s = random.uniform(5.0, 18.0)

        nodes_triggered = random.choice([0, 1])
        consensus_reached = False
        node_a_pga = pga * random.uniform(0.7, 1.0)
        node_b_pga = pga * random.uniform(0.7, 1.0)
        node_c_pga = pga * random.uniform(0.7, 1.0)

        ax = (pga * g * random.uniform(0.4, 0.7)) * random.choice([-1, 1])
        ay = (pga * g * random.uniform(0.4, 0.7)) * random.choice([-1, 1])
        az = (pga * g * random.uniform(0.5, 0.8)) * random.choice([-1, 1])
        rms = pga * random.uniform(0.42, 0.60)

        solenoid_valve_status = "ENABLED"
        solenoid_valve_relay = 1
        solenoid_door_status = "LOCKED"
        solenoid_door_relay = 0
        valve_latency_ms = 0
        door_latency_ms = 0
        e2e_latency_ms = 0

        solenoid_log = (
            f"[MONITOR] Heavy Vehicle vibration (PGA={pga:.4f}g, Freq={freq_hz:.1f}Hz) | "
            f"STA/LTA < 3.5 trigger threshold | Normal continuous logging"
        )
        is_earthquake = 0

    else: # ambient_noise
        subtype = "sensor_ambient_drift"
        mag = 0.0
        mmi = "NONE"
        pga = random.uniform(0.0010, 0.0035)
        sta_lta = random.uniform(0.28, 0.65)
        freq_hz = random.uniform(18.0, 26.0)
        duration_s = random.uniform(5.0, 60.0)

        nodes_triggered = 0
        consensus_reached = False
        node_a_pga = random.uniform(0.0010, 0.0035)
        node_b_pga = random.uniform(0.0010, 0.0035)
        node_c_pga = random.uniform(0.0010, 0.0035)

        ax = random.gauss(0, 0.002)
        ay = random.gauss(0, 0.002)
        az = random.gauss(0, 0.003)
        rms = pga * random.uniform(0.60, 0.85)

        solenoid_valve_status = "ENABLED"
        solenoid_valve_relay = 1
        solenoid_door_status = "LOCKED"
        solenoid_door_relay = 0
        valve_latency_ms = 0
        door_latency_ms = 0
        e2e_latency_ms = 0

        solenoid_log = f"[MONITOR] Ambient calm baseline (PGA={pga:.4f}g) | Telemetry nominal"
        is_earthquake = 0

    return {
        "sample_id": sample_id,
        "timestamp": iso_time,
        "primary_node_id": node_id,
        "event_category": event_type,
        "subtype": subtype,
        "is_earthquake": is_earthquake,
        "magnitude": mag,
        "intensity_mmi": mmi,
        "pga": round(pga, 5),
        "node_a_pga": round(node_a_pga, 5),
        "node_b_pga": round(node_b_pga, 5),
        "node_c_pga": round(node_c_pga, 5),
        "nodes_triggered_count": nodes_triggered,
        "consensus_reached": consensus_reached,
        "sta_lta": round(sta_lta, 3),
        "freq_hz": round(freq_hz, 1),
        "rms": round(rms, 5),
        "ax": round(ax, 4),
        "ay": round(ay, 4),
        "az": round(az, 4),
        "duration_s": round(duration_s, 2),
        "gas_raw": gas_raw,
        "gas_alert": gas_alert,
        "motion_detected": motion_detected,
        "occupancy_recent": occupancy_recent,
        "solenoid_valve_status": solenoid_valve_status,
        "solenoid_valve_relay": solenoid_valve_relay,
        "solenoid_door_status": solenoid_door_status,
        "solenoid_door_relay": solenoid_door_relay,
        "valve_latency_ms": valve_latency_ms,
        "door_latency_ms": door_latency_ms,
        "e2e_latency_ms": e2e_latency_ms,
        "solenoid_log": solenoid_log
    }

def main():
    parser = argparse.ArgumentParser(description="Lindu Realistic Multi-Event Dataset Generator")
    parser.add_argument("--count", "-n", type=int, default=10000,
                        help="Number of samples to generate (default: 10000)")
    args = parser.parse_args()

    count = args.count
    print("=" * 75)
    print(f"  LINDU-EEW: Generating {count} Realistic Physical Samples")
    print("  (Earthquakes, Foot Stomps, Manual Shakes, Door Slams, Trucks, Noise)")
    print("=" * 75)

    base_time = datetime(2026, 10, 14, 0, 0, 0, tzinfo=timezone.utc)
    samples = []

    # Distribute event counts based on EVENT_PROFILES
    event_pool = []
    for etype, weight in EVENT_PROFILES:
        n_ev = int(round(weight * count))
        event_pool.extend([etype] * n_ev)

    # Pad or trim to exact count
    while len(event_pool) < count:
        event_pool.append("earthquake")
    if len(event_pool) > count:
        event_pool = event_pool[:count]

    random.shuffle(event_pool)

    for sid, etype in enumerate(event_pool, start=1):
        samples.append(generate_sample(sid, etype, base_time))

    # Summaries
    cat_counts = {}
    for s in samples:
        cat = s["event_category"]
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    print("\n--- Event Distribution ---")
    for cat, cnt in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  • {cat.replace('_', ' ').title():20s}: {cnt:5d} samples ({cnt*100.0/count:5.1f}%)")

    # Actuator Stats
    valve_shutoffs = sum(1 for s in samples if s["solenoid_valve_status"] == "DISABLED")
    door_unlocks = sum(1 for s in samples if s["solenoid_door_status"] == "UNLOCKED")
    door_locked_quakes = sum(1 for s in samples if s["is_earthquake"] == 1 and s["solenoid_door_status"] == "LOCKED")
    rejected_false_alarms = sum(1 for s in samples if s["is_earthquake"] == 0 and s["solenoid_valve_status"] == "ENABLED")

    print("\n--- Solenoid Actuator & Consensus Validation ---")
    print(f"  • Solenoid Gas Valves Shutoff (DISABLED): {valve_shutoffs:5d} ({valve_shutoffs*100.0/count:.1f}%)")
    print(f"  • Solenoid Doors UNLOCKED for Evacuation: {door_unlocks:5d} (Safe egress for occupied rooms)")
    print(f"  • Solenoid Doors Kept LOCKED during Quake: {door_locked_quakes:5d} (Anti-trespassing for empty rooms)")
    print(f"  • False Alarms Rejected (Stomp/Shake/Door): {rejected_false_alarms:5d} (100.0% of non-earthquake events safe)")

    # Export to CSV
    csv_file = os.path.join(OUTPUT_DIR, f"realistic_earthquake_and_disturbances_{count}.csv")
    json_file = os.path.join(OUTPUT_DIR, f"realistic_earthquake_and_disturbances_{count}.json")

    headers = list(samples[0].keys())
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(samples)
    print(f"\n[OK] CSV Exported:  {csv_file}")

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2)
    print(f"[OK] JSON Exported: {json_file}")

    # Also write a convenient symlink or default copy named realistic_dataset.csv
    default_csv = os.path.join(OUTPUT_DIR, "realistic_dataset.csv")
    with open(default_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(samples)
    print(f"[OK] Default Link:  {default_csv}")

    print("\nRealistic dataset generation completed successfully.")

if __name__ == "__main__":
    main()
