#!/usr/bin/env python3
"""
Lindu-EEW: Update Real Earthquake Episodes Index from TimescaleDB
Extracts all shock vibration episodes across the entire operational history (Sept 16 - Oct 18)
directly from the live TimescaleDB database and updates historical_earthquake_episodes_index.csv.
"""

import csv
import os
import psycopg2
from datetime import datetime, timezone

import sys

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_EPISODES_INDEX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUTPUT_DIR, "historical_earthquake_episodes_index.csv")

DB_HOST = os.getenv("DB_HOST", "timescaledb")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "lindu_admin")
DB_PASS = os.getenv("DB_PASS", "supersecretpassword")
DB_NAME = os.getenv("DB_NAME", "lindudb")

CLUSTER_GAP_THRESHOLD_SEC = 25.0

def main():
    print("=" * 75)
    print("  LINDU-EEW: Updating Historical Earthquake Episodes from Live TimescaleDB")
    print("=" * 75)

    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        dbname=DB_NAME
    )
    cur = conn.cursor()

    # 1. Fetch consensus alert timestamps for ground-truth correlation
    cur.execute("SELECT time_alert FROM tb_system_alerts ORDER BY time_alert ASC;")
    alert_times = [r[0].timestamp() for r in cur.fetchall() if r[0]]
    print(f"Loaded {len(alert_times)} consensus alert timestamps from tb_system_alerts.")

    # 2. Fetch all telemetry records with PGA >= 0.035g
    cur.execute("""
        SELECT time, node_id, pga, rms, valve_status, gas_alert
        FROM sensor_telemetry
        WHERE pga >= 0.035
        ORDER BY time ASC;
    """)
    rows = cur.fetchall()
    print(f"Fetched {len(rows)} shock points (PGA >= 0.035g) from sensor_telemetry.")

    # 3. Cluster shock points
    clusters = []
    current_cluster = []

    for r in rows:
        t, node_id, pga, rms, valve, gas = r
        epoch = t.timestamp()
        item = {
            "dt": t,
            "epoch": epoch,
            "node_id": node_id,
            "pga": float(pga or 0),
            "rms": float(rms or 0),
            "valve": valve,
            "gas": gas
        }
        if not current_cluster:
            current_cluster.append(item)
        else:
            if epoch - current_cluster[-1]["epoch"] <= CLUSTER_GAP_THRESHOLD_SEC:
                current_cluster.append(item)
            else:
                clusters.append(current_cluster)
                current_cluster = [item]
    if current_cluster:
        clusters.append(current_cluster)

    print(f"Segmented {len(clusters)} distinct shock episodes.")

    # 4. Generate episode metadata
    episodes_meta = []
    for ep_idx, cluster in enumerate(clusters, start=1):
        onset_time = cluster[0]["epoch"]
        peak_item = max(cluster, key=lambda x: x["pga"])
        peak_time = peak_item["epoch"]
        coda_end_time = cluster[-1]["epoch"]

        nodes_in_cluster = set(x["node_id"] for x in cluster)
        node_count = len(nodes_in_cluster)
        max_pga = peak_item["pga"]
        max_rms = max(x["rms"] for x in cluster)

        if node_count >= 2:
            event_id = f"EQ_EVENT_{ep_idx:03d}"
            category = "MULTI_NODE_EARTHQUAKE"
        else:
            event_id = f"DISTURB_{ep_idx:03d}"
            category = "LOCAL_DISTURBANCE"

        has_alert_match = any(abs(a - onset_time) <= 60.0 for a in alert_times)
        valve_tripped = any(x["valve"] == "DISABLED" for x in cluster)
        gas_alert = any(x["gas"] is True for x in cluster)
        duration_sec = (coda_end_time - onset_time)

        episode_info = {
            "event_id": event_id,
            "category": category,
            "onset_time": cluster[0]["dt"].strftime("%Y-%m-%d %H:%M:%S+00"),
            "peak_time": peak_item["dt"].strftime("%Y-%m-%d %H:%M:%S+00"),
            "duration_sec": round(duration_sec, 2),
            "total_points": len(cluster),
            "participating_nodes": ";".join(sorted(list(nodes_in_cluster))),
            "node_count": node_count,
            "peak_pga": round(max_pga, 5),
            "peak_rms": round(max_rms, 5),
            "consensus_alert_correlated": 1 if has_alert_match else 0,
            "valve_tripped": 1 if valve_tripped else 0,
            "gas_alert": 1 if gas_alert else 0,
            "p_to_s_lead_time_sec": round(max(0.0, peak_time - onset_time), 2)
        }
        episodes_meta.append(episode_info)

    # 5. Write to CSV
    headers = list(episodes_meta[0].keys())
    with open(OUTPUT_EPISODES_INDEX, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(episodes_meta)

    print(f"\n[OK] Successfully wrote {len(episodes_meta)} episodes to: {OUTPUT_EPISODES_INDEX}")
    
    eq_count = sum(1 for e in episodes_meta if e["category"] == "MULTI_NODE_EARTHQUAKE")
    disturb_count = sum(1 for e in episodes_meta if e["category"] == "LOCAL_DISTURBANCE")
    print(f"  • Multi-Node Earthquakes: {eq_count}")
    print(f"  • Local Disturbances:     {disturb_count}")
    print(f"  • Max PGA:                {max(e['peak_pga'] for e in episodes_meta):.4f} g")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
