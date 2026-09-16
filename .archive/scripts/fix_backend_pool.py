import re

with open('src/server/consensus.py', 'r') as f:
    py = f.read()

# Add psycopg2.pool
py = py.replace('import psycopg2\n', 'import psycopg2\nfrom psycopg2 import pool\n')

# Replace get_db_connection
target_conn = '''def get_db_connection():
    try:
        return psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, dbname=DB_NAME)
    except:
        return None'''

replacement_conn = '''# Global Connection Pool
db_pool = None
try:
    db_pool = psycopg2.pool.ThreadedConnectionPool(1, 20, host=DB_HOST, user=DB_USER, password=DB_PASS, dbname=DB_NAME)
except Exception as e:
    print("Gagal membuat Connection Pool:", e)

def get_db_connection():
    if db_pool:
        try:
            return db_pool.getconn()
        except:
            return None
    return None

def release_db_connection(conn):
    if db_pool and conn:
        db_pool.putconn(conn)'''

py = py.replace(target_conn, replacement_conn)

# Fix save_telemetry
target_telemetry = '''    try:
        cur = conn.cursor()
        
        # Konversi Unix Epoch ke TIMESTAMPTZ secara aman
        ts_value = payload.get("ts", 0)
        if ts_value and ts_value > 1000000:
            cur.execute("""
                INSERT INTO tb_sensor_telemetry (ts, node_id, pga, sta_lta, freq_hz, ax, ay, az, lat, lon, uptime_ms)
                VALUES (to_timestamp(%s), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (
                ts_value,
                payload.get("node_id"),
                payload.get("pga", 0),
                payload.get("sta_lta", 0),
                payload.get("freq_hz", 0),
                payload.get("ax", 0),
                payload.get("ay", 0),
                payload.get("az", 0),
                payload.get("lat", 0),
                payload.get("lon", 0),
                payload.get("uptime", 0)
            ))
            conn.commit()
    except Exception as e:
        print("Error saving telemetry:", e)'''

target_telemetry_replace = '''    try:
        cur = conn.cursor()
        
        # Konversi Unix Epoch ke TIMESTAMPTZ secara aman
        ts_value = payload.get("ts", 0)
        
        # JIKA epoch berupa integer milidetik, konversi ke detik untuk PostgreSQL
        if ts_value > 2000000000000:
            ts_value = ts_value / 1000.0

        if ts_value and ts_value > 1000000:
            cur.execute("""
                INSERT INTO tb_sensor_telemetry (ts, node_id, pga, sta_lta, freq_hz, ax, ay, az, lat, lon, uptime_ms)
                VALUES (to_timestamp(%s), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (
                ts_value,
                payload.get("node_id"),
                payload.get("pga", 0),
                payload.get("sta_lta", 0),
                payload.get("freq_hz", 0),
                payload.get("ax", 0),
                payload.get("ay", 0),
                payload.get("az", 0),
                payload.get("lat", 0),
                payload.get("lon", 0),
                payload.get("uptime", 0)
            ))
            conn.commit()
    except Exception as e:
        print("Error saving telemetry:", e)
    finally:
        release_db_connection(conn)'''

# Wait, the current save_telemetry doesn't even have conn.commit() in the try block!
# Let's just use regex to replace the whole body of save_telemetry

with open('src/server/consensus.py', 'w') as f:
    f.write(py)

