import React, { useState } from 'react';
import { ChevronDown, Radio } from 'lucide-react';
import TelemetryChart from './TelemetryChart';

export default function HistorySidebar({ history, activeNodes, onSelectQuake, onFocusNode, onOpenDetail }) {
  const [activeTab, setActiveTab] = useState('history');

  return (
    <div className="bg-black/80 backdrop-blur-md border border-gray-700 rounded-xl flex flex-col shadow-2xl pointer-events-auto flex-1 overflow-hidden">
      
      {/* Tabs Header */}
      <div className="bg-gray-800 flex border-b border-gray-700">
        <button 
          onClick={() => setActiveTab('history')}
          className={`flex-1 py-3 text-sm font-bold text-center ${activeTab === 'history' ? 'bg-gray-700 text-blue-400 border-b-2 border-blue-400' : 'text-gray-400 hover:bg-gray-750'}`}
        >
          Riwayat Gempa
        </button>
        <button 
          onClick={() => setActiveTab('sensors')}
          className={`flex-1 py-3 text-sm font-bold text-center ${activeTab === 'sensors' ? 'bg-gray-700 text-green-400 border-b-2 border-green-400' : 'text-gray-400 hover:bg-gray-750'}`}
        >
          Stasiun Sensor
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-2 custom-scrollbar">
        {activeTab === 'sensors' ? (
          <div className="space-y-2">
            {Object.keys(activeNodes || {}).length === 0 ? (
              <p className="text-gray-500 text-center text-sm mt-4">Belum ada sensor yang menyala.</p>
            ) : (
              Object.entries(activeNodes).map(([nodeId, data]) => (
                <div key={nodeId} className="bg-gray-800 p-3 rounded-lg border border-gray-700 shadow-sm flex flex-col gap-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 cursor-pointer" onClick={() => onFocusNode(nodeId)}>
                      <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                      <strong className="text-gray-200 text-sm hover:text-blue-400 transition-colors">Sensor: {nodeId}</strong>
                    </div>
                    <button 
                      onClick={() => onOpenDetail(nodeId)}
                      className="text-xs bg-gray-700 hover:bg-gray-600 text-blue-400 px-2 py-1 rounded transition-colors"
                    >
                      Detail →
                    </button>
                  </div>
                  <div className="text-xs text-gray-500">
                    Posisi: {data.lat.toFixed(4)}, {data.lon.toFixed(4)}
                  </div>
                </div>
              ))
            )}
          </div>
        ) : history.length === 0 ? (
          <p className="text-gray-500 text-xs text-center mt-10">Belum ada data gempa.</p>
        ) : (
          history.map((q) => <HistoryItem key={q.id} q={q} onSelectQuake={() => onSelectQuake(q)} />)
        )}
      </div>
    </div>
  );
}

function HistoryItem({ q, onSelectQuake }) {
  const [isOpen, setIsOpen] = useState(false);

  const nodeLabel = q.is_external ? "Metrik Eksternal" : "Node Terlibat";
  const extBadge = q.is_external ? (
    <span className="bg-blue-600 text-white px-1.5 py-0.5 rounded text-[9px] ml-1">EXT</span>
  ) : null;

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 shadow-sm overflow-hidden flex flex-col">
      <div 
        className="p-3 cursor-pointer hover:bg-gray-750 flex items-center justify-between"
        onClick={() => {
          onSelectQuake();
          setIsOpen(!isOpen);
        }}
      >
        <div className="flex flex-col gap-1">
          <div className="flex items-center">
            <span className="text-white font-bold text-sm">Gempa M {q.magnitude}</span>
            {extBadge}
          </div>
          <span className="text-gray-400 text-[10px]">{q.time}</span>
        </div>
        <div className="flex items-center gap-2">
          {q.radius_km && <span className="bg-red-900/50 text-red-400 px-2 py-1 rounded-full text-[10px] font-bold">R: {Math.round(q.radius_km)} km</span>}
          <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </div>
      </div>
      
      {isOpen && (
        <div className="bg-gray-850 p-3 border-t border-gray-750 text-xs text-gray-300">
          <div className="mb-2">
            <span className="text-gray-500 block mb-1 uppercase text-[9px]">{nodeLabel}</span>
            <div className="grid grid-cols-2 gap-2 max-h-32 overflow-y-auto pr-1">
              {q.triggering_nodes?.map(n => (
                <div key={n.id} className="bg-gray-800 p-1.5 rounded flex flex-col">
                  <span className="font-bold text-blue-400 text-[10px] truncate">{n.id}</span>
                  <span className="text-gray-400 text-[9px]">PGA: {n.pga}G</span>
                </div>
              ))}
            </div>
          </div>
          {q.desc && <div className="text-[10px] text-gray-400 italic">"{q.desc}"</div>}
          <TelemetryChart quake={q} />
        </div>
      )}
    </div>
  );
}
