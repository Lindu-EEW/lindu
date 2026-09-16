import re

with open('src/server/consensus.py', 'r') as f:
    py = f.read()

target = '''        # [SYARAT TRIGGER ALERT LOKAL]
        if pga < 0.12:
            return # Abaikan noise kecil'''

replacement = '''        freq_hz = payload.get("freq_hz", 0)
        
        # [ALGORITMA ANTI-HOAKS / FILTER GETARAN KAKI]
        # 1. PGA >= 0.12 (Getaran harus cukup keras)
        # 2. STA/LTA >= 2.0 (Energi getaran harus berkelanjutan, bukan benturan singkat)
        # 3. Frekuensi <= 20 Hz (Gelombang seismik bumi, bukan ketukan/hentakan sepatu yang tinggi)
        is_real_quake = (pga >= 0.12 and sta_lta >= 2.0 and freq_hz <= 20)
        
        if not is_real_quake:
            return # Buang hentakan kaki, buku jatuh, dan noise kecil'''

py = py.replace(target, replacement)

with open('src/server/consensus.py', 'w') as f:
    f.write(py)

