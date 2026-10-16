#!/usr/bin/env python3
"""
Lindu-EEW: Earthquake Early Warning System - Scalable Dataset & Actuator Generator
Generates physically calibrated seismic telemetry with solenoid actuation logs.

Modes:
1. Event Mode (--mode events):
   - Generates N earthquake/disturbances event summaries with solenoid logs.
2. Continuous Time-Series Mode (--mode timeseries):
   - Generates second-by-second (1 Hz / 10 Hz) continuous telemetry streaming across
     all 3 nodes (pre-quake ambient -> P-wave -> S-wave peak -> coda decay -> calm).

Supports any target sample size: 1,000, 5,000, 10,000, 50,000+
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
    {"node_id": "node_acbd13f9", "role": "sensor_actuator", "lat": 35.5402, "lon": 139.5178},
    {"node_id": "node_2418399e", "role": "sensor_actuator", "lat": 35.5406, "lon": 139.5182},
    {"node_id": "node_3c096f0c", "role": "sensor_only",     "lat": 35.5398, "lon": 139.5174}
]

def generate_earthquake_event(sample_id, base_time, total_samples):
    g = 9.80665
    node = random.choice(NODES)
    node_id = node["node_id"]

    # Proportional tier distribution across any sample size N
    frac = sample_id / float(total_samples)
    if frac <= 0.30:
        tier = "minor_earthquake"
        magnitude = round(random.uniform(3.0, 4.4), 1)
        pga = random.uniform(0.025, 0.075)
        sta_lta = random.uniform(3.10, 5.80)
        freq_hz = random.uniform(1.8, 6.5)
        duration_s = random.uniform(8.0, 22.0)
        p_to_s_ratio = random.uniform(0.35, 0.65)
        mmi = random.choice(["III", "IV"])
    elif frac <= 0.70:
        tier = "moderate_earthquake"
        magnitude = round(random.uniform(4.5, 5.9), 1)
        pga = random.uniform(0.075, 0.220)
        sta_lta = random.uniform(5.50, 14.50)
        freq_hz = random.uniform(1.2, 5.0)
        duration_s = random.uniform(18.0, 45.0)
        p_to_s_ratio = random.uniform(0.40, 0.70)
        mmi = random.choice(["V", "VI"])
    elif frac <= 0.90:
        tier = "strong_earthquake"
        magnitude = round(random.uniform(6.0, 6.9), 1)
        pga = random.uniform(0.220, 0.550)
        sta_lta = random.uniform(12.0, 24.0)
        freq_hz = random.uniform(0.9, 3.8)
        duration_s = random.uniform(35.0, 65.0)
        p_to_s_ratio = random.uniform(0.45, 0.75)
        mmi = random.choice(["VII", "VIII"])
    else:
        tier = "severe_earthquake"
        magnitude = round(random.uniform(7.0, 7.8), 1)
        pga = random.uniform(0.550, 0.920)
        sta_lta = random.uniform(22.0, 36.0)
        freq_hz = random.uniform(0.6, 2.8)
        duration_s = random.uniform(50.0, 95.0)
        p_to_s_ratio = random.uniform(0.50, 0.85)
        mmi = "IX"

    ax_frac = random.uniform(0.40, 0.70)
    az_frac = random.uniform(0.25, 0.45)
    ay_frac = math.sqrt(max(0.01, 1.0 - (ax_frac**2 + az_frac**2) / 2.0))

    ax = (pga * g * ax_frac) * random.choice([-1, 1]) + random.gauss(0, 0.015)
    ay = (pga * g * ay_frac) * random.choice([-1, 1]) + random.gauss(0, 0.015)
    az = (pga * g * az_frac) * random.choice([-1, 1]) + random.gauss(0, 0.015)
    rms = pga * random.uniform(0.45, 0.68)

    gas_leak_prob = 0.03 if tier == "minor_earthquake" else (0.15 if tier == "moderate_earthquake" else 0.32)
    has_gas_leak = random.random() < gas_leak_prob
    if has_gas_leak:
        gas_raw = random.randint(2200, 3850)
        gas_alert = True
    else:
        gas_raw = random.randint(280, 520)
        gas_alert = False

    occupancy_recent = random.random() < 0.75
    motion_detected = occupancy_recent if random.random() < 0.60 else False

    # Solenoid Valve: Cut power (RELAY_OFF, 0)
    solenoid_valve_status = "DISABLED"
    solenoid_valve_relay = 0
    valve_latency_ms = random.randint(118, 178)

    # Solenoid Door: Unlock (RELAY_ON, 1) only if occupants present
    if occupancy_recent:
        solenoid_door_status = "UNLOCKED"
        solenoid_door_relay = 1
        door_latency_ms = random.randint(132, 215)
    else:
        solenoid_door_status = "LOCKED"
        solenoid_door_relay = 0
        door_latency_ms = 0

    e2e_latency_ms = max(valve_latency_ms, door_latency_ms) + random.randint(140, 260)
    sample_time = base_time + timedelta(seconds=sample_id * 15)
    iso_timestamp = sample_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    door_log_txt = (
        f"Door UNLOCKED in {door_latency_ms}ms (RELAY_ON, Occupancy=DETECTED)"
        if solenoid_door_status == "UNLOCKED"
        else "Door KEPT LOCKED (RELAY_OFF, Occupancy=NONE)"
    )
    gas_log_txt = f"Gas Leak DETECTED ({gas_raw} ppm)" if gas_alert else "Gas Normal"

    solenoid_log = (
        f"[ACTUATOR][SOLENOID] Quake M{magnitude} ({tier.replace('_', ' ').title()}) | "
        f"PGA={pga:.4f}g | STA/LTA={sta_lta:.2f} | "
        f"Gas Solenoid Valve SHUTOFF in {valve_latency_ms}ms (RELAY_OFF, {gas_log_txt}) | "
        f"Solenoid {door_log_txt} | "
        f"E2E Latency={e2e_latency_ms}ms"
    )

    return {
        "sample_id": sample_id,
        "timestamp": iso_timestamp,
        "node_id": node_id,
        "event_type": tier,
        "magnitude": magnitude,
        "intensity_mmi": mmi,
        "pga": round(pga, 5),
        "sta_lta": round(sta_lta, 3),
        "freq_hz": round(freq_hz, 1),
        "rms": round(rms, 5),
        "ax": round(ax, 4),
        "ay": round(ay, 4),
        "az": round(az, 4),
        "duration_s": round(duration_s, 2),
        "p_to_s_ratio": round(p_to_s_ratio, 3),
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
        "solenoid_log": solenoid_log,
        "is_earthquake": 1
    }

def generate_continuous_timeseries(num_events=50):
    """
    Generates continuous streaming second-by-second sensor telemetry across all 3 nodes.
    Each event has pre-quake ambient -> P-wave arrival -> S-wave peak -> Coda decay -> calm.
    Outputs tens of thousands of continuous time-series rows for TimescaleDB stress testing.
    """
    g = 9.80665
    t_curr = datetime(2026, 10, 14, 0, 0, 0, tzinfo=timezone.utc)
    rows = []
    row_id = 1

    for ev_id in range(1, num_events + 1):
        # 1. Pre-event calm noise (10 seconds)
        for sec in range(10):
            t_curr += timedelta(seconds=1)
            for node in NODES:
                pga = random.uniform(0.003, 0.012)
                rows.append({
                    "row_id": row_id,
                    "timestamp": t_curr.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                    "node_id": node["node_id"],
                    "phase": "ambient_pre",
                    "pga": round(pga, 5),
                    "sta_lta": round(random.uniform(0.9, 1.4), 2),
                    "freq_hz": round(random.uniform(1.0, 3.5), 1),
                    "rms": round(pga * 0.7, 5),
                    "ax": round(random.gauss(0, 0.01), 4),
                    "ay": round(random.gauss(0, 0.01), 4),
                    "az": round(random.gauss(0, 0.01), 4),
                    "gas_raw": random.randint(300, 450),
                    "gas_alert": False,
                    "valve_status": "ENABLED",
                    "door_status": "LOCKED",
                    "solenoid_log": "Normal baseline monitoring"
                })
                row_id += 1

        # 2. Quake parameters
        mag = round(random.uniform(3.5, 7.2), 1)
        peak_pga = 0.04 * (10 ** (0.28 * (mag - 3.0)))
        quake_duration = random.randint(15, 45)

        # 3. Active quake shaking per second
        for sec in range(quake_duration):
            t_curr += timedelta(seconds=1)
            progress = sec / float(quake_duration)
            if progress < 0.20:
                envelope = progress / 0.20 * 0.35 # P-wave arrival
                phase = "P_wave"
            elif progress < 0.45:
                envelope = 0.35 + (progress - 0.20) / 0.25 * 0.65 # S-wave peak
                phase = "S_wave_peak"
            else:
                envelope = math.exp(-3.5 * (progress - 0.45)) # Coda decay
                phase = "coda_decay"

            for node in NODES:
                curr_pga = max(0.008, peak_pga * envelope + random.gauss(0, 0.01))
                is_active = curr_pga > 0.03
                valve_st = "DISABLED" if is_active else "ENABLED"
                door_st = "UNLOCKED" if is_active else "LOCKED"
                log_txt = (
                    f"[ACTUATOR] S-Wave Active (PGA={curr_pga:.4f}g) -> Solenoid Valve CLOSED, Door UNLOCKED"
                    if is_active else "Coda decaying"
                )
                rows.append({
                    "row_id": row_id,
                    "timestamp": t_curr.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                    "node_id": node["node_id"],
                    "phase": phase,
                    "pga": round(curr_pga, 5),
                    "sta_lta": round(max(1.0, (curr_pga / 0.012) * 2.5), 2),
                    "freq_hz": round(random.uniform(1.2, 4.8), 1),
                    "rms": round(curr_pga * 0.55, 5),
                    "ax": round((curr_pga * g * 0.6) * random.choice([-1, 1]), 4),
                    "ay": round((curr_pga * g * 0.5) * random.choice([-1, 1]), 4),
                    "az": round((curr_pga * g * 0.4) * random.choice([-1, 1]), 4),
                    "gas_raw": random.randint(350, 520),
                    "gas_alert": False,
                    "valve_status": valve_st,
                    "door_status": door_st,
                    "solenoid_log": log_txt
                })
                row_id += 1

    return rows

def main():
    parser = argparse.ArgumentParser(description="Lindu-EEW Dataset Generator")
    parser.add_argument("--count", "-n", type=int, default=1000,
                        help="Number of samples to generate (e.g. 1000, 5000, 10000)")
    parser.add_argument("--mode", choices=["events", "timeseries"], default="events",
                        help="events (summary samples) or timeseries (second-by-second streaming)")
    args = parser.parse_args()

    print("=" * 70)
    print(f"  LINDU-EEW: Dataset Generator (Mode={args.mode}, Count={args.count})")
    print("=" * 70)

    base_time = datetime(2026, 10, 14, 0, 0, 0, tzinfo=timezone.utc)

    if args.mode == "events":
        csv_filename = f"earthquake_{args.count}_with_solenoid_logs.csv"
        json_filename = f"earthquake_{args.count}_with_solenoid_logs.json"
        csv_path = os.path.join(OUTPUT_DIR, csv_filename)
        json_path = os.path.join(OUTPUT_DIR, json_filename)

        samples = [generate_earthquake_event(i, base_time, args.count) for i in range(1, args.count + 1)]

        headers = list(samples[0].keys())
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(samples)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(samples, f, indent=2)

        print(f"[OK] Generated {len(samples)} Earthquake Event Samples with Solenoid Logs:")
        print(f"     CSV:  {csv_path}")
        print(f"     JSON: {json_path}")

    else: # timeseries
        num_events = max(10, args.count // 100)
        csv_filename = f"continuous_telemetry_timeseries_{args.count}rows.csv"
        csv_path = os.path.join(OUTPUT_DIR, csv_filename)

        print(f"Generating continuous multi-node time-series across {num_events} seismic events...")
        rows = generate_continuous_timeseries(num_events=num_events)
        # trim to count if requested
        if len(rows) > args.count:
            rows = rows[:args.count]

        headers = list(rows[0].keys())
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

        print(f"[OK] Generated {len(rows)} Continuous Time-Series Rows across 3 nodes:")
        print(f"     CSV: {csv_path}")

    print("\nGeneration completed successfully.")

if __name__ == "__main__":
    main()
