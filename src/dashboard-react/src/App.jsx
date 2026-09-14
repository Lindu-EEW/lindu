import React, { useState, useEffect } from 'react';
import { useMqtt } from './hooks/useMqtt';
import MapPanel from './components/MapPanel';
import TopOverlay from './components/TopOverlay';
import HistorySidebar from './components/HistorySidebar';
import AlarmBanner from './components/AlarmBanner';
import NodeDetailModal from './components/NodeDetailModal';
import CommandCenterPanel from './components/CommandCenterPanel';

function App() {
  const { isConnected, activeNodes, quakeDatabase, liveAlarm, setLiveAlarm, localMode, setLocalMode, sendCommand } = useMqtt();
  const [selectedQuake, setSelectedQuake] = useState(null);
  const [focusedNode, setFocusedNode] = useState(null);
  const [detailNode, setDetailNode] = useState(null);
  
  const [userLat, setUserLat] = useState(35.6895);
  const [userLon, setUserLon] = useState(139.6917);
  const [locationName, setLocationName] = useState("Tokyo, Japan");

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setUserLat(pos.coords.latitude);
          setUserLon(pos.coords.longitude);
        },
        () => {},
        { enableHighAccuracy: true, timeout: 5000 }
      );
    }
  }, []);

  useEffect(() => {
    fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${userLat}&lon=${userLon}&zoom=10`)
      .then(res => res.json())
      .then(data => {
        if (data && data.address) {
          const city = data.address.city || data.address.town || data.address.state || "Lokasi Tidak Diketahui";
          const country = data.address.country || "";
          setLocationName(`${city}, ${country}`);
        }
      })
      .catch(() => setLocationName("Lokasi Aktif"));
  }, [userLat, userLon]);

  return (
    <div className="relative w-full h-screen overflow-hidden bg-gray-900 font-sans antialiased text-white">
      <MapPanel 
        activeNodes={activeNodes} 
        focusedNode={focusedNode}
        displayQuake={liveAlarm || selectedQuake || (quakeDatabase.length > 0 ? quakeDatabase[0] : null)} 
        quakeDatabase={quakeDatabase} 
        userLat={userLat} 
        userLon={userLon} 
      />
      
      {/* Left Sidebar Layout */}
      <div className="absolute left-6 top-6 bottom-6 w-80 flex flex-col gap-4 z-[1000] pointer-events-none">
        <TopOverlay 
          isConnected={isConnected} 
          activeNodesCount={Object.keys(activeNodes).length} 
          locationName={locationName}
        />
        <HistorySidebar 
          history={quakeDatabase} 
          activeNodes={activeNodes}
          onSelectQuake={setSelectedQuake} 
          onFocusNode={setFocusedNode}
          onOpenDetail={setDetailNode}
        />
      </div>
      

      {/* Right Sidebar Layout */}
      <div className="absolute right-6 top-6 bottom-6 flex flex-col gap-4 z-[1000] pointer-events-none items-end">
        <CommandCenterPanel 
          activeNodes={activeNodes} 
          sendCommand={sendCommand} 
        />
      </div>
      
      <AlarmBanner 
        liveAlarm={liveAlarm} 
        userLat={userLat} 
        userLon={userLon} 
        onDismiss={() => setLiveAlarm(null)}
      />

      {detailNode && (
        <NodeDetailModal 
          nodeId={detailNode} 
          nodeData={activeNodes[detailNode]} 
          quakeDatabase={quakeDatabase} 
          onClose={() => setDetailNode(null)} 
        />
      )}
    </div>
  );
}

export default App;
