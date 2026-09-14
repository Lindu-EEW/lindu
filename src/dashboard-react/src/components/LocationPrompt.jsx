import React from 'react';
import { MapPin, AlertCircle, Navigation } from 'lucide-react';

export default function LocationPrompt({ onRequest, onUseDefault, isLoading, error }) {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-900 text-white p-4">
      <div className="bg-black/60 p-8 rounded-2xl border border-gray-700 shadow-2xl max-w-lg w-full text-center backdrop-blur-md">
        <div className="flex justify-center mb-6">
          <div className="bg-orange-500/20 p-4 rounded-full border border-orange-500/50">
            <MapPin className="w-12 h-12 text-orange-400" />
          </div>
        </div>
        
        <h1 className="text-3xl font-black text-white tracking-wider mb-2">
          LINDU.ID <span className="text-orange-500 text-lg align-middle">OPS</span>
        </h1>
        
        <p className="text-gray-300 mb-8 text-sm leading-relaxed">
          Sistem Peringatan Dini Gempa (EEWS) memerlukan lokasi Anda saat ini untuk menghitung secara presisi jarak dan waktu tiba (ETA) gelombang mematikan sebelum mengguncang bangunan Anda.
        </p>

        {error && (
          <div className="bg-red-900/40 border border-red-500 text-red-200 p-3 rounded-lg text-xs mb-6 flex items-start gap-2 text-left">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <p>{error}</p>
          </div>
        )}

        <div className="flex flex-col gap-3">
          <button 
            onClick={onRequest}
            disabled={isLoading}
            className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-4 rounded-lg flex items-center justify-center gap-2 transition disabled:opacity-50"
          >
            {isLoading ? (
              <span className="animate-pulse">Mengunci Satelit GPS...</span>
            ) : (
              <><Navigation className="w-5 h-5" /> Deteksi Lokasi Saya Sekarang</>
            )}
          </button>
          
          {error && (
            <button 
              onClick={onUseDefault}
              className="w-full bg-gray-700 hover:bg-gray-600 text-white font-bold py-3 px-4 rounded-lg transition"
            >
              Gunakan Lokasi Simulasi (Jakarta)
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
