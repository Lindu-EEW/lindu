#!/usr/bin/env python3
"""
Lindu-EEW: Historical Database Feature Extractor & Preprocessor for AI Research
Transforms 30,228+ continuous historical telemetry records into windowed feature vectors
suitable for machine learning (1D-CNN, LSTM, Random Forest, Isolation Forest).
"""

import csv
import json
import math
import os
from datetime import datetime

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(OUTPUT_DIR, "historical_db_telemetry_29k.csv")
OUTPUT_FEATURES_CSV = os.path.join(OUTPUT_DIR, "ai_historical_features.csv")
OUTPUT_SUMMARY_JSON = os.path.join(OUTPUT_DIR, "historical_ai_summary.json")

def parse_iso(ts_str):
    try:
        # Handles various ISO formats with or without timezone
        clean_ts = ts_str.replace("Z", "+00:00")
        if "+" in clean_ts:
            base, offset = clean_ts.split("+")
            if "." in base:
                dt = datetime.strptime(base, "%Y-%m-%d %H:%M:%S.%f")
            else:
                dt = datetime.strptime(base, "%Y-%m-%d %H:%M:%S")
            return dt.timestamp()
        else:
            return datetime.strptime(ts_str[:19], "%Y-%m-%d %H:%M:%S").timestamp()
    except Exception:
        return 0.0

def process_historical_data(window_size=10):
    print("=" * 70)
    print("  LINDU-EEW: Processing 30,000+ Historical DB Records for AI Research")
    print("=" * 70)

    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Loaded {len(rows)} raw telemetry records from TimescaleDB.")

    # Group by node_id
    node_records = {}
    for r in rows:
        nid = r["node_id"]
        if nid not in node_records:
            node_records[nid] = []
        node_records[nid].append(r)

    processed_windows = []
    window_id = 1

    for nid, records in node_records.items():
        print(f"Processing node {nid} ({len(records)} records)...")
        # Step through records in non-overlapping windows of window_size
        for i in range(0, len(records) - window_size + 1, window_size):
            chunk = records[i:i + window_size]

            pgas = [float(c["pga"]) for c in chunk if c["pga"]]
            rmss = [float(c["rms"]) for c in chunk if c["rms"]]
            axs = [float(c["accel_x"]) for c in chunk if c["accel_x"]]
            ays = [float(c["accel_y"]) for c in chunk if c["accel_y"]]
            azs = [float(c["accel_z"]) for c in chunk if c["accel_z"]]
            gas_raws = [int(c["gas_raw"]) for c in chunk if c["gas_raw"]]
            has_gas_alert = any(c["gas_alert"] == "t" for c in chunk)
            valve_states = [c["valve_status"] for c in chunk if c["valve_status"]]

            if not pgas:
                continue

            max_pga = max(pgas)
            avg_pga = sum(pgas) / len(pgas)
            max_rms = max(rmss) if rmss else 0.0
            avg_rms = sum(rmss) / len(rmss) if rmss else 0.0

            # Acceleration variances across 3 axes
            mean_ax = sum(axs) / len(axs) if axs else 0.0
            mean_ay = sum(ays) / len(ays) if ays else 0.0
            mean_az = sum(azs) / len(azs) if azs else 0.0

            var_ax = sum((a - mean_ax) ** 2 for a in axs) / len(axs) if axs else 0.0
            var_ay = sum((a - mean_ay) ** 2 for a in ays) / len(ays) if ays else 0.0
            var_az = sum((a - mean_az) ** 2 for a in azs) / len(azs) if azs else 0.0
            total_kinetic_variance = var_ax + var_ay + var_az

            avg_gas = sum(gas_raws) / len(gas_raws) if gas_raws else 0
            is_valve_disabled = "DISABLED" in valve_states

            # Determine Class Label for Supervised / Semi-supervised Learning:
            # 1. SHOCK_ALERT: max_pga > 0.12g or (max_pga > 0.05g and kinetic variance > 0.05)
            # 2. GAS_LEAK: has_gas_alert or avg_gas > 2000
            # 3. BASELINE_NORMAL: calm environmental baseline
            if max_pga > 0.12 or (max_pga > 0.05 and total_kinetic_variance > 0.05):
                label = "SHOCK_VIBRATION"
                is_anomaly = 1
            elif has_gas_alert or avg_gas > 2000:
                label = "GAS_HAZARD"
                is_anomaly = 1
            else:
                label = "NORMAL_BASELINE"
                is_anomaly = 0

            processed_windows.append({
                "window_id": window_id,
                "node_id": nid,
                "start_time": chunk[0]["time"],
                "end_time": chunk[-1]["time"],
                "window_size": len(chunk),
                "max_pga": round(max_pga, 5),
                "avg_pga": round(avg_pga, 5),
                "max_rms": round(max_rms, 5),
                "avg_rms": round(avg_rms, 5),
                "mean_ax": round(mean_ax, 4),
                "mean_ay": round(mean_ay, 4),
                "mean_az": round(mean_az, 4),
                "var_ax": round(var_ax, 4),
                "var_ay": round(var_ay, 4),
                "var_az": round(var_az, 4),
                "total_kinetic_variance": round(total_kinetic_variance, 4),
                "avg_gas_raw": round(avg_gas, 1),
                "has_gas_alert": 1 if has_gas_alert else 0,
                "valve_status": "DISABLED" if is_valve_disabled else "ENABLED",
                "label": label,
                "is_anomaly": is_anomaly
            })
            window_id += 1

    # Write processed features CSV
    headers = list(processed_windows[0].keys())
    with open(OUTPUT_FEATURES_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(processed_windows)
    print(f"\n[OK] Generated {len(processed_windows)} feature windows: {OUTPUT_FEATURES_CSV}")

    # Class distribution
    dist = {}
    for w in processed_windows:
        dist[w["label"]] = dist.get(w["label"], 0) + 1

    print("\n--- Feature Window Class Distribution ---")
    for l, c in dist.items():
        print(f"  • {l:20s}: {c:5d} windows ({c * 100.0 / len(processed_windows):.1f}%)")

    summary = {
        "total_telemetry_records": len(rows),
        "total_feature_windows": len(processed_windows),
        "window_duration_samples": window_size,
        "class_distribution": dist,
        "nodes": list(node_records.keys())
    }
    with open(OUTPUT_SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"[OK] Summary metadata exported: {OUTPUT_SUMMARY_JSON}")

if __name__ == "__main__":
    process_historical_data()
