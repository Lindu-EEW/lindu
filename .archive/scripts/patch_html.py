import re

with open('src/dashboard/index.html', 'r') as f:
    content = f.read()

# 1. Add Control Panel UI next to the left panel
control_panel_ui = '''            <div class="bg-black/80 p-5 rounded-xl border border-gray-700 pointer-auto shadow-xl">
                <h1 class="text-3xl font-black text-orange-500 tracking-wider">LINDU.ID <span class="text-gray-400 text-sm font-normal">OPS CENTER</span></h1>
                <div class="mt-3 space-y-1">
                    <p class="text-gray-400 text-sm">MQTT Link: <span id="mqtt-status" class="text-yellow-400 font-bold">Menyambungkan...</span></p>
                    <p class="text-gray-400 text-sm">Sensor Aktif: <span id="node-count" class="text-green-400 font-bold text-lg">0</span></p>
                </div>
            </div>
            
            <!-- NEW CONTROL PANEL (Kanan Atas) -->
            <div class="bg-gray-900/90 p-5 rounded-xl border border-blue-500/50 pointer-auto shadow-2xl backdrop-blur-sm w-96 max-h-[90vh] overflow-y-auto">
                <h2 class="text-xl font-bold text-blue-400 mb-4 border-b border-blue-500/30 pb-2"><i class="fas fa-terminal"></i> Command Center</h2>
                
                <div id="metrics-container" class="space-y-4">
                    <!-- Metrics akan dirender di sini via JS -->
                    <div class="text-center text-gray-500 text-sm">Memuat metrik node...</div>
                </div>
            </div>
'''
if "NEW CONTROL PANEL" not in content:
    content = content.replace('''            <div class="bg-black/80 p-5 rounded-xl border border-gray-700 pointer-auto shadow-xl">
                <h1 class="text-3xl font-black text-orange-500 tracking-wider">LINDU.ID <span class="text-gray-400 text-sm font-normal">OPS CENTER</span></h1>
                <div class="mt-3 space-y-1">
                    <p class="text-gray-400 text-sm">MQTT Link: <span id="mqtt-status" class="text-yellow-400 font-bold">Menyambungkan...</span></p>
                    <p class="text-gray-400 text-sm">Sensor Aktif: <span id="node-count" class="text-green-400 font-bold text-lg">0</span></p>
                    

                </div>
            </div>''', control_panel_ui)


# 2. Add FontAwesome to head if missing
if "font-awesome" not in content.lower() and "fontawesome" not in content.lower():
    content = content.replace('</head>', '    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">\n</head>')

# 3. Add JS functions for metrics and commands at the bottom
js_logic = '''
        // --- CONTROL CENTER LOGIC ---
        async function fetchMetrics() {
            try {
                const res = await fetch('/api/metrics');
                const data = await res.json();
                const container = document.getElementById('metrics-container');
                
                if (data.length === 0) {
                    container.innerHTML = '<div class="text-center text-gray-500 text-sm">Belum ada data metrik.</div>';
                    return;
                }
                
                let html = '';
                data.forEach(n => {
                    const statusColor = n.status === 'online' ? 'text-green-400' : 'text-red-400';
                    const otaColor = n.ota_status === 'IDLE' ? 'text-gray-400' : (n.ota_status.includes('ERROR') ? 'text-red-500' : 'text-yellow-400 animate-pulse');
                    const sensorColor = n.sensor_ok ? 'text-green-400' : 'text-red-500';
                    
                    html += `
                    <div class="bg-black/60 p-3 rounded-lg border border-gray-700">
                        <div class="flex justify-between items-center mb-2">
                            <span class="font-mono font-bold text-white">${n.node_id}</span>
                            <span class="text-[10px] uppercase font-bold px-2 py-1 rounded bg-gray-800 ${statusColor}">${n.status}</span>
                        </div>
                        <div class="grid grid-cols-2 gap-x-2 gap-y-1 text-xs mb-3">
                            <div class="text-gray-400">Versi: <span class="text-white font-mono">${n.fw_version}</span></div>
                            <div class="text-gray-400">OTA: <span class="font-mono ${otaColor}">${n.ota_status}</span></div>
                            <div class="text-gray-400">Latensi: <span class="text-white">${n.latency_ms} ms</span></div>
                            <div class="text-gray-400">Sensor: <span class="${sensorColor}">${n.sensor_ok ? 'OK' : 'FAIL'}</span></div>
                        </div>
                        <div class="flex gap-2">
                            <button onclick="sendCommand('valve_lock', '${n.node_id}')" class="flex-1 bg-red-900/50 hover:bg-red-700 text-red-200 text-[10px] py-1 rounded border border-red-700 transition"><i class="fas fa-lock"></i> Lock</button>
                            <button onclick="sendCommand('valve_unlock', '${n.node_id}')" class="flex-1 bg-green-900/50 hover:bg-green-700 text-green-200 text-[10px] py-1 rounded border border-green-700 transition"><i class="fas fa-unlock"></i> Unlock</button>
                        </div>
                        <div class="flex gap-2 mt-2">
                            <button onclick="sendCommand('identify', '${n.node_id}')" class="flex-1 bg-gray-800 hover:bg-gray-600 text-white text-[10px] py-1 rounded border border-gray-600 transition"><i class="fas fa-lightbulb"></i> Identify</button>
                            <button onclick="sendCommand('force_update', '${n.node_id}')" class="flex-1 bg-blue-900/50 hover:bg-blue-700 text-blue-200 text-[10px] py-1 rounded border border-blue-700 transition"><i class="fas fa-download"></i> OTA Update</button>
                        </div>
                    </div>`;
                });
                
                // Tambahkan tombol Global di bawah
                html += `
                <div class="mt-4 pt-4 border-t border-gray-700">
                    <button onclick="sendCommand('force_update', 'all')" class="w-full bg-purple-900/50 hover:bg-purple-700 text-purple-200 text-xs py-2 rounded border border-purple-700 transition font-bold"><i class="fas fa-sync"></i> UPDATE SEMUA NODE (GLOBAL)</button>
                </div>
                `;
                
                container.innerHTML = html;
            } catch (err) {
                console.error("Error fetching metrics:", err);
            }
        }
        
        async function sendCommand(cmd, target_node) {
            try {
                const res = await fetch('/api/cmd', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ cmd, target_node })
                });
                const data = await res.json();
                if (res.ok) {
                    alert(`Perintah terkirim: ${cmd} -> ${target_node}`);
                } else {
                    alert(`Gagal mengirim: ${data.error}`);
                }
            } catch (err) {
                alert(`Error jaringan: ${err}`);
            }
        }

        // Jalankan fetchMetrics setiap 2 detik
        setInterval(fetchMetrics, 2000);
        fetchMetrics();
        // --- END CONTROL CENTER LOGIC ---
'''
if "fetchMetrics" not in content:
    content = content.replace('// Simulasi pergerakan marker (untuk demo visual)', js_logic + '\n        // Simulasi pergerakan marker (untuk demo visual)')

with open('src/dashboard/index.html', 'w') as f:
    f.write(content)

