import json

# ==========================================
# 1. TAMBAH TABEL LOG DI SERVER PYTHON
# ==========================================
with open('src/server/consensus.py', 'r') as f:
    py = f.read()

target_db_init = '''            CREATE TABLE IF NOT EXISTS tb_server_health ('''
replacement_db_init = '''            CREATE TABLE IF NOT EXISTS tb_node_logs (
                ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                node_id VARCHAR(32),
                message TEXT
            );
            CREATE TABLE IF NOT EXISTS tb_server_health ('''
py = py.replace(target_db_init, replacement_db_init)

target_mqtt = '''    if "/status" in msg.topic:'''
replacement_mqtt = '''    if "/log" in msg.topic:
        try:
            node_id = msg.topic.split('/')[2]
            log_msg = payload.get("message", "Unknown log")
            conn = get_db_connection()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO tb_node_logs (node_id, message) VALUES (%s, %s)", (node_id, log_msg))
                    conn.commit()
                    cur.execute("DELETE FROM tb_node_logs WHERE ts < NOW() - INTERVAL '3 days'")
                    conn.commit()
                finally:
                    release_db_connection(conn)
        except Exception as e:
            print("[LOG ERROR]", e)
        return

    if "/status" in msg.topic:'''
py = py.replace(target_mqtt, replacement_mqtt)

with open('src/server/consensus.py', 'w') as f:
    f.write(py)

# ==========================================
# 2. TAMBAH DROPDOWN & PANEL DI GRAFANA
# ==========================================
with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dash = json.load(f)

# Tambahkan Variabel Dropdown $node_id
if 'templating' not in dash:
    dash['templating'] = {"list": []}
    
dash['templating']['list'] = [{
    "current": {"selected": False, "text": "All", "value": "$__all"},
    "datasource": {"type": "grafana-postgresql-datasource", "uid": "lindu_pg"},
    "definition": "SELECT DISTINCT node_id FROM tb_nodes",
    "hide": 0,
    "includeAll": True,
    "label": "🔍 Pilih Node untuk Diinspeksi",
    "multi": False,
    "name": "node_id",
    "options": [],
    "query": "SELECT DISTINCT node_id FROM tb_nodes",
    "refresh": 1,
    "type": "query"
}]

# Tambahkan Panel Syslog Inspector
syslog_panel = {
    "type": "table",
    "title": "📋 Remote Serial Monitor (Internal ESP32 Logs) - $node_id",
    "id": 23,
    "gridPos": {"w": 24, "h": 7, "x": 0, "y": 72},
    "targets": [{
        "refId": "A",
        "rawSql": "SELECT ts AS \"Waktu (JST)\", node_id AS \"ID Node\", message AS \"System Log\" FROM tb_node_logs WHERE node_id IN ($node_id) ORDER BY ts DESC LIMIT 50",
        "format": "table",
        "datasource": {"type": "grafana-postgresql-datasource", "uid": "lindu_pg"}
    }],
    "datasource": {"type": "grafana-postgresql-datasource", "uid": "lindu_pg"}
}
dash['panels'].append(syslog_panel)

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dash, f, indent=2)

