#!/usr/bin/env python3
"""
Lindu-EEW: Historical Database Feature Extractor & Preprocessor for AI Research (TimescaleDB Direct)
Transforms all 330,000+ continuous historical telemetry records into windowed feature vectors
suitable for machine learning (1D-CNN, LSTM, Random Forest, Isolation Forest).
"""

import csv
import json
import os
import sys
import psycopg2

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FEATURES_CSV = sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUTPUT_DIR, "ai_historical_features.csv")
OUTPUT_SUMMARY_JSON = sys.argv[2] if len(sys.argv) > 2 else os.path.join(OUTPUT_DIR, "historical_ai_summary.json")

DB_HOST = os.getenv("DB_HOST", "timescaledb")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "lindu_admin")
DB_PASS = os.getenv("DB_PASS", "supersecretpassword")
DB_NAME = os.getenv("DB_NAME", "lindudb")

def process_historical_data(window_size=10):
    print("=" * 70)
    print("  LINDU-EEW: Processing 330,000+ Historical DB Records for AI Research")
    print("=" * 70)

    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        dbname=DB_NAME
    )
    cur = conn.cursor()

    cur.execute("""
        SELECT time, node_id, pga, rms, accel_x, accel_y, accel_z, gas_raw, gas_alert, valve_status
        FROM sensor_telemetry
        ORDER BY node_id, time ASC;
    """)
    rows = cur.fetchall()
    print(f"Loaded {len(rows)} raw telemetry records directly from TimescaleDB.")

    # Group by node_id
    node_records = {}
    for r in rows:
        nid = r[1]
        if nid not in node_records:
            node_records[nid] = []
        node_records[nid].append({
            "time": r[0].strftime("%Y-%m-%d %H:%M:%S.%f") if r[0] else "",
            "node_id": r[1],
            "pga": r[2],
            "rms": r[3],
            "accel_x": r[4],
            "accel_y": r[5],
            "accel_z": r[6],
            "gas_raw": r[7],
            "gas_alert": r[8],
            "valve_status": r[9]
        })

    cur.close()
    conn.close()

    processed_windows = []
    window_id = 1

    for nid, records in node_records.items():
        print(f"Processing node {nid} ({len(records)} records)...")
        for i in range(0, len(records) - window_size + 1, window_size):
            chunk = records[i:i + window_size]

            pgas = [float(c["pga"]) for c in chunk if c["pga"] is not None]
            rmss = [float(c["rms"]) for c in chunk if c["rms"] is not None]
            axs = [float(c["accel_x"]) for c in chunk if c["accel_x"] is not None]
            ays = [float(c["accel_y"]) for c in chunk if c["accel_y"] is not None]
            azs = [float(c["accel_z"]) for c in chunk if c["accel_z"] is not None]
            gas_raws = [int(c["gas_raw"]) for c in chunk if c["gas_raw"] is not None]
            has_gas_alert = any(c["gas_alert"] is True for c in chunk)
            valve_states = [c["valve_status"] for c in chunk if c["valve_status"]]

            if not pgas:
                continue

            max_pga = max(pgas)
            avg_pga = sum(pgas) / len(pgas)
            max_rms = max(rmss) if rmss else 0.0
            avg_rms = sum(rmss) / len(rmss) if rmss else 0.0

            mean_ax = sum(axs) / len(axs) if axs else 0.0
            mean_ay = sum(ays) / len(ays) if ays else 0.0
            mean_az = sum(azs) / len(azs) if azs else 0.0

            var_ax = sum((a - mean_ax) ** 2 for a in axs) / len(axs) if axs else 0.0
            var_ay = sum((a - mean_ay) ** 2 for a in ays) / len(ays) if ays else 0.0
            var_az = sum((a - mean_az) ** 2 for a in azs) / len(azs) if azs else 0.0
            total_kinetic_variance = var_ax + var_ay + var_az

            avg_gas = sum(gas_raws) / len(gas_raws) if gas_raws else 0
            is_valve_disabled = "DISABLED" in valve_states

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
