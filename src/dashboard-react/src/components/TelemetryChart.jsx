import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import { Activity } from 'lucide-react';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Tooltip,
  Legend
);

export default function TelemetryChart({ quake }) {
  const seriesData = quake.telemetry_series;

  if (!seriesData || Object.keys(seriesData).length === 0) {
    if (!quake.triggering_nodes || quake.triggering_nodes.length === 0) {
      return (
        <div className="h-40 flex items-center justify-center text-gray-500 text-sm">
          <Activity className="w-5 h-5 mr-2 animate-pulse" /> Menunggu telemetri...
        </div>
      );
    }
    
    // FALLBACK: Historical PGA Bar Chart
    const barData = {
      labels: quake.triggering_nodes.map(n => n.id),
      datasets: [{
        label: 'Peak Ground Acceleration (G)',
        data: quake.triggering_nodes.map(n => n.pga),
        backgroundColor: 'rgba(239, 68, 68, 0.6)',
        borderColor: 'rgb(239, 68, 68)',
        borderWidth: 1
      }]
    };
    
    return (
      <div className="h-48 mt-3 w-full bg-black/40 rounded-lg p-2 border border-gray-700">
        <h4 className="text-xs text-center text-gray-400 mb-2">Distribusi Getaran Maksimum (PGA)</h4>
        <Bar 
          data={barData}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              y: { grid: { color: '#374151' }, ticks: { color: '#9ca3af', font: { size: 9 } } },
              x: { grid: { display: false }, ticks: { color: '#9ca3af', font: { size: 8 } } }
            },
            plugins: { legend: { display: false } }
          }}
        />
      </div>
    );
  }

  // Jika ada Telemetri Live (Grafik Garis)
  const nodeIds = Object.keys(seriesData);
  const maxLength = Math.max(...nodeIds.map((id) => seriesData[id].length));

  const colors = ['#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4'];

  const data = {
    labels: Array.from({ length: maxLength }, (_, i) => `T+${i + 1}s`),
    datasets: nodeIds.map((id, index) => ({
      label: id,
      data: seriesData[id],
      borderColor: colors[index % colors.length],
      backgroundColor: colors[index % colors.length] + '40',
      borderWidth: 2,
      pointRadius: 1,
      tension: 0.3,
    })),
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 0 },
    scales: {
      y: {
        beginAtZero: true,
        grid: { color: '#374151' },
        ticks: { color: '#9ca3af', font: { size: 9 } },
        title: { display: true, text: 'G-Force (PGA)', color: '#6b7280', font: { size: 10 } }
      },
      x: {
        grid: { display: false },
        ticks: { color: '#9ca3af', font: { size: 9 }, maxTicksLimit: 10 }
      }
    },
    plugins: {
      legend: {
        display: Object.keys(seriesData).length <= 5,
        labels: { color: 'white', font: { size: 8 }, boxWidth: 10 }
      }
    }
  };

  return (
    <div className="h-48 mt-3 w-full bg-black/40 rounded-lg p-2 border border-gray-700">
      <Line data={data} options={options} />
    </div>
  );
}
