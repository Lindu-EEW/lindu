import re

with open('src/server/consensus.py', 'r') as f:
    content = f.read()

target = '''        kecepatan = jarak_km / selisih_waktu if selisih_waktu > 0 else float('inf')
        
        # HUKUM FISIKA (P-Wave Velocity Validation)
        print(f"[*] Mengevaluasi {t1['node_id']} & {t2['node_id']}")
        print(f"    Jarak: {jarak_km:.2f} km | Δt: {selisih_waktu:.3f}s | Kecepatan: {kecepatan:.2f} km/s")
        
        # Logika Fisika P-Wave (1.0 km/s - 15.0 km/s)
        if kecepatan > 1.0 and kecepatan < 15.0:
            print(f"[+] KONSENSUS TERCAPAI! Jarak {jarak_km:.2f} KM ditempuh dalam {selisih_waktu} detik (Kecepatan {kecepatan:.2f} km/s).")
            fire_alarm(mqtt_client, t1, t2, kecepatan, selisih_waktu)
            return  # Selesai, buffer sudah dikosongkan di fire_alarm
        else:
            print(f"    [-] Validasi pair gagal. Kecepatan {kecepatan:.2f} km/s tidak masuk akal.")'''

replace = '''        # HUKUM FISIKA & KETERBATASAN WAKTU
        print(f"[*] Mengevaluasi {t1['node_id']} & {t2['node_id']}")
        
        is_valid = False
        if selisih_waktu == 0:
            # 1. Episentrum berada persis di tengah kedua node (equidistant)
            # 2. Rambatan terjadi di bawah 1 detik (karena presisi timestamp ESP32 hanya 1 detik)
            kecepatan = 6.0 # Asumsi kecepatan standar P-Wave
            is_valid = True
            print(f"    Jarak: {jarak_km:.2f} km | Δt: 0.000s -> EPISENTRUM EQUIDISTANT / SIMULTAN")
            print(f"[+] KONSENSUS TERCAPAI! Gelombang tiba bersamaan di kedua sensor.")
        else:
            kecepatan = jarak_km / selisih_waktu
            print(f"    Jarak: {jarak_km:.2f} km | Δt: {selisih_waktu:.3f}s | Kecepatan: {kecepatan:.2f} km/s")
            # Toleransi hingga 25 km/s untuk kompensasi pembulatan detik
            if kecepatan > 0.5 and kecepatan < 25.0:
                is_valid = True
                print(f"[+] KONSENSUS TERCAPAI! Jarak {jarak_km:.2f} KM (Kecepatan {kecepatan:.2f} km/s).")
            else:
                print(f"    [-] Validasi pair gagal. Kecepatan {kecepatan:.2f} km/s tidak masuk akal.")
                
        if is_valid:
            fire_alarm(mqtt_client, t1, t2, kecepatan, selisih_waktu)
            return  # Selesai, buffer sudah dikosongkan di fire_alarm'''

if "EPISENTRUM EQUIDISTANT" not in content:
    content = content.replace(target, replace)
    with open('src/server/consensus.py', 'w') as f:
        f.write(content)

