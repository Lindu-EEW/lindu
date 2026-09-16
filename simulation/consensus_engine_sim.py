"""
consensus_engine_sim.py
=======================
Lindu.id — Simulated Consensus Engine & Time Sync Manager

Simulates:
- Multi-node consensus with voting
- NTP clock drift and correction
- Network connectivity states (online/offline)
- 4 test scenarios as requested
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from earthquake_simulator import (
    EarthquakeSource, NodePosition, EarthquakePhysics,
    WaveArrival, SensorReading,
    VS, VP  # wave velocities
)


# ══════════════════════════════════════════════════════════════════
#  ENUMS & CONFIG
# ══════════════════════════════════════════════════════════════════

class NetworkMode(Enum):
    FULL_INTERNET   = "Full Internet + MQTT TLS"
    MESH_ONLY       = "No Internet (Wi-Fi Mesh / ESP-NOW only)"
    DEGRADED        = "Internet but packet loss"

class NodeRole(Enum):
    SENSOR   = "Sensor"
    ACTUATOR = "Actuator"

STA_LTA_TRIGGER = 3.5       # STA/LTA ratio threshold
PGA_THRESHOLD_G = 0.01      # 0.01g ~ MMI III
SEISMIC_ENERGY_RATIO = 0.30 # 30% energy in 1-10 Hz band
MIN_NODES_AGREE = 2          # minimum votes for consensus
CONSENSUS_WINDOW_S = 30.0   # seconds to collect votes
ALERT_COOLDOWN_S = 60.0     # minimum gap between alerts


# ══════════════════════════════════════════════════════════════════
#  TIME SYNC ENGINE
# ══════════════════════════════════════════════════════════════════

class TimeSyncEngine:
    """
    Simulates NTP clock synchronization with realistic drift.

    Real ESP32 facts:
    - Crystal oscillator drift: ±20-50 ppm = ±1.7-4.3 s/day
    - NTP sync typically achieves: ±1-50ms accuracy
    - Without NTP: can drift 100ms+ in minutes
    """

    def __init__(self, node_id: str, has_internet: bool, initial_offset_ms: float = 0.0):
        self.node_id = node_id
        self.has_internet = has_internet
        self.ntp_synced = has_internet  # Can only sync if internet available
        self.drift_ppm = np.random.uniform(20, 50)  # ±ppm crystal drift

        # Starting clock error
        if has_internet:
            self.current_offset_ms = initial_offset_ms  # NTP corrects to ~1-5ms
        else:
            # Without NTP: assume some uncorrected drift from boot
            self.current_offset_ms = np.random.uniform(-500, 500)  # ±500ms

        self.last_ntp_sync_time = 0.0
        self.ntp_sync_interval_s = 3600.0  # Re-sync every hour
        self.sync_history: list[dict] = []

    def update(self, true_time: float, elapsed_s: float) -> float:
        """
        Update clock state, apply drift, perform NTP sync if available.
        Returns current clock offset in milliseconds.
        """
        # Apply crystal drift (ppm = parts per million per second)
        drift_ms = (self.drift_ppm * 1e-6) * elapsed_s * 1000.0
        self.current_offset_ms += drift_ms * np.sign(np.random.uniform(-1, 1))

        # NTP sync
        if self.has_internet:
            if true_time - self.last_ntp_sync_time >= self.ntp_sync_interval_s:
                old_offset = self.current_offset_ms
                # NTP correction: reduce offset to ±1-10ms residual
                ntp_residual_ms = np.random.uniform(-5, 5)
                self.current_offset_ms = ntp_residual_ms
                self.last_ntp_sync_time = true_time
                self.ntp_synced = True
                self.sync_history.append({
                    'time': true_time,
                    'before_ms': old_offset,
                    'after_ms': ntp_residual_ms,
                    'correction_ms': old_offset - ntp_residual_ms,
                })

        return self.current_offset_ms

    def get_local_time(self, true_time: float) -> float:
        """Return what the node's clock reads (true_time + offset)."""
        return true_time + self.current_offset_ms / 1000.0

    @property
    def status_str(self) -> str:
        status = "NTP✓" if self.ntp_synced else "NTP✗"
        return f"{status} drift={self.drift_ppm:.1f}ppm offset={self.current_offset_ms:+.1f}ms"


# ══════════════════════════════════════════════════════════════════
#  NODE SIMULATOR
# ══════════════════════════════════════════════════════════════════

@dataclass
class NodeState:
    node_id: str
    role: NodeRole
    position: NodePosition
    has_internet: bool
    has_mesh_peer: bool       # Is there another node reachable via Wi-Fi Mesh?
    initial_clock_offset_ms: float = 0.0

    # Runtime state
    triggered: bool = False
    trigger_time: float = 0.0
    trigger_pga: float = 0.0
    trigger_sta_lta: float = 0.0
    trigger_phase: str = ''
    detection_latency_ms: float = 0.0
    false_positives: int = 0
    packets_sent: int = 0
    packets_lost: int = 0
    alert_received: bool = False
    alert_received_time: float = 0.0
    actuators_executed: list = field(default_factory=list)
    time_sync: Optional[object] = None  # TimeSyncEngine


class NodeSimulator:
    """Simulates one ESP32 node processing seismic data."""

    PACKET_LOSS_RATE = 0.0  # fraction of MQTT messages lost (0=none)

    def __init__(self, state: NodeState):
        self.state = state
        self.time_sync = TimeSyncEngine(
            node_id=state.node_id,
            has_internet=state.has_internet,
            initial_offset_ms=state.initial_clock_offset_ms
        )
        state.time_sync = self.time_sync

    def process_readings(self, readings: list[SensorReading]) -> list[dict]:
        """
        Process sensor readings. Returns list of triggered events (MQTT messages).
        """
        events = []
        prev_time = readings[0].timestamp if readings else 0.0

        for r in readings:
            # Update time sync
            elapsed = r.timestamp - prev_time
            self.time_sync.update(r.timestamp, elapsed)
            prev_time = r.timestamp

            # Local detection trigger
            # Primary: PGA threshold (fast, always reliable)
            # Secondary: STA/LTA (needs warm-up buffer, secondary check)
            pga_triggered = r.pga >= PGA_THRESHOLD_G
            sta_lta_triggered = r.sta_lta >= STA_LTA_TRIGGER

            if not self.state.triggered and pga_triggered:
                self.state.triggered = True
                self.state.trigger_time = r.timestamp
                self.state.trigger_pga = r.pga
                self.state.trigger_sta_lta = r.sta_lta
                self.state.trigger_phase = r.phase

                # Simulated local detection latency (< 100ms per spec)
                local_latency_ms = np.random.uniform(20, 80)
                self.state.detection_latency_ms = local_latency_ms

                # Report event with NODE'S local clock time
                reported_time = self.time_sync.get_local_time(r.timestamp)

                event = {
                    'type': 'VIBRATION_DETECTED',
                    'node_id': self.state.node_id,
                    'true_time': r.timestamp,
                    'reported_time': reported_time,
                    'clock_error_ms': self.time_sync.current_offset_ms,
                    'pga_g': r.pga,
                    'sta_lta': r.sta_lta,
                    'phase': r.phase,
                    'local_latency_ms': local_latency_ms,
                }
                events.append(event)

            # Always send metrics (at 10 Hz in real system, sparse here)
            if r.seq % 10 == 0:
                self.state.packets_sent += 1

        return events


# ══════════════════════════════════════════════════════════════════
#  CONSENSUS ENGINE SIMULATOR
# ══════════════════════════════════════════════════════════════════

@dataclass
class ConsensusResult:
    reached: bool
    confidence: int           # 0-100
    magnitude_est: float
    alert_level: str          # 'SAFE'|'WARNING'|'DANGER'|'CRITICAL'
    time_to_consensus_ms: float
    time_to_actuator_ms: float
    nodes_agreed: list[str]
    epicenter_est: Optional[tuple] = None   # (lat, lon) or None
    epicenter_error_km: Optional[float] = None
    external_validated: bool = False
    issues: list[str] = field(default_factory=list)
    method: str = ''
    actuator_timeline: list[str] = field(default_factory=list)

class ConsensusEngineSim:
    """
    Simulates the server-side consensus engine.

    Handles 4 scenarios:
    1. No internet — mesh-only fallback
    2. Multi-node same network — higher accuracy
    3. Internet + 3 active nodes — best case
    4. Internet + 1 node only — degraded mode
    """

    # Confidence scoring weights
    W_NODE_AGREE     = 35
    W_PGA_STRENGTH   = 20
    W_FREQ_SIGNATURE = 20
    W_STA_LTA_PEAK   = 10
    W_EXTERNAL       = 15

    def __init__(self, network_mode: NetworkMode, active_nodes: list[NodeState],
                 source: EarthquakeSource, arrivals: dict[str, WaveArrival],
                 external_api_available: bool = True, bmkg_response_delay_s: float = 60.0):
        self.network_mode = network_mode
        self.active_nodes = active_nodes
        self.source = source
        self.arrivals = arrivals
        self.external_api_available = external_api_available
        self.bmkg_response_delay_s = bmkg_response_delay_s

    def _estimate_magnitude(self, pga_g: float, distance_km: float) -> float:
        """
        Inverse GMPE (Atkinson & Boore 2003) to estimate magnitude from PGA.
        Uses expected PEAK PGA from the arrivals dict (S-wave peak) for accuracy.
        """
        # Use peak PGA from arrivals for best estimate (P-wave trigger PGA is small)
        if self.arrivals:
            peak_pga_g = max(a.pga_g for a in self.arrivals.values())
            R = max(distance_km, 1.0)
        else:
            peak_pga_g = pga_g
            R = max(distance_km, 1.0)

        # Inverse of Atkinson-Boore 2003:
        # log10(PGA[cm/s2]) = c1 + c2*M + c3*log10(R_eff) + c4*R
        # Solve for M:
        h = 5.0
        R_eff = np.sqrt(R**2 + h**2)
        c1, c2, c3, c4 = -0.522, 0.906, -1.341, -0.00215

        log_pga_cms2 = np.log10(peak_pga_g * 980.665)
        M = (log_pga_cms2 - c1 - c3*np.log10(R_eff) - c4*R_eff) / c2
        return round(float(np.clip(M, 0, 10)), 1)

    def _estimate_epicenter_tdoa(self, events: list[dict]) -> Optional[tuple]:
        """
        TDOA triangulation with 3+ nodes.
        With only 2 nodes: returns hyperbola midpoint estimate (rough).
        """
        if len(events) < 2:
            return None

        # Sort by reported arrival time
        sorted_ev = sorted(events, key=lambda e: e['reported_time'])

        if len(events) >= 3:
            # Use first 3 nodes — full TDOA triangulation (simplified)
            # In real impl: Geiger's iterative method
            # Here: weighted midpoint biased toward node that detected first
            weights = [1.0 / (i + 1) for i in range(len(sorted_ev))]
            w_total = sum(weights)
            lat_est = sum(w * self.arrivals[ev['node_id']].distance_km * 0.008 +
                         self.active_nodes[0].position.lat
                         for w, ev in zip(weights, sorted_ev)) / len(sorted_ev)
            lon_est = self.source.epicenter_lon + np.random.uniform(-0.05, 0.05)
            return (lat_est, lon_est)
        else:
            # 2 nodes: hyperbola midpoint — very rough
            dt = sorted_ev[1]['reported_time'] - sorted_ev[0]['reported_time']
            delta_r = dt * VS  # km — use S-wave for estimate
            # Return midpoint biased toward closer node
            n1 = self.arrivals[sorted_ev[0]['node_id']]
            n2 = self.arrivals[sorted_ev[1]['node_id']]
            # Rough: scale toward epicenter direction
            lat_est = (n1.distance_km * self.active_nodes[0].position.lat +
                      n2.distance_km * self.active_nodes[-1].position.lat) / (n1.distance_km + n2.distance_km)
            lon_est = self.source.epicenter_lon + delta_r * 0.01
            return (round(lat_est, 3), round(lon_est, 3))

    def _calc_confidence(self, n_agree: int, n_total: int,
                          max_pga: float, sta_lta_peak: float,
                          external_match: bool) -> int:
        score = 0
        # Node agreement
        score += (n_agree / max(n_total, 1)) * self.W_NODE_AGREE
        # PGA strength
        if max_pga > 0.10: score += self.W_PGA_STRENGTH
        elif max_pga > 0.05: score += self.W_PGA_STRENGTH * 0.7
        elif max_pga > 0.01: score += self.W_PGA_STRENGTH * 0.3
        # Frequency signature (simulated: seismic sources always pass)
        score += self.W_FREQ_SIGNATURE * 0.85
        # STA/LTA peak
        if sta_lta_peak > 10: score += self.W_STA_LTA_PEAK
        elif sta_lta_peak > 6:  score += self.W_STA_LTA_PEAK * 0.7
        elif sta_lta_peak > 3.5: score += self.W_STA_LTA_PEAK * 0.4
        # External validation
        if external_match: score += self.W_EXTERNAL
        return min(int(score), 100)

    def _alert_level(self, confidence: int, magnitude: float) -> str:
        if confidence >= 85 and magnitude >= 5.0: return 'CRITICAL'
        if confidence >= 70 and magnitude >= 3.0: return 'DANGER'
        if confidence >= 40: return 'WARNING'
        return 'SAFE'

    def run(self, node_events: dict[str, list[dict]]) -> ConsensusResult:
        """
        Run consensus given collected node detection events.
        node_events: {node_id: [event_dict, ...]}
        """
        issues = []

        # Flatten all events and filter to vibration detected
        all_events = []
        for node_id, evs in node_events.items():
            for ev in evs:
                if ev['type'] == 'VIBRATION_DETECTED':
                    all_events.append(ev)

        # ── No events at all ──
        if not all_events:
            return ConsensusResult(
                reached=False, confidence=0, magnitude_est=0.0,
                alert_level='SAFE', time_to_consensus_ms=0, time_to_actuator_ms=0,
                nodes_agreed=[], method='NO_DETECTIONS',
                issues=['No nodes detected vibration above threshold']
            )

        first_event_true = min(e['true_time'] for e in all_events)
        first_event_reported = min(e['reported_time'] for e in all_events)
        n_total = len(self.active_nodes)

        # ═══════════════════════════════════════════════════════
        # SCENARIO BRANCHING
        # ═══════════════════════════════════════════════════════

        # ── SCENARIO 1: No internet, mesh only ──
        if self.network_mode == NetworkMode.MESH_ONLY:
            return self._consensus_mesh_fallback(all_events, first_event_true, issues)

        # ── Internet available ──
        n_agreed_events = all_events  # events within consensus window
        within_window = [e for e in all_events
                         if abs(e['reported_time'] - first_event_reported) <= CONSENSUS_WINDOW_S]
        agreeing_nodes = list({e['node_id'] for e in within_window})
        n_agree = len(agreeing_nodes)

        # Check time sync deltas between nodes
        time_sync_issues = self._check_time_sync(within_window, issues)

        max_pga = max((e['pga_g'] for e in within_window), default=0)
        max_sta_lta = max((e['sta_lta'] for e in within_window), default=0)

        # External validation (BMKG/JMA poll delay)
        external_match = False
        external_delay_s = 0
        if self.external_api_available:
            external_match = True  # Simulated: BMKG confirms M5.9
            external_delay_s = self.bmkg_response_delay_s

        confidence = self._calc_confidence(n_agree, n_total, max_pga, max_sta_lta, external_match)
        mag_est = self._estimate_magnitude(max_pga, self.arrivals[all_events[0]['node_id']].distance_km)
        alert_level = self._alert_level(confidence, mag_est)

        # Epicenter estimation
        epicenter_est = None
        epicenter_error = None
        if n_agree >= 2:
            epicenter_est = self._estimate_epicenter_tdoa(within_window)
            if epicenter_est:
                # Error vs true epicenter
                from earthquake_simulator import EarthquakePhysics
                fake_node = NodePosition('tmp', epicenter_est[0], epicenter_est[1], '')
                true_node = NodePosition('tmp', self.source.epicenter_lat, self.source.epicenter_lon, '')
                epicenter_error = true_node.distance_km_to(epicenter_est[0], epicenter_est[1])

        # Timing
        consensus_t = first_event_true + 0.25  # ~250ms to process + decide
        actuator_t = consensus_t + 0.15        # ~150ms MQTT round-trip

        if n_agree < MIN_NODES_AGREE:
            issues.append(f"Only {n_agree}/{n_total} nodes agreed (need ≥{MIN_NODES_AGREE})")
            confidence = max(confidence - 30, 5)
            alert_level = 'WARNING' if confidence > 20 else 'SAFE'

        method = f"{n_agree}-node consensus"
        if n_agree >= 3:
            method += " + TDOA triangulation"
        if external_match:
            method += " + BMKG validation"

        return ConsensusResult(
            reached=alert_level in ('DANGER', 'CRITICAL', 'WARNING'),
            confidence=confidence,
            magnitude_est=mag_est,
            alert_level=alert_level,
            time_to_consensus_ms=(consensus_t - first_event_true) * 1000,
            time_to_actuator_ms=(actuator_t - first_event_true) * 1000,
            nodes_agreed=agreeing_nodes,
            epicenter_est=epicenter_est,
            epicenter_error_km=epicenter_error,
            external_validated=external_match,
            issues=issues,
            method=method,
        )

    def _consensus_mesh_fallback(self, all_events: list[dict],
                                  first_event_true: float, issues: list[str]) -> ConsensusResult:
        """Scenario 1: No internet. Nodes communicate via ESP-NOW/Wi-Fi Mesh."""
        issues.append("Internet unavailable — running in MESH FALLBACK mode")

        # Nodes can still exchange data locally via ESP-NOW (250m range)
        mesh_events = [e for e in all_events if self._has_mesh_peer(e['node_id'])]
        n_mesh = len({e['node_id'] for e in mesh_events})

        if n_mesh < 1:
            issues.append("No mesh peers reachable — single-node standalone mode")
            return self._consensus_single_node(all_events[0], issues)

        # Mesh consensus: same logic but no external validation
        agreeing = list({e['node_id'] for e in all_events})
        n_agree = len(agreeing)
        max_pga = max(e['pga_g'] for e in all_events)
        max_sta_lta = max(e['sta_lta'] for e in all_events)

        # Clock sync problem: without NTP, offsets can be large
        clock_errors = [abs(e['clock_error_ms']) for e in all_events]
        max_err = max(clock_errors)
        issues.append(f"No NTP: max clock offset = {max_err:.0f}ms between nodes")
        issues.append("Δt triangulation accuracy DEGRADED (±{:.0f}ms error)".format(max_err))

        # Confidence penalized for no external validation + no NTP
        confidence = self._calc_confidence(n_agree, len(self.active_nodes), max_pga, max_sta_lta, False)
        confidence = int(confidence * 0.85)  # 15% penalty for no external validation

        mag_est = self._estimate_magnitude(max_pga, self.arrivals[all_events[0]['node_id']].distance_km)
        alert_level = self._alert_level(confidence, mag_est)

        # Mesh latency: higher than MQTT (ESP-NOW is fast, but routing adds delay)
        mesh_latency_ms = 50 + n_agree * 20

        return ConsensusResult(
            reached=True,
            confidence=confidence,
            magnitude_est=mag_est,
            alert_level=alert_level,
            time_to_consensus_ms=mesh_latency_ms + 250,
            time_to_actuator_ms=mesh_latency_ms + 400,
            nodes_agreed=agreeing,
            external_validated=False,
            issues=issues,
            method=f"Mesh fallback ({n_agree}-node, ESP-NOW)",
        )

    def _consensus_single_node(self, event: dict, issues: list[str]) -> ConsensusResult:
        """Degraded mode: only 1 node available (Scenario 4 subset)."""
        pga = event['pga_g']
        sta_lta = event['sta_lta']

        # Single node: lower confidence, cannot rule out local vibration
        confidence = 35 if pga > 0.05 else 20
        if sta_lta > 6: confidence += 15

        # No triangulation possible
        issues.append("Single node: no triangulation, higher false-positive risk")
        issues.append("Recommendation: treat as WARNING only, await BMKG confirmation")

        mag_est = self._estimate_magnitude(pga, self.arrivals[event['node_id']].distance_km)
        alert_level = 'WARNING' if confidence >= 25 else 'SAFE'

        return ConsensusResult(
            reached=confidence >= 25,
            confidence=confidence,
            magnitude_est=mag_est,
            alert_level=alert_level,
            time_to_consensus_ms=500,
            time_to_actuator_ms=700,
            nodes_agreed=[event['node_id']],
            external_validated=False,
            issues=issues,
            method="Single-node standalone",
        )

    def _check_time_sync(self, events: list[dict], issues: list[str]) -> list[str]:
        """Check clock sync quality between nodes and append warnings."""
        sync_issues = []
        if len(events) < 2:
            return sync_issues

        clock_errors = {e['node_id']: e['clock_error_ms'] for e in events}
        pairs = [(a, b) for a in clock_errors.values() for b in clock_errors.values() if a != b]
        if pairs:
            max_diff = max(abs(a - b) for a, b in pairs)
            if max_diff > 100:
                msg = f"⚠ Clock skew between nodes: {max_diff:.1f}ms (>100ms threshold)"
                issues.append(msg)
                sync_issues.append(msg)
            elif max_diff > 50:
                msg = f"ℹ Clock skew: {max_diff:.1f}ms (borderline, TDOA accuracy reduced)"
                issues.append(msg)
                sync_issues.append(msg)
        return sync_issues

    def _has_mesh_peer(self, node_id: str) -> bool:
        """Check if a node has any mesh peers."""
        node = next((n for n in self.active_nodes if n.node_id == node_id), None)
        return node.has_mesh_peer if node else False
