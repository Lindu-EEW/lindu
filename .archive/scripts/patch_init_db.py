with open('src/server/consensus.py', 'r') as f:
    py = f.read()

target = '''        cur.execute("ALTER TABLE tb_system_alerts ADD COLUMN IF NOT EXISTS triggering_nodes JSONB;")
        cur.execute("ALTER TABLE tb_system_alerts ADD COLUMN IF NOT EXISTS seismic_details JSONB;")
        
        cur.execute("ALTER TABLE tb_nodes ADD COLUMN IF NOT EXISTS last_seen TIMESTAMPTZ DEFAULT NOW();")
        print("[DB] Semua tabel dipastikan ada.")'''

replacement = '''        cur.execute("ALTER TABLE tb_system_alerts ADD COLUMN IF NOT EXISTS triggering_nodes JSONB;")
        cur.execute("ALTER TABLE tb_system_alerts ADD COLUMN IF NOT EXISTS seismic_details JSONB;")
        
        cur.execute("ALTER TABLE tb_nodes ADD COLUMN IF NOT EXISTS last_seen TIMESTAMPTZ DEFAULT NOW();")
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tb_server_health (
                ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                cpu_percent REAL,
                ram_percent REAL,
                uptime_hours REAL,
                status VARCHAR(32)
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tb_node_logs (
                ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                node_id VARCHAR(32),
                message TEXT
            );
        """)
        print("[DB] Semua tabel dipastikan ada.")'''
py = py.replace(target, replacement)

with open('src/server/consensus.py', 'w') as f:
    f.write(py)

