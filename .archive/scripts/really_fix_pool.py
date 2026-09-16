import re

with open('src/server/consensus.py', 'r') as f:
    py = f.read()

target = '''def get_db_connection():
    if db_pool:
        try:
            return db_pool.getconn()
        except:
            return None
    return None'''

replacement = '''def get_db_connection():
    global db_pool
    if db_pool:
        try:
            conn = db_pool.getconn()
            # PING TEST: Pastikan koneksi tidak basi (stale)
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
            except Exception:
                print("[DB WARN] Koneksi basi terdeteksi! Membangun ulang Connection Pool...")
                db_pool.closeall()
                import psycopg2
                import psycopg2.pool
                from config import DB_HOST, DB_NAME, DB_USER, DB_PASS
                db_pool = psycopg2.pool.ThreadedConnectionPool(1, 20, host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
                conn = db_pool.getconn()
            return conn
        except Exception as e:
            print("[DB ERROR] Gagal mengambil koneksi dari pool:", e)
            return None
    return None'''

py = py.replace(target, replacement)

with open('src/server/consensus.py', 'w') as f:
    f.write(py)

