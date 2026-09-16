import json
import re

# ==========================================
# 1. FIX KONEKSI BASI & BUAT TABEL KESEHATAN
# ==========================================
with open('src/server/consensus.py', 'r') as f:
    py = f.read()

# Tambahkan pembuatan tabel server_health saat inisialisasi DB
target_db_init = '''        conn.commit()
        release_db_connection(conn)
        print("[DB] Berhasil terhubung ke PostgreSQL dan verifikasi tabel.")'''

replacement_db_init = '''        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tb_server_health (
                ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                cpu_percent REAL,
                ram_percent REAL,
                uptime_hours REAL,
                status VARCHAR(32)
            );
        """)
        conn.commit()
        release_db_connection(conn)
        print("[DB] Berhasil terhubung ke PostgreSQL dan verifikasi tabel.")'''
py = py.replace(target_db_init, replacement_db_init)

# Ubah thread telemetry agar langsung INSERT ke DB (Bypass MQTT)
target_telemetry = '''                payload = {
                    "cpu_percent": cpu_usage,
                    "ram_percent": ram_usage,
                    "uptime_hours": uptime_hrs,
                    "status": "ONLINE"
                }
                mqtt_client.publish("lindu/server/status", json.dumps(payload), retain=True)'''

replacement_telemetry = '''                # Kirim ke MQTT untuk status
                payload = {"cpu_percent": cpu_usage, "ram_percent": ram_usage, "uptime_hours": uptime_hrs, "status": "ONLINE"}
                mqtt_client.publish("lindu/server/status", json.dumps(payload), retain=True)
                
                # Simpan ke DB untuk dibaca Grafana
                conn = get_db_connection()
                if conn:
                    try:
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO tb_server_health (cpu_percent, ram_percent, uptime_hours, status)
                            VALUES (%s, %s, %s, %s)
                        """, (cpu_usage, ram_usage, uptime_hrs, "ONLINE"))
                        conn.commit()
                        
                        # Auto-Purge data kesehatan server > 1 hari agar tidak penuh
                        cursor.execute("DELETE FROM tb_server_health WHERE ts < NOW() - INTERVAL '1 day'")
                        conn.commit()
                    finally:
                        release_db_connection(conn)'''
py = py.replace(target_telemetry, replacement_telemetry)

# Fix Stale Connection dengan ping & auto-reconnect
target_getconn = '''def get_db_connection():
    try:
        return db_pool.getconn()
    except Exception as e:
        print("[DB ERROR] Gagal mengambil koneksi dari pool:", e)
        return None'''

replacement_getconn = '''def get_db_connection():
    global db_pool
    try:
        conn = db_pool.getconn()
        # PING TEST: Pastikan koneksi tidak basi (stale)
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            # Jika basi, hancurkan pool dan buat baru
            print("[DB WARN] Koneksi basi terdeteksi! Membangun ulang Connection Pool...")
            db_pool.closeall()
            db_pool = psycopg2.pool.ThreadedConnectionPool(1, 20, host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
            conn = db_pool.getconn()
        return conn
    except Exception as e:
        print("[DB ERROR] Gagal mengambil koneksi dari pool:", e)
        return None'''
py = py.replace(target_getconn, replacement_getconn)

with open('src/server/consensus.py', 'w') as f:
    f.write(py)

# ==========================================
# 2. TAMBAHKAN PANEL KESEHATAN KE GRAFANA
# ==========================================
with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    dash = json.load(f)

# Geser panel Command Center ke kanan, beri ruang di kiri untuk Server Health
for p in dash['panels']:
    if 'Command Center' in p.get('title', ''):
        p['gridPos'] = {"w": 14, "h": 9, "x": 10, "y": 63}

server_health_panel = {
    "type": "stat",
    "title": "🖥️ Raspberry Pi (Server Health)",
    "id": 22,
    "gridPos": {"w": 10, "h": 9, "x": 0, "y": 63},
    "targets": [{
        "refId": "A",
        "rawSql": "SELECT cpu_percent AS \"CPU (%)\", ram_percent AS \"RAM (%)\", uptime_hours AS \"Uptime (Jam)\" FROM tb_server_health ORDER BY ts DESC LIMIT 1",
        "format": "table",
        "datasource": {"type": "grafana-postgresql-datasource", "uid": "lindu_pg"}
    }],
    "datasource": {"type": "grafana-postgresql-datasource", "uid": "lindu_pg"},
    "fieldConfig": {
        "defaults": {
            "color": {"mode": "thresholds"},
            "thresholds": {
                "mode": "absolute",
                "steps": [
                    {"color": "green", "value": None},
                    {"color": "orange", "value": 75},
                    {"color": "red", "value": 90}
                ]
            }
        }
    },
    "options": {
        "reduceOptions": {"calcs": ["lastNotNull"]},
        "orientation": "vertical",
        "textMode": "auto"
    }
}
dash['panels'].append(server_health_panel)

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    json.dump(dash, f, indent=2)

