import React, { useEffect, useRef, useMemo } from 'react';
import L from 'leaflet';
import { MapContainer, TileLayer, Marker, CircleMarker, Circle, Popup, Tooltip, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const isValidCoord = (lat, lon) =>
  typeof lat === 'number' && typeof lon === 'number' && Number.isFinite(lat) && Number.isFinite(lon);

export default function MapPanel({ activeNodes, focusedNode, displayQuake, quakeDatabase, userLat, userLon, flyToUserTrigger }) {
  const mapRef = useRef(null);

  const getDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371; 
    const dLat = (lat2 - lat1) * (Math.PI / 180);
    const dLon = (lon2 - lon1) * (Math.PI / 180);
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * (Math.PI / 180)) * Math.cos(lat2 * (Math.PI / 180)) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    return R * (2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a)));
  };

  useEffect(() => {
    if (mapRef.current && displayQuake && isValidCoord(userLat, userLon)) {
      const qLat = displayQuake.lat ?? displayQuake.epi_lat;
      const qLon = displayQuake.lon ?? displayQuake.epi_lon;
      if (!isValidCoord(qLat, qLon)) return;

      const dist_km = getDistance(userLat, userLon, qLat, qLon);
      const isSafe = dist_km > (displayQuake.radius_km || displayQuake.radius);

      if (!isSafe) {
          mapRef.current.flyToBounds([
            [userLat, userLon],
            [qLat, qLon]
          ], { padding: [50, 50], duration: 1.5 });
      }
    }
  }, [displayQuake, userLat, userLon]);

  useEffect(() => {
    if (flyToUserTrigger && mapRef.current && isValidCoord(userLat, userLon)) {
      mapRef.current.flyTo([userLat, userLon], 14, { duration: 1.5 });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [flyToUserTrigger]);

  useEffect(() => {
    if (focusedNode && activeNodes[focusedNode] && mapRef.current) {
      const { lat, lon } = activeNodes[focusedNode];
      if (isValidCoord(lat, lon)) {
        mapRef.current.flyTo([lat, lon], 12, { duration: 1.5 });
      }
    }
  }, [focusedNode, activeNodes]);

  // Aggregate all known nodes from history + active status, dropping any without valid coordinates
  const allKnownNodes = useMemo(() => {
    const nodes = { ...activeNodes };
    if (quakeDatabase) {
      quakeDatabase.forEach(q => {
        if (q.triggering_nodes) {
          q.triggering_nodes.forEach(n => {
            if (!nodes[n.id]) nodes[n.id] = { lat: n.lat, lon: n.lon };
          });
        }
      });
    }
    return Object.fromEntries(
      Object.entries(nodes).filter(([, data]) => isValidCoord(data?.lat, data?.lon))
    );
  }, [activeNodes, quakeDatabase]);

  return (
    <>
    

    <MapContainer 
      center={[userLat, userLon]} 
      zoom={10} 
      className="absolute inset-0 z-0 bg-gray-900"
      ref={mapRef}
      zoomControl={false}
    >
      <TileLayer
        url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
        attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
      />
      
      {/* User Marker */}
      <CircleMarker center={[userLat, userLon]} radius={6} color="#10b981" fillColor="#10b981" fillOpacity={1}>
        <Popup>Lokasi Anda</Popup>
      </CircleMarker>

{/* Geoshake Style: All Known Sensor Nodes */}
      {Object.entries(allKnownNodes).map(([nodeId, data]) => {
        // Find if this node is involved in the CURRENTLY selected/displayed quake
        const isTriggered = displayQuake?.triggering_nodes?.find(n => n.id === nodeId);
        let nodeColor = "#3b82f6"; // Default Blue (Standby)
        let nodeFillOpacity = 0.5;
        let nodeRadius = 6; // Bigger for easier clicking/hovering
        
        // Intensity Color Logic (Shindo/PGA scale approximation)
        if (isTriggered) {
          nodeFillOpacity = 1;
          nodeRadius = 8;
          if (isTriggered.pga > 0.5) nodeColor = "#ef4444"; // Red (Severe)
          else if (isTriggered.pga > 0.2) nodeColor = "#f97316"; // Orange (Strong)
          else nodeColor = "#eab308"; // Yellow (Moderate)
        }

        return (
          <CircleMarker 
            key={nodeId} 
            center={[data.lat, data.lon]} 
            radius={nodeRadius} 
            color="white" 
            weight={1}
            fillColor={nodeColor} 
            fillOpacity={nodeFillOpacity}
          >
            {/* HOVER TOOLTIP for instant interaction without clicking */}
            <Tooltip direction="top" offset={[0, -10]} opacity={0.9}>
              <div className="text-center font-sans">
                <div className="font-bold border-b border-gray-300 pb-1 mb-1">Sensor: {nodeId}</div>
                {isTriggered ? (
                  <div className="text-red-600 font-bold">PGA: {isTriggered.pga}G</div>
                ) : (
                  <div className="text-blue-600">Standby</div>
                )}
              </div>
            </Tooltip>
          </CircleMarker>
        );
      })}

      {/* Geoshake Style: Epicenter & S-Wave Radius */}
      {displayQuake && isValidCoord(
        displayQuake.lat ?? displayQuake.epi_lat,
        displayQuake.lon ?? displayQuake.epi_lon
      ) && (() => {
        const qLat = displayQuake.lat ?? displayQuake.epi_lat;
        const qLon = displayQuake.lon ?? displayQuake.epi_lon;
        return (
          <>
            {/* Animated Epicenter Pulse */}
            <Marker
              position={[qLat, qLon]}
              icon={L.divIcon({
                className: 'epicenter-icon',
                html: '<div class="epi-core"><div class="epi-ripple"></div></div>',
                iconSize: [24, 24],
                iconAnchor: [12, 12]
              })}
            />

            {/* S-Wave Danger Zone */}
            <Circle
              center={[qLat, qLon]}
              radius={(displayQuake.radius_km || displayQuake.radius || 0) * 1000}
              color="#ef4444" weight={1} fillColor="#ef4444" fillOpacity={0.10}
            />

            {/* Triangulation Beams */}
            {displayQuake.triggering_nodes?.filter(node => isValidCoord(node.lat, node.lon)).map(node => {
              const isSevere = node.pga > 0.5;
              return (
                <Polyline
                  key={node.id}
                  positions={[[node.lat, node.lon], [qLat, qLon]]}
                  color={isSevere ? "#ef4444" : "#fbbf24"}
                  weight={isSevere ? 3 : 2}
                  dashArray={isSevere ? "" : "6, 6"}
                  opacity={0.6}
                />
              );
            })}
          </>
        );
      })()}
    </MapContainer>
    </>
  );
}
