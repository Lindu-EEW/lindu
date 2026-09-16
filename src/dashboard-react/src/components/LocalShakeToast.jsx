import React, { useEffect, useState } from 'react';

const TOAST_DURATION_MS = 4000;

export default function LocalShakeToast({ events }) {
  const [visible, setVisible] = useState([]);

  useEffect(() => {
    if (events.length === 0) return;
    const latest = events[events.length - 1];

    setVisible((prev) => [...prev, latest]);
    const timer = setTimeout(() => {
      setVisible((prev) => prev.filter((e) => e.id !== latest.id));
    }, TOAST_DURATION_MS);

    return () => clearTimeout(timer);
  }, [events]);

  if (visible.length === 0) return null;

  return (
    <div className="fixed top-6 left-1/2 -translate-x-1/2 z-[2000] flex flex-col items-center gap-2 pointer-events-none">
      {visible.map((e) => (
        <div
          key={e.id}
          className="bg-pink-600/95 text-white px-5 py-2.5 rounded-lg shadow-xl font-semibold text-sm flex items-center gap-2 animate-pulse"
        >
          <span className="text-lg">⚡</span>
          <span>
            <span className="font-bold">{e.nodeId}</span> mendeteksi guncangan (PGA: {e.pga.toFixed(2)}G)
          </span>
        </div>
      ))}
    </div>
  );
}
