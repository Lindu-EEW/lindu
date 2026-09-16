import re

with open('src/server/consensus.py', 'r') as f:
    py = f.read()

# Replace any conn.close() with release_db_connection(conn)
py = py.replace('conn.close()', 'release_db_connection(conn)')

# Now fix save_telemetry which was leaking connections completely
telemetry_leak_pattern = '''        if ts_value and ts_value > 1000000:
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

telemetry_fix = '''        if ts_value and ts_value > 1000000:
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

py = py.replace(telemetry_leak_pattern, telemetry_fix)

with open('src/server/consensus.py', 'w') as f:
    f.write(py)
