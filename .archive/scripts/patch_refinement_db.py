import re

with open('src/server/consensus.py', 'r') as f:
    py = f.read()

# Cari bagian penerbitan ALARM_UPDATE
target = '''                    mqtt_client.publish(TOPIC_ALARM, json.dumps(update_payload))
                    print(f"[LIVE REFINEMENT] Pusat: {refined_lat:.4f}, {refined_lon:.4f} | Mag: {refined_mag:.1f} | Nodes: {len(active_quake['nodes_pga'])}")'''

replacement = '''                    mqtt_client.publish(TOPIC_ALARM, json.dumps(update_payload))
                    print(f"[LIVE REFINEMENT] Pusat: {refined_lat:.4f}, {refined_lon:.4f} | Mag: {refined_mag:.1f} | Nodes: {len(active_quake['nodes_pga'])}")
                    
                    # Update database agar Grafana menampilkan magnitudo dan radius yang sudah direvisi
                    try:
                        conn_update = get_db_connection()
                        if conn_update:
                            cur_update = conn_update.cursor()
                            cur_update.execute("""
                                UPDATE tb_system_alerts 
                                SET magnitude = %s, radius_km = %s, epi_lat = %s, epi_lon = %s, description = %s, triggering_nodes = %s
                                WHERE time_alert >= NOW() - INTERVAL '1 minute'
                                RETURNING time_alert;
                            """, (
                                round(refined_mag, 1), 
                                round(refined_radius, 1), 
                                refined_lat, 
                                refined_lon, 
                                update_payload["desc"],
                                json.dumps(t_nodes)
                            ))
                            conn_update.commit()
                    except Exception as e:
                        print("Gagal update DB Refinement:", e)
                    finally:
                        release_db_connection(conn_update)'''

py = py.replace(target, replacement)

with open('src/server/consensus.py', 'w') as f:
    f.write(py)

