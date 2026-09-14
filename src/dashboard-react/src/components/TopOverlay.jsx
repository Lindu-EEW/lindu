import React from 'react';

export default function TopOverlay({ isConnected, activeNodesCount, locationName }) {
  return (
    <div className="bg-black/80 p-5 rounded-xl border border-gray-700 pointer-events-auto shadow-xl flex-shrink-0">
        <h1 className="text-3xl font-black text-orange-500 tracking-wider flex items-center gap-2">
          <span className="text-red-500 text-4xl">∿</span> LINDU.ID <span className="text-gray-400 text-sm font-normal">COMMAND CENTER</span>
        </h1>
        <div className="mt-3 space-y-1">
          <p className="text-gray-400 text-sm">
            Lokasi: <span className="text-white font-bold">{locationName || "Mendeteksi..."}</span>
          </p>
          <p className="text-gray-400 text-sm">
            MQTT Link: <span className={`font-bold ${isConnected ? 'text-green-400' : 'text-yellow-400'}`}>
              {isConnected ? 'ONLINE' : 'Menyambungkan...'}
            </span>
          </p>
          <p className="text-gray-400 text-sm">
            Sensor Aktif: <span className="text-green-400 font-bold text-lg">{activeNodesCount}</span>
          </p>
        </div>
        
      </div>
  );
}
