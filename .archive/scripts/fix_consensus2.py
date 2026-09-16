import re

with open('src/server/consensus.py', 'r') as f:
    content = f.read()

# Replace the block
old_block = """        is_real_quake = (pga >= 0.12 and sta_lta >= 2.0 and freq_hz <= 20)
        
        if not is_real_quake:
            return # Buang hentakan kaki, buku jatuh, dan noise kecil
        
        # Simpan SETIAP pesan telemetri ke database (rekaman detik-per-detik)
        save_telemetry(payload)"""

new_block = """        # Simpan SETIAP pesan telemetri ke database (rekaman detik-per-detik)
        # Termasuk data gas, cuaca, dll.
        save_telemetry(payload)

        # [ALGORITMA ANTI-HOAKS / FILTER GETARAN KAKI]
        is_real_quake = (pga >= 0.12 and sta_lta >= 2.0 and freq_hz <= 20)
        
        if not is_real_quake:
            return # Buang hentakan kaki, buku jatuh, dan noise kecil"""

content = content.replace(old_block, new_block)

with open('src/server/consensus.py', 'w') as f:
    f.write(content)

