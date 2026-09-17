import React from 'react';
import { Flame, Unlock } from 'lucide-react';

// Menampilkan peringatan kalau ada node yang mendeteksi kebocoran gas (MQ-2).
// Valve node itu otomatis ditutup oleh firmware (fail-safe) dan TIDAK auto-buka
// sendiri lagi walau bacaan gas sudah normal - operator harus menekan tombol
// di sini (mengirim MQTT cmd "enable_valve") untuk membuka valve-nya kembali.
export default function GasAlertBanner({ activeNodes, sendCommand }) {
  const leakingNodes = Object.values(activeNodes).filter((n) => n.gas_alert);

  if (leakingNodes.length === 0) return null;

  return (
    <div className="absolute top-8 right-6 z-[1000] flex flex-col gap-3 pointer-events-auto max-w-sm">
      {leakingNodes.map((n) => (
        <div
          key={n.id}
          className="bg-orange-700 text-white px-5 py-4 rounded-xl shadow-[0_10px_30px_rgba(255,120,0,0.5)] border-2 border-orange-400"
        >
          <h2 className="font-black text-base mb-1 flex items-center gap-2">
            <Flame className="text-yellow-300 w-5 h-5" /> KEBOCORAN GAS TERDETEKSI
          </h2>
          <p className="text-xs text-orange-100 mb-2">
            Node <span className="font-mono font-bold">{n.id}</span> - valve gas/air otomatis DITUTUP demi keamanan.
            {typeof n.gas_raw === 'number' && (
              <> Bacaan sensor: <span className="font-mono">{n.gas_raw}</span>.</>
            )}
          </p>
          <p className="text-[11px] text-orange-200 mb-3">
            Valve TIDAK akan terbuka otomatis walau bacaan sudah normal - pastikan area sudah aman sebelum membuka kembali.
          </p>
          <button
            onClick={() => {
              if (confirm(`Pastikan kebocoran gas di lokasi node ${n.id} sudah benar-benar aman sebelum membuka kembali valve-nya. Lanjutkan?`)) {
                sendCommand('enable_valve', n.id);
              }
            }}
            className="w-full flex justify-center items-center gap-2 bg-orange-900 hover:bg-orange-950 rounded-lg border border-orange-300 font-bold text-sm py-2 transition"
          >
            <Unlock size={14} /> Buka Kembali Valve
          </button>
        </div>
      ))}
    </div>
  );
}
