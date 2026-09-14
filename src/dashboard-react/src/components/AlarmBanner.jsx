import React, { useEffect, useState } from 'react';
import { Shield, TriangleAlert, SatelliteDish } from 'lucide-react';

export default function AlarmBanner({ liveAlarm, userLat, userLon, onDismiss }) {
  const [eta, setEta] = useState(0);

  // Simple haversine for distance check
  const getDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371; 
    const dLat = (lat2 - lat1) * (Math.PI / 180);
    const dLon = (lon2 - lon1) * (Math.PI / 180);
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * (Math.PI / 180)) * Math.cos(lat2 * (Math.PI / 180)) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    return R * (2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a)));
  };

  // Safe destructuring for hooks
  const lat = liveAlarm ? liveAlarm.epi_lat : 0;
  const lon = liveAlarm ? liveAlarm.epi_lon : 0;
  const rad = liveAlarm ? liveAlarm.radius_km : 0;
  const ts = liveAlarm ? liveAlarm.timestamp : 0;

  const dist_km = liveAlarm ? getDistance(userLat, userLon, lat, lon) : 0;
  const isSafe = liveAlarm ? (dist_km > rad) : true;

  useEffect(() => {
    if (!liveAlarm || isSafe) return;
    let currentEta = dist_km / 3.5;
    setEta(currentEta);
    const interval = setInterval(() => {
      currentEta -= 0.1;
      if (currentEta <= 0) {
        setEta(0);
        clearInterval(interval);
      } else {
        setEta(currentEta);
      }
    }, 100);
    return () => clearInterval(interval);
  }, [dist_km, isSafe, ts, liveAlarm]);

  if (!liveAlarm) return null;

  if (isSafe) {
    return null;
  }

  // Danger Mode
  return (
    <>
      <div className="absolute inset-0 z-[999] pointer-events-none bg-red-600/20 animate-pulse mix-blend-overlay"></div>
      <div className="absolute top-8 left-1/2 transform -translate-x-1/2 z-[1000] bg-red-700 text-white px-10 py-6 rounded-2xl shadow-[0_10px_40px_rgba(255,0,0,0.6)] border-4 border-red-400 text-center w-[90%] max-w-2xl pointer-events-auto">
        <h1 className="text-3xl font-black mb-2 flex items-center justify-center gap-3">
          {liveAlarm.is_external ? (
            <><SatelliteDish className="text-cyan-300 w-8 h-8" /> PERINGATAN DINI ({liveAlarm.source}) <SatelliteDish className="text-cyan-300 w-8 h-8" /></>
          ) : (
            <><TriangleAlert className="text-yellow-300 w-8 h-8" /> PERINGATAN DINI GEMPA <TriangleAlert className="text-yellow-300 w-8 h-8" /></>
          )}
        </h1>
        <p className="text-lg mb-4">{liveAlarm.desc}</p>
        <div className="bg-black/40 p-4 rounded-xl border border-red-500 flex justify-between items-center mb-4">
          <div>
            <p className="text-sm text-red-300 uppercase font-bold tracking-wider mb-1">GELOMBANG MERUSAK TIBA DALAM:</p>
            <p className={`text-4xl font-mono font-bold ${eta <= 0 ? 'text-red-500' : 'text-white'}`}>
              {eta <= 0 ? '🚨 TIBA! 🚨' : `${eta.toFixed(1)}s`}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-red-300">Estimasi Kekuatan:</p>
            <p className="text-3xl font-black text-orange-400">M {liveAlarm.magnitude}</p>
            <p className="text-xs text-red-200 mt-1">Jarak Anda: {dist_km.toFixed(1)} km</p>
          </div>
        </div>
        <button onClick={onDismiss} className="px-6 py-2 bg-red-900 hover:bg-red-800 rounded-lg border border-red-400 font-bold text-sm transition shadow-lg">Abaikan Peringatan / Reset</button>
      </div>
    </>
  );
}
