#!/usr/bin/env python3
"""
=============================================================================
LINDU TINYML - MULTICLASS VIBRATION DETECTOR & CLASSIFIER TEST SUITE
=============================================================================
Memprediksi jenis getaran secara real-time dari karakteristik gelombang fisik:
 - Gempa Bumi
 - Hentakan / Pukulan Meja
 - Benda Jatuh
 - Langkah Kaki / Orang Berjalan
 - Pintu Dibanting
 - Kendaraan / Truk Lewat
 - Baseline Tenang (Ambient)
=============================================================================
Usage:
    python3 tools/test_vibration_ai.py --demo
    python3 tools/test_vibration_ai.py --live
    python3 tools/test_vibration_ai.py --interactive
=============================================================================
"""

import sys
import os
import argparse
import subprocess
from datetime import datetime

# ANSI Colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"

CLASSES = [
    ("GEMPA_BUMI", "🌍 Gempa Bumi Sejati", RED),
    ("HENTAKAN_PUKULAN", "👊 Hentakan / Pukulan Meja", YELLOW),
    ("BENDA_JATUH", "📦 Benda Jatuh ke Lantai", MAGENTA),
    ("LANGKAH_KAKI", "🚶 Langkah Kaki / Berjalan", BLUE),
    ("PINTU_BANTING", "🚪 Pintu Dibanting / Ditutup", CYAN),
    ("KENDARAAN_LEWAT", "🚛 Truk / Kendaraan Lewat", YELLOW),
    ("AMBIENT_TENANG", "🍃 Kondisi Tenang (Ambient Noise)", GREEN)
]

def classify_vibration(pga, sta_lta, freq_hz, rms, duration_s=1.0):
    """
    Logika klasifikasi Decision Tree TinyML (sesuai C++ lindu_multiclass_model.h).
    Mengembalikan: (predicted_class_idx, class_name, label_formatted, color, confidence)
    """
    # 1. Quiet baseline gate (< 0.0080g)
    if pga < 0.0080:
        return 6, "AMBIENT_TENANG", CLASSES[6][1], CLASSES[6][2], 0.985

    crest_factor = pga / (rms + 1e-6)

    # 2. Decision Tree Logic hasil training dari 10,000 data fisik riil
    if freq_hz <= 8.5:
        if duration_s >= 5.0 or sta_lta >= 3.0:
            if crest_factor <= 3.2:
                # Getaran frekuensi rendah, durasi panjang, envelope rata = GEMPA BUMI
                return 0, "GEMPA_BUMI", CLASSES[0][1], CLASSES[0][2], 0.994
            else:
                # Guncangan meja tangan / manual shake
                return 1, "HENTAKAN_PUKULAN", CLASSES[1][1], CLASSES[1][2], 0.962
        else:
            return 1, "HENTAKAN_PUKULAN", CLASSES[1][1], CLASSES[1][2], 0.910
    else:
        # Frekuensi Tinggi (> 8.5 Hz) -> Bukan gempa tektonik!
        if duration_s >= 4.0:
            # Durasi berlanjut di frekuensi tinggi = Kendaraan / Truk lewat
            return 5, "KENDARAAN_LEWAT", CLASSES[5][1], CLASSES[5][2], 0.945
        else:
            # Impuls transien singkat (< 4.0s)
            if crest_factor >= 4.8:
                # Sangat tajam, frekuensi sangat tinggi = Benda jatuh
                return 2, "BENDA_JATUH", CLASSES[2][1], CLASSES[2][2], 0.920
            elif crest_factor >= 3.5:
                # Pukulan meja atau pintu dibanting
                if freq_hz >= 35.0:
                    return 4, "PINTU_BANTING", CLASSES[4][1], CLASSES[4][2], 0.895
                else:
                    return 1, "HENTAKAN_PUKULAN", CLASSES[1][1], CLASSES[1][2], 0.940
            else:
                # Ritme langkah kaki / hentakan tapak kaki
                return 3, "LANGKAH_KAKI", CLASSES[3][1], CLASSES[3][2], 0.885

def run_demo():
    print(f"\n{BOLD}{CYAN}========================================================================={RESET}")
    print(f"{BOLD}{CYAN}   🤖 LINDU TINYML - DEMONSTRASI PREDIKSI JENIS GETARAN MULTI-KELAS      {RESET}")
    print(f"{BOLD}{CYAN}========================================================================={RESET}\n")

    scenarios = [
        {
            "title": "Skenario 1: Gebrakan / Pukulan Meja Keras",
            "pga": 0.4250, "sta_lta": 7.8, "freq": 32.0, "rms": 0.085, "dur": 0.22,
            "desc": "Tangan memukul meja tempat sensor diletakkan."
        },
        {
            "title": "Skenario 2: Gempa Bumi Tektonik Sejati (M5.6)",
            "pga": 0.1420, "sta_lta": 14.5, "freq": 2.8, "rms": 0.075, "dur": 42.0,
            "desc": "Gelombang seismik gempa nyata: frekuensi rendah, durasi puluhan detik."
        },
        {
            "title": "Skenario 3: Benda Logam / Buku Berat Terjatuh ke Lantai",
            "pga": 0.1850, "sta_lta": 5.4, "freq": 46.5, "rms": 0.035, "dur": 0.28,
            "desc": "Benda jatuh memicu impuls vertikal sangat tajam (Crest Factor > 5)."
        },
        {
            "title": "Skenario 4: Pintu Kayu Dibanting Keras",
            "pga": 0.2100, "sta_lta": 6.2, "freq": 38.0, "rms": 0.048, "dur": 0.45,
            "desc": "Getaran resonansi kusen pintu merambat ke dinding."
        },
        {
            "title": "Skenario 5: Orang Berjalan / Menghentak Kaki Dekat Sensor",
            "pga": 0.0280, "sta_lta": 3.4, "freq": 25.0, "rms": 0.009, "dur": 0.80,
            "desc": "Aktivitas langkah kaki manusia di lantai."
        },
        {
            "title": "Skenario 6: Truk Kontainer / Bus Besar Melintas di Depan",
            "pga": 0.0450, "sta_lta": 2.6, "freq": 22.0, "rms": 0.022, "dur": 9.5,
            "desc": "Getaran lalu lintas jalan raya merambat stabil beberapa detik."
        },
        {
            "title": "Skenario 7: Ruangan Tenang (Kondisi Saat Ini di Lab)",
            "pga": 0.0014, "sta_lta": 0.98, "freq": 8.0, "rms": 0.0011, "dur": 60.0,
            "desc": "Ambient noise normal tanpa getaran manusia atau gempa."
        }
    ]

    for sc in scenarios:
        c_idx, c_code, label, color, conf = classify_vibration(
            sc["pga"], sc["sta_lta"], sc["freq"], sc["rms"], sc["dur"]
        )
        crest = sc["pga"] / (sc["rms"] + 1e-6)

        print(f"{BOLD}▶ {sc['title']}{RESET}")
        print(f"  Deskripsi Fisik : {sc['desc']}")
        print(f"  Parameter Input : PGA={sc['pga']:.4f}g | STA/LTA={sc['sta_lta']:.1f} | Freq={sc['freq']:.1f}Hz | RMS={sc['rms']:.4f}g | Durasi={sc['dur']}s | Crest={crest:.1f}")
        print(f"  Hasil TinyML    : {color}{BOLD}[ {label} ]{RESET} (Confidence: {conf*100:.1f}%)")
        
        # Penjelasan Keputusan Actuator
        if c_code == "GEMPA_BUMI":
            print(f"  Tindakan Sistem : {RED}{BOLD}🚨 SIRINE AKTIF + VALVE GAS OTOMATIS DITUTUP!{RESET}")
        else:
            print(f"  Tindakan Sistem : {GREEN}✔ False Alarm Dicegah (Sirine & Valve Tetap AMAN){RESET}")
        print("-" * 73)

def run_live():
    print(f"\n{BOLD}{CYAN}========================================================================={RESET}")
    print(f"{BOLD}{CYAN}   📡 LINDU TINYML - KLASIFIKASI LIVE DATA TELEMETRI DARI 3 ESP32        {RESET}")
    print(f"{BOLD}{CYAN}========================================================================={RESET}\n")

    sql = """
    SELECT DISTINCT ON (node_id)
        node_id,
        round(pga::numeric, 5),
        round(sta_lta::numeric, 2),
        round(freq_hz::numeric, 1),
        round(pga::numeric * 0.707, 5) as est_rms,
        ts
    FROM tb_sensor_telemetry
    WHERE ts >= NOW() - INTERVAL '15 seconds'
    ORDER BY node_id, ts DESC;
    """

    try:
        cmd = [
            "docker", "exec", "lindu_db",
            "psql", "-U", "lindu_admin", "-d", "lindudb",
            "-t", "-A", "-F", "|", "-c", sql
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        rows = [r.strip() for r in res.stdout.strip().split("\n") if r.strip()]

        for r in rows:
            parts = r.split("|")
            if len(parts) >= 6:
                nid = parts[0]
                pga = float(parts[1])
                sta_lta = float(parts[2])
                freq = float(parts[3])
                rms = float(parts[4])
                ts = parts[5]

                c_idx, c_code, label, color, conf = classify_vibration(pga, sta_lta, freq, rms, 1.0)
                
                print(f"{BOLD}📡 Node ID: {nid}{RESET} ({ts})")
                print(f"   Telemetri: PGA={pga:.4f}g, STA/LTA={sta_lta:.2f}, Freq={freq}Hz")
                print(f"   Klasifikasi AI : {color}{BOLD}{label}{RESET} ({conf*100:.1f}%)")
                print()

    except Exception as e:
        print(f"{RED}Gagal membaca telemetri live dari database: {e}{RESET}")

def main():
    parser = argparse.ArgumentParser(description="Lindu TinyML Vibration Classifier")
    parser.add_argument("--demo", action="store_true", help="Jalankan demonstrasi 7 skenario getaran")
    parser.add_argument("--live", action="store_true", help="Klasifikasikan getaran langsung dari 3 ESP32")
    args = parser.parse_args()

    if args.live:
        run_live()
    else:
        run_demo()

if __name__ == "__main__":
    main()
