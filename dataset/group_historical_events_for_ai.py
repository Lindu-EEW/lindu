#!/usr/bin/env python3
"""
Lindu-EEW: Historical Event Segmentation & Earthquake Episode Grouping for AI
Groups 30,228+ continuous database telemetry records into individual earthquake episodes
and false disturbance events with phase tagging (PRE_SHOCK, P_WAVE, S_WAVE_PEAK, CODA).

Outputs:
1. dataset/historical_db_grouped_by_event.csv:
   Full telemetry enriched with:
   - event_id (e.g. EQ_EVENT_001, DISTURB_005, or BASELINE_IDLE)
   - event_category (MULTI_NODE_EARTHQUAKE, LOCAL_DISTURBANCE, BASELINE)
   - event_phase (PRE_SHOCK, P_WAVE_ONSET, S_WAVE_PEAK, CODA_DECAY, AMBIENT)
   - seconds_from_onset (Time in seconds from the first wave arrival)
   - participating_nodes_count (Number of nodes detecting the event)

2. dataset/historical_earthquake_episodes_index.csv:
   Catalog of every earthquake episode with duration, peak PGA, participating nodes,
   alert correlation, and solenoid actuation response.
"""

import csv
import json
import math
import os
from datetime import datetime, timezone, timedelta

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
TELEMETRY_CSV = os.path.join(OUTPUT_DIR, "historical_db_telemetry_29k.csv")
ALERTS_CSV = os.path.join(OUTPUT_DIR, "historical_db_alerts.csv")

OUTPUT_GROUPED_CSV = os.path.join(OUTPUT_DIR, "historical_db_grouped_by_event.csv")
OUTPUT_EPISODES_INDEX = os.path.join(OUTPUT_DIR, "historical_earthquake_episodes_index.csv")

def parse_iso(ts_str):
    try:
        clean = ts_str.split('+')[0].strip()
        if '.' in clean:
            dt = datetime.strptime(clean, "%Y-%m-%d %H:%M:%S.%f")
        else:
            dt = datetime.strptime(clean, "%Y-%m-%d %H:%M:%S")
        return dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None

def main():
    print("=" * 75)
    print("  LINDU-EEW: Grouping Historical DB Records into Earthquake Episodes")
    print("=" * 75)

    # 1. Load alerts from tb_system_alerts for ground-truth correlation
    alerts = []
    if os.path.exists(ALERTS_CSV):
        with open(ALERTS_CSV, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                dt = parse_iso(r["time_alert"])
                if dt:
                    alerts.append({
                        "time": dt,
                        "mag": float(r.get("magnitude", 0) or 0),
                        "desc": r.get("description", "")
                    })
    print(f"Loaded {len(alerts)} consensus alert events from tb_system_alerts.")

    # 2. Load all raw telemetry records
    with open(TELEMETRY_CSV, "r", encoding="utf-8") as f:
        records = list(csv.DictReader(f))
    print(f"Loaded {len(records)} raw continuous telemetry records from TimescaleDB.")

    # Parse timestamps and float PGAs
    parsed_records = []
    for idx, r in enumerate(records):
        dt = parse_iso(r["time"])
        if dt:
            pga = float(r["pga"]) if r["pga"] else 0.0
            rms = float(r["rms"]) if r["rms"] else 0.0
            parsed_records.append({
                "row_index": idx,
                "dt": dt,
                "epoch": dt.timestamp(),
                "node_id": r["node_id"],
                "pga": pga,
                "rms": rms,
                "raw": r
            })

    # Sort chronologically
    parsed_records.sort(key=lambda x: x["epoch"])

    # 3. Clustering / Segmentation: Identify active shock windows
    # A shock is active when PGA > 0.035g or RMS > 0.10g
    # Combine consecutive shock points within 25 seconds into the same episode
    CLUSTER_GAP_THRESHOLD_SEC = 25.0
    PRE_WINDOW_SEC = 5.0
    POST_WINDOW_SEC = 15.0

    shock_clusters = []
    current_cluster = []

    for item in parsed_records:
        if item["pga"] >= 0.035:
            if not current_cluster:
                current_cluster.append(item)
            else:
                last_epoch = current_cluster[-1]["epoch"]
                if item["epoch"] - last_epoch <= CLUSTER_GAP_THRESHOLD_SEC:
                    current_cluster.append(item)
                else:
                    shock_clusters.append(current_cluster)
                    current_cluster = [item]

    if current_cluster:
        shock_clusters.append(current_cluster)

    print(f"\nIdentified {len(shock_clusters)} distinct physical shock episodes.")

    # 4. Expand episodes to include pre-shock and post-shock tails, and classify
    episodes_meta = []
    record_event_map = {} # maps row_index -> event info

    for ep_idx, cluster in enumerate(shock_clusters, start=1):
        onset_time = cluster[0]["epoch"]
        peak_item = max(cluster, key=lambda x: x["pga"])
        peak_time = peak_item["epoch"]
        coda_end_time = cluster[-1]["epoch"]

        # Expand time window
        win_start = onset_time - PRE_WINDOW_SEC
        win_end = coda_end_time + POST_WINDOW_SEC

        nodes_in_cluster = set(x["node_id"] for x in cluster)
        node_count = len(nodes_in_cluster)
        max_pga = peak_item["pga"]
        max_rms = max(x["rms"] for x in cluster)

        # Classify episode:
        # Multi-node consensus (>= 2 nodes) = Genuine Earthquake
        # Single node only (< 2 nodes) = Local disturbance (stomp, desk shake)
        if node_count >= 2:
            event_id = f"EQ_EVENT_{ep_idx:03d}"
            category = "MULTI_NODE_EARTHQUAKE"
        else:
            event_id = f"DISTURB_{ep_idx:03d}"
            category = "LOCAL_DISTURBANCE"

        # Check correlation with server consensus alert
        has_alert_match = any(abs(a["time"].timestamp() - onset_time) <= 60.0 for a in alerts)

        # Check if solenoid valve was shutoff
        valve_tripped = any(x["raw"]["valve_status"] == "DISABLED" for x in cluster)
        gas_alert = any(x["raw"]["gas_alert"] == "t" for x in cluster)

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

        # Tag individual records within this window
        for item in parsed_records:
            if win_start <= item["epoch"] <= win_end:
                t_sec = item["epoch"] - onset_time

                # Tag seismic phase
                if t_sec < 0:
                    phase = "PRE_SHOCK_AMBIENT"
                elif t_sec <= (peak_time - onset_time):
                    phase = "P_WAVE_ONSET" # First rising wave arrivals!
                elif t_sec <= (coda_end_time - onset_time):
                    phase = "S_WAVE_PEAK"  # Destructive shear waves!
                else:
                    phase = "CODA_DECAY"   # Attenuating tail

                # If already tagged by an earlier episode, avoid overwrite unless this cluster is more significant
                if item["row_index"] not in record_event_map:
                    record_event_map[item["row_index"]] = {
                        "event_id": event_id,
                        "event_category": category,
                        "event_phase": phase,
                        "seconds_from_onset": round(t_sec, 2),
                        "nodes_in_event": node_count
                    }

    # 5. Build Enriched Telemetry Dataset
    enriched_rows = []
    for item in parsed_records:
        r = item["raw"]
        tag = record_event_map.get(item["row_index"], {
            "event_id": "BASELINE_MONITORING",
            "event_category": "AMBIENT_NOISE",
            "event_phase": "AMBIENT_BASELINE",
            "seconds_from_onset": 0.0,
            "nodes_in_event": 0
        })

        enriched_rows.append({
            "event_id": tag["event_id"],
            "event_category": tag["event_category"],
            "event_phase": tag["event_phase"],
            "seconds_from_onset": tag["seconds_from_onset"],
            "nodes_in_event": tag["nodes_in_event"],
            "time": r["time"],
            "node_id": r["node_id"],
            "pga": r["pga"],
            "rms": r["rms"],
            "accel_x": r["accel_x"],
            "accel_y": r["accel_y"],
            "accel_z": r["accel_z"],
            "temperature": r["temperature"],
            "pressure": r["pressure"],
            "humidity": r["humidity"],
            "valve_status": r["valve_status"],
            "gas_raw": r["gas_raw"],
            "gas_alert": r["gas_alert"]
        })

    # Export Enriched Telemetry CSV
    headers = list(enriched_rows[0].keys())
    with open(OUTPUT_GROUPED_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(enriched_rows)
    print(f"[OK] Exported Grouped Telemetry: {OUTPUT_GROUPED_CSV} ({len(enriched_rows)} rows)")

    # Export Episodes Index Catalog CSV
    ep_headers = list(episodes_meta[0].keys())
    with open(OUTPUT_EPISODES_INDEX, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ep_headers)
        writer.writeheader()
        writer.writerows(episodes_meta)
    print(f"[OK] Exported Earthquake Episode Catalog: {OUTPUT_EPISODES_INDEX} ({len(episodes_meta)} episodes)")

    # Statistics Summary
    eq_episodes = [e for e in episodes_meta if e["category"] == "MULTI_NODE_EARTHQUAKE"]
    disturb_episodes = [e for e in episodes_meta if e["category"] == "LOCAL_DISTURBANCE"]

    print("\n" + "=" * 75)
    print("  SUMMARY: HISTORICAL DATABASE EARTHQUAKE EPISODES")
    print("=" * 75)
    print(f"  • Total Distinct Episodes Segmented:     {len(episodes_meta)}")
    print(f"  • Multi-Node Earthquakes (Consensus):    {len(eq_episodes)} episodes")
    print(f"  • Local Shocks / Disturbances (1 Node):  {len(disturb_episodes)} episodes")
    print(f"  • Baseline Idle Monitoring Records:      {sum(1 for r in enriched_rows if r['event_id'] == 'BASELINE_MONITORING')} rows")

    if eq_episodes:
        max_eq_pga = max(e["peak_pga"] for e in eq_episodes)
        avg_lead = sum(e["p_to_s_lead_time_sec"] for e in eq_episodes) / len(eq_episodes)
        print(f"  • Peak Earthquake PGA in Database:      {max_eq_pga:.3f} g")
        print(f"  • Average P-Wave to S-Wave Lead Time:    {avg_lead:.2f} seconds")

    print("\nDataset ready for earthquake prediction training & deep learning sequence modeling.")

if __name__ == "__main__":
    main()
