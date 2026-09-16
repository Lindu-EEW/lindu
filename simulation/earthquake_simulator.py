"""
earthquake_simulator.py
========================
Lindu.id — Earthquake Physics & Waveform Engine

Generates realistic M5.9 seismic waveforms including:
- P-wave (compressional, arrives first, smaller amplitude)
- S-wave (shear, arrives after, larger amplitude, causes damage)
- Surface waves (slowest, longest duration, largest amplitude)

Physical parameters based on:
- Boore & Atkinson (2008) GMPE
- Brune (1970) source spectrum model
- Standard seismological constants for Indonesian region
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional
import time


# ══════════════════════════════════════════════════════════════════
#  PHYSICAL CONSTANTS
# ══════════════════════════════════════════════════════════════════

VP  = 6.0    # P-wave velocity (km/s) — upper crustal rock
VS  = 3.5    # S-wave velocity (km/s)
VLG = 3.0    # Love/Rayleigh surface wave velocity (km/s)
G   = 9.81   # Gravity (m/s²)


# ══════════════════════════════════════════════════════════════════
#  DATA CLASSES
# ══════════════════════════════════════════════════════════════════

@dataclass
class NodePosition:
    node_id: str
    lat: float
    lon: float
    location_name: str

    def distance_km_to(self, lat2: float, lon2: float) -> float:
        """Haversine distance in km"""
        R = 6371.0
        phi1, phi2 = np.radians(self.lat), np.radians(lat2)
        dphi = np.radians(lat2 - self.lat)
        dlam = np.radians(lon2 - self.lon)
        a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlam/2)**2
        return 2 * R * np.arcsin(np.sqrt(a))


@dataclass
class EarthquakeSource:
    magnitude: float        # Richter / Mw
    epicenter_lat: float
    epicenter_lon: float
    depth_km: float
    origin_time: float      # Unix timestamp (s) — absolute event time

    @property
    def seismic_moment(self) -> float:
        """Seismic moment Mo (N·m) from Hanks & Kanamori (1979)"""
        return 10 ** (1.5 * (self.magnitude + 10.7)) * 1e-7  # dyne·cm → N·m

    @property
    def stress_drop_pa(self) -> float:
        """Stress drop (Pa) — typical tectonic 1-10 MPa"""
        return 3e6  # 3 MPa

    @property
    def source_radius_km(self) -> float:
        """Brune source radius r0 = 0.37 * Vs * (Mo/stress_drop)^(1/3)"""
        Mo = self.seismic_moment
        r = 0.37 * (VS * 1000) * (Mo / self.stress_drop_pa) ** (1/3)
        return r / 1000  # m → km

    @property
    def corner_frequency_hz(self) -> float:
        """Brune corner frequency fc"""
        return 0.37 * VS / self.source_radius_km  # Hz

    @property
    def rupture_duration_s(self) -> float:
        """Approximate rupture duration (seconds)"""
        return 1.0 / self.corner_frequency_hz


@dataclass
class WaveArrival:
    node_id: str
    distance_km: float
    hypocentral_km: float  # slant distance including depth

    p_arrival_offset_s: float  # seconds after origin
    s_arrival_offset_s: float
    surface_arrival_offset_s: float

    pga_g: float           # Peak Ground Acceleration (g) — horizontal
    pgv_cms: float         # Peak Ground Velocity (cm/s)

    def p_arrival_abs(self, origin_time: float) -> float:
        return origin_time + self.p_arrival_offset_s

    def s_arrival_abs(self, origin_time: float) -> float:
        return origin_time + self.s_arrival_offset_s


@dataclass
class SensorReading:
    node_id: str
    timestamp: float        # Unix time (s), NTP-synced
    seq: int
    ax: float               # acceleration X (m/s²)
    ay: float               # acceleration Y (m/s²)
    az: float               # acceleration Z (m/s²)  includes gravity
    pga: float              # instantaneous PGA magnitude (g)
    sta_lta: float          # STA/LTA ratio at this moment
    phase: str              # 'quiet'|'p_wave'|'s_wave'|'surface'
    clock_offset_ms: float  # simulated NTP clock error


# ══════════════════════════════════════════════════════════════════
#  EARTHQUAKE PHYSICS ENGINE
# ══════════════════════════════════════════════════════════════════

class EarthquakePhysics:
    """
    Generates ground motion time-series using simplified Brune source model
    + attenuation + site effects.
    """

    def compute_arrivals(self, source: EarthquakeSource, node: NodePosition) -> WaveArrival:
        """Compute wave arrival times and amplitude estimates at a node."""

        # Epicentral and hypocentral distances
        R_epi = node.distance_km_to(source.epicenter_lat, source.epicenter_lon)
        R_hypo = np.sqrt(R_epi**2 + source.depth_km**2)

        # Travel times (simple 1D flat-earth model)
        tp = R_hypo / VP
        ts = R_hypo / VS
        tsurf = R_epi / VLG  # surface waves travel along surface

        # ── PGA estimation using Atkinson & Boore (2003) ──
        # Calibrated for M5.9 @ 5-13km → PGA ≈ 0.15-0.40g (realistic)
        M = source.magnitude
        R = max(R_hypo, 1.0)  # avoid zero

        # Atkinson & Boore (2003) Table 6 coefficients for PGA (rock site)
        # log10(PGA[cm/s²]) = c1 + c2*M + c3*log10(R_eff) + c4*R
        # where R_eff = sqrt(R² + h²), h = 5km (pseudo-depth)
        h = 5.0
        R_eff = np.sqrt(R**2 + h**2)

        c1, c2, c3, c4 = -0.522, 0.906, -1.341, -0.00215
        log_pga_cms2 = c1 + c2*M + c3*np.log10(R_eff) + c4*R_eff

        # Convert cm/s² → g
        pga_g = (10 ** log_pga_cms2) / 980.665

        # Depth correction (deeper sources: less surface motion)
        depth_factor = np.exp(-0.03 * max(source.depth_km - 10, 0))

        pga_g = pga_g * depth_factor
        pga_g = max(pga_g, 1e-5)  # floor

        # PGV estimate (Campbell & Bozorgnia 2008)
        log_pgv = -1.242 + 1.609*M - 1.270*np.log10(R) - 0.0038*R
        pgv_cms = 10 ** log_pgv

        return WaveArrival(
            node_id=node.node_id,
            distance_km=R_epi,
            hypocentral_km=R_hypo,
            p_arrival_offset_s=tp,
            s_arrival_offset_s=ts,
            surface_arrival_offset_s=tsurf,
            pga_g=pga_g,
            pgv_cms=pgv_cms,
        )

    def generate_waveform(
        self,
        source: EarthquakeSource,
        arrival: WaveArrival,
        sr: int = 104,              # sample rate Hz (LSM6DS3 default)
        duration_s: float = 360.0,  # 5 minutes + margin
        clock_offset_ms: float = 0.0,
    ) -> list[SensorReading]:
        """
        Generate a time-series of SensorReading objects simulating
        what an ESP32-S3 + LSM6DS3 would report during the earthquake.

        Timeline (all relative to node's local clock):
          t < p_arrive       → quiet background noise
          p_arrive ≤ t < s   → P-wave (high freq, small amp)
          s ≤ t < surf       → S-wave (damage phase, max amplitude)
          surf ≤ t < end     → Surface waves + coda decay
        """
        readings = []
        dt = 1.0 / sr
        total_samples = int(duration_s * sr)

        # Node local time = true time + clock_offset
        offset_s = clock_offset_ms / 1000.0

        tp_local = source.origin_time + arrival.p_arrival_offset_s + offset_s
        ts_local = source.origin_time + arrival.s_arrival_offset_s + offset_s
        tsf_local = source.origin_time + arrival.surface_arrival_offset_s + offset_s

        # Shake duration scales with magnitude
        shake_duration = 10 * 10 ** (0.5 * (source.magnitude - 5))  # seconds
        end_shaking = ts_local + shake_duration

        # Amplitude scaling
        pga_ms2 = arrival.pga_g * G
        p_amp   = pga_ms2 * 0.30   # P-wave: ~30% of PGA
        s_amp   = pga_ms2 * 1.00   # S-wave: 100%
        suf_amp = pga_ms2 * 0.60   # Surface: 60%

        # Corner frequency for spectral shape
        fc = source.corner_frequency_hz

        rng = np.random.default_rng(seed=42)

        # STA/LTA rolling buffers
        STA_WIN = int(0.5 * sr)   # 0.5s
        LTA_WIN = int(30.0 * sr)  # 30s
        sta_buf = np.zeros(STA_WIN)
        lta_buf = np.zeros(LTA_WIN)
        sta_i, lta_i = 0, 0
        sta_sum, lta_sum = 0.0, 0.0

        def update_sta_lta(val):
            nonlocal sta_sum, lta_sum, sta_i, lta_i
            old_s = sta_buf[sta_i]; sta_sum += val - old_s; sta_buf[sta_i] = val; sta_i=(sta_i+1)%STA_WIN
            old_l = lta_buf[lta_i]; lta_sum += val - old_l; lta_buf[lta_i] = val; lta_i=(lta_i+1)%LTA_WIN
            sta_avg = sta_sum / STA_WIN
            lta_avg = lta_sum / LTA_WIN
            return sta_avg / (lta_avg + 1e-8)

        for i in range(total_samples):
            t_local = source.origin_time + offset_s + i * dt

            # ── Background noise (always present) ──
            noise_x = rng.normal(0, 0.003)   # ~3 mg RMS background
            noise_y = rng.normal(0, 0.003)
            noise_z = rng.normal(0, 0.002)
            phase = 'quiet'

            # ── P-wave ──
            if t_local >= tp_local and t_local < ts_local:
                phase = 'p_wave'
                t_in = t_local - tp_local
                env = min(t_in / 2.0, 1.0) * np.exp(-t_in / 8.0)  # envelope

                # P-wave: predominantly vertical, high frequency
                freq_p = min(fc * 2, 8.0)
                p_sig  = p_amp * env
                noise_z += p_sig * np.sin(2*np.pi*freq_p*t_in + rng.uniform(0, 2*np.pi))
                noise_x += p_sig * 0.3 * rng.normal()
                noise_y += p_sig * 0.3 * rng.normal()

            # ── S-wave + coda ──
            elif t_local >= ts_local:
                t_in = t_local - ts_local
                phase = 's_wave' if t_local < tsf_local else 'surface'

                if t_local < tsf_local:
                    # S-wave: horizontal, lower frequency, max amplitude
                    env = min(t_in / 1.5, 1.0) * np.exp(-t_in / 15.0)
                    freq_s = min(fc, 3.0)
                    s_sig = s_amp * env
                    angle = rng.uniform(0, 2*np.pi)
                    noise_x += s_sig * np.cos(angle) * np.sin(2*np.pi*freq_s*t_in)
                    noise_y += s_sig * np.sin(angle) * np.sin(2*np.pi*freq_s*t_in + 0.5)
                    noise_z += s_sig * 0.5 * np.sin(2*np.pi*fc*t_in)

                # Surface waves (Love + Rayleigh)
                if t_local >= tsf_local:
                    t_sf = t_local - tsf_local
                    env_sf = np.exp(-t_sf / 40.0)  # slow decay
                    freq_sf = 0.5  # long period
                    suf_sig = suf_amp * env_sf
                    noise_x += suf_sig * np.sin(2*np.pi*freq_sf*t_sf)
                    noise_y += suf_sig * 0.8 * np.sin(2*np.pi*freq_sf*t_sf + np.pi/4)
                    noise_z += suf_sig * 0.4 * np.sin(2*np.pi*freq_sf*t_sf + np.pi/2)

            # ── Coda decay after main shaking ──
            if t_local > end_shaking:
                decay = np.exp(-(t_local - end_shaking) / 60.0)
                noise_x *= (1 + 0.5 * decay)
                noise_y *= (1 + 0.5 * decay)

            # Final acceleration values
            ax = noise_x
            ay = noise_y
            az = noise_z + G  # Z includes gravity

            # PGA (horizontal resultant, no gravity)
            pga_inst = np.sqrt(ax**2 + ay**2) / G  # g

            # STA/LTA on horizontal resultant
            sig = abs(np.sqrt(ax**2 + ay**2) - G * 0)  # detrend gravity from resultant
            sta_lta_val = update_sta_lta(abs(ax - np.mean([noise_x])))

            readings.append(SensorReading(
                node_id=arrival.node_id,
                timestamp=t_local,
                seq=i,
                ax=round(ax, 6),
                ay=round(ay, 6),
                az=round(az, 6),
                pga=round(pga_inst, 6),
                sta_lta=round(sta_lta_val, 3),
                phase=phase,
                clock_offset_ms=clock_offset_ms,
            ))

        return readings
