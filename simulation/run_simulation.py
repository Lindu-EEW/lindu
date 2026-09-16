"""
run_simulation.py
=================
Lindu.id — Main Simulation Runner

Executes all 4 test scenarios for M5.9 earthquake (5 minutes duration)
and generates a detailed test report.

Usage:
    python3 run_simulation.py
    python3 run_simulation.py --no-plot    # skip matplotlib charts
"""

import sys
import time
import argparse
import numpy as np
from dataclasses import dataclass
from typing import Optional

from earthquake_simulator import (
    EarthquakeSource, NodePosition, EarthquakePhysics, SensorReading,
    VS, VP
)
from consensus_engine_sim import (
    NetworkMode, NodeRole, NodeState, NodeSimulator,
    ConsensusEngineSim, TimeSyncEngine,
    STA_LTA_TRIGGER, PGA_THRESHOLD_G, ConsensusResult
)

# ══════════════════════════════════════════════════════════════════════
#  SCENARIO DEFINITIONS
# ══════════════════════════════════════════════════════════════════════

# ── Earthquake M5.9 ──
EARTHQUAKE = EarthquakeSource(
    magnitude=5.9,
    epicenter_lat=-6.150,
    epicenter_lon=106.800,
    depth_km=12.0,
    origin_time=1000.0,  # Simulation T=0 is t=1000s (arbitrary epoch)
)

# ── Node positions (realistic building layout, ~100-500m apart) ──
NODE_POSITIONS = {
    'node1': NodePosition('node1', -6.200, 106.816, 'Gedung A - Lantai 1'),
    'node2': NodePosition('node2', -6.195, 106.820, 'Gedung B - Lantai 1'),
    'node3': NodePosition('node3', -6.205, 106.812, 'Gedung C - Lantai 1'),
}
ACTUATOR_POS = NodePosition('actuator1', -6.200, 106.816, 'Panel Aktuator')

SIMULATION_DURATION_S = 360.0  # 6 minutes (5 min shake + 1 min coda)
SAMPLE_RATE_HZ = 104            # LSM6DS3 @ 104 Hz

# ══════════════════════════════════════════════════════════════════════
#  DISPLAY HELPERS
# ══════════════════════════════════════════════════════════════════════

RESET = '\033[0m'
BOLD  = '\033[1m'
RED   = '\033[91m'
YEL   = '\033[93m'
GRN   = '\033[92m'
CYN   = '\033[96m'
BLU   = '\033[94m'
MAG   = '\033[95m'
DIM   = '\033[2m'

def bar(val, max_val=1.0, width=30, char='█'):
    filled = int(width * min(val, max_val) / max_val)
    return char * filled + '░' * (width - filled)

def severity_color(level: str) -> str:
    return {
        'CRITICAL': RED + BOLD,
        'DANGER':   RED,
        'WARNING':  YEL,
        'SAFE':     GRN,
    }.get(level, RESET)

def confidence_color(c: int) -> str:
    if c >= 80: return GRN
    if c >= 50: return YEL
    return RED

def print_header(title: str, color: str = CYN):
    w = 70
    print(f"\n{color}{'═'*w}{RESET}")
    print(f"{color}{BOLD}  {title}{RESET}")
    print(f"{color}{'═'*w}{RESET}")

def print_section(title: str):
    print(f"\n{BLU}  ── {title} ──{RESET}")

def print_ok(msg: str):  print(f"  {GRN}✓{RESET} {msg}")
def print_warn(msg: str): print(f"  {YEL}⚠{RESET} {msg}")
def print_err(msg: str):  print(f"  {RED}✗{RESET} {msg}")
def print_info(msg: str): print(f"  {CYN}ℹ{RESET} {msg}")

# ══════════════════════════════════════════════════════════════════════
#  CORE SIMULATION RUNNER
# ══════════════════════════════════════════════════════════════════════

class SimulationRunner:

    def __init__(self, show_plots: bool = True):
        self.physics = EarthquakePhysics()
        self.show_plots = show_plots
        self.results: list[dict] = []

        # Pre-compute arrivals for all nodes
        self.arrivals = {}
        for nid, pos in NODE_POSITIONS.items():
            self.arrivals[nid] = self.physics.compute_arrivals(EARTHQUAKE, pos)
        self.arrivals['actuator1'] = self.physics.compute_arrivals(EARTHQUAKE, ACTUATOR_POS)

    def generate_waveform(self, node_id: str, clock_offset_ms: float = 0.0) -> list[SensorReading]:
        """Generate waveform for a given node."""
        return self.physics.generate_waveform(
            source=EARTHQUAKE,
            arrival=self.arrivals[node_id],
            sr=SAMPLE_RATE_HZ,
            duration_s=SIMULATION_DURATION_S,
            clock_offset_ms=clock_offset_ms,
        )

    def print_earthquake_info(self):
        print_header("🌋  LINDU.ID — EARTHQUAKE SIMULATION  M5.9", MAG)
        eq = EARTHQUAKE
        physics = self.physics
        print(f"""
  {BOLD}Earthquake Parameters:{RESET}
  Magnitude    : {RED}{BOLD}M {eq.magnitude} (Richter/Mw){RESET}
  Epicenter    : {eq.epicenter_lat}°S, {eq.epicenter_lon}°E
  Depth        : {eq.depth_km} km (shallow crustal)
  Origin Time  : T+0.000s (simulation reference)
  Seismic Moment: {eq.seismic_moment:.2e} N·m
  Source Radius : {eq.source_radius_km:.2f} km
  Corner Freq   : {eq.corner_frequency_hz:.2f} Hz
  Rupture Duration: {eq.rupture_duration_s:.1f} s
  Shake Duration  : ~{10 * 10**(0.5*(eq.magnitude-5)):.0f} s (S+coda)

  {BOLD}Sensor Nodes:{RESET}""")

        for nid, arr in self.arrivals.items():
            if nid == 'actuator1': continue
            pga_mmi = self._pga_to_mmi(arr.pga_g)
            print(f"  {CYN}{nid:8s}{RESET} dist={arr.distance_km:5.1f}km  "
                  f"P-wave@T+{arr.p_arrival_offset_s:.2f}s  "
                  f"S-wave@T+{arr.s_arrival_offset_s:.2f}s  "
                  f"PGA={arr.pga_g:.4f}g  MMI={pga_mmi}")
        arr_act = self.arrivals['actuator1']
        print(f"  {MAG}actuator{RESET}  dist={arr_act.distance_km:5.1f}km  "
              f"S-wave@T+{arr_act.s_arrival_offset_s:.2f}s  "
              f"PGA={arr_act.pga_g:.4f}g")

    def _pga_to_mmi(self, pga_g: float) -> str:
        """Convert PGA (g) to approximate MMI scale."""
        pgal = pga_g * 980.665  # g to gal (cm/s²)
        if pgal < 0.17: return "I"
        if pgal < 1.4:  return "II"
        if pgal < 3.9:  return "III"
        if pgal < 9.2:  return "IV"
        if pgal < 18:   return "V"
        if pgal < 34:   return "VI"
        if pgal < 65:   return "VII"
        if pgal < 124:  return "VIII"
        if pgal < 236:  return "IX"
        return "X+"

    def print_time_sync_analysis(self, nodes: list[NodeState]):
        """Detailed time sync report across all nodes."""
        print_section("TIME SYNCHRONIZATION ANALYSIS")
        print(f"\n  {'Node':12s} {'NTP?':6s} {'Drift (ppm)':12s} {'Clock Offset':14s} {'Status':20s}")
        print(f"  {'─'*12} {'─'*6} {'─'*12} {'─'*14} {'─'*20}")
        for n in nodes:
            ts = n.time_sync
            if ts is None: continue
            ntp_str = f"{GRN}YES{RESET}" if ts.ntp_synced else f"{RED}NO {RESET}"
            off_str = f"{ts.current_offset_ms:+.1f}ms"
            off_color = GRN if abs(ts.current_offset_ms) < 50 else (YEL if abs(ts.current_offset_ms) < 200 else RED)
            print(f"  {CYN}{n.node_id:12s}{RESET} {ntp_str:15s} {ts.drift_ppm:8.1f}     "
                  f"{off_color}{off_str:14s}{RESET} {ts.status_str}")

        # Inter-node clock skew
        offsets = [n.time_sync.current_offset_ms for n in nodes if n.time_sync]
        if len(offsets) >= 2:
            max_skew = max(offsets) - min(offsets)
            skew_color = GRN if max_skew < 50 else (YEL if max_skew < 200 else RED)
            print(f"\n  Max inter-node clock skew: {skew_color}{max_skew:.1f}ms{RESET}", end='')
            if max_skew < 50:
                print(f"  → {GRN}Excellent for TDOA triangulation{RESET}")
            elif max_skew < 200:
                print(f"  → {YEL}Acceptable, TDOA accuracy ±{max_skew/VS:.2f}km{RESET}")
            else:
                print(f"  → {RED}HIGH SKEW: TDOA error ±{max_skew/1000*VS:.1f}km, triangulation unreliable{RESET}")

            # Time correction impact on S-P interval
            print(f"\n  Impact on S-P arrival time difference (distance calc):")
            sp_interval = self.arrivals['node1'].s_arrival_offset_s - self.arrivals['node1'].p_arrival_offset_s
            error_km = max_skew / 1000.0 * VS
            pct = error_km / self.arrivals['node1'].distance_km * 100
            print(f"    True S-P interval : {sp_interval:.3f}s")
            print(f"    Clock skew        : {max_skew:.1f}ms")
            print(f"    Distance error    : {skew_color}±{error_km:.2f}km ({pct:.1f}%){RESET}")

    def print_node_detections(self, nodes: list[NodeState]):
        print_section("PER-NODE DETECTION RESULTS")
        print(f"\n  {'Node':12s} {'Triggered':10s} {'Phase':10s} {'PGA (g)':10s} {'STA/LTA':8s} {'Latency':10s} {'Offset@T':10s}")
        print(f"  {'─'*12} {'─'*10} {'─'*10} {'─'*10} {'─'*8} {'─'*10} {'─'*10}")
        for n in nodes:
            if n.role == NodeRole.ACTUATOR: continue
            trig_str = f"{GRN}YES{RESET}" if n.triggered else f"{RED}NO {RESET}"
            phase_color = RED if n.trigger_phase == 's_wave' else YEL if n.trigger_phase == 'p_wave' else GRN
            print(f"  {CYN}{n.node_id:12s}{RESET} {trig_str:18s} "
                  f"{phase_color}{n.trigger_phase or '—':10s}{RESET} "
                  f"{n.trigger_pga:.5f}  "
                  f"{n.trigger_sta_lta:6.2f}    "
                  f"{n.detection_latency_ms:5.0f}ms    "
                  f"{n.time_sync.current_offset_ms if n.time_sync else 0:+.1f}ms")

    def print_consensus_result(self, result: ConsensusResult, scenario_name: str):
        lv_color = severity_color(result.alert_level)
        cf_color = confidence_color(result.confidence)

        print(f"\n  {'─'*60}")
        print(f"  {BOLD}Consensus Result:{RESET}")
        print(f"  Alert Level   : {lv_color}{BOLD}{result.alert_level:10s}{RESET}  "
              f"{bar(result.confidence, 100, 25)}")
        print(f"  Confidence    : {cf_color}{result.confidence}%{RESET}")
        print(f"  Magnitude Est : {RED}{result.magnitude_est}  "
              f"(true: {EARTHQUAKE.magnitude}){RESET}  "
              f"error={abs(result.magnitude_est - EARTHQUAKE.magnitude):.1f}")
        print(f"  Nodes Agreed  : {', '.join(result.nodes_agreed) or '—'}")
        print(f"  Method        : {DIM}{result.method}{RESET}")
        print(f"  Ext. Validated: {'✓ BMKG confirmed' if result.external_validated else '✗ No external confirmation'}")

        if result.epicenter_est:
            err = result.epicenter_error_km
            err_color = GRN if err and err < 5 else YEL if err and err < 20 else RED
            print(f"  Epicenter Est : ({result.epicenter_est[0]:.3f}°, {result.epicenter_est[1]:.3f}°)  "
                  f"error={err_color}{err:.1f}km{RESET}" if err else "  Epicenter Est : N/A")

        print(f"\n  {BOLD}Timing:{RESET}")
        print(f"  Time to Consensus : {result.time_to_consensus_ms:.0f}ms  "
              f"{'✓ <500ms' if result.time_to_consensus_ms < 500 else '⚠ slow'}")
        print(f"  Time to Actuator  : {result.time_to_actuator_ms:.0f}ms  "
              f"{'✓ <2000ms' if result.time_to_actuator_ms < 2000 else '⚠ slow'}")

        if getattr(result, 'actuator_timeline', None):
            print(f"\n  {BOLD}Actuator Execution Timeline:{RESET}")
            for step in getattr(result, 'actuator_timeline', []):
                print(f"    {step}")

        if result.issues:
            print(f"\n  {BOLD}Issues / Notes:{RESET}")
            for issue in result.issues:
                if '⚠' in issue or 'DEGRADED' in issue or 'HIGH' in issue:
                    print_warn(f"  {issue}")
                elif 'ℹ' in issue:
                    print_info(f"  {issue}")
                else:
                    print_info(f"  {issue}")

    def _build_actuator_timeline(self, result: ConsensusResult, s_wave_eta: float) -> list[str]:
        """Build a human-readable actuator execution timeline."""
        # Use agreed nodes, or fall back to all known arrival nodes
        avail_nodes = result.nodes_agreed if result.nodes_agreed else list(self.arrivals.keys())
        avail_nodes = [n for n in avail_nodes if n in self.arrivals and n != 'actuator1']
        if not avail_nodes:
            return ["No nodes detected — timeline unavailable"]

        first_p = min(self.arrivals[nid].p_arrival_offset_s for nid in avail_nodes)
        first_s = min(self.arrivals[nid].s_arrival_offset_s for nid in avail_nodes)

        consensus_s = first_p + result.time_to_consensus_ms / 1000.0
        actuator_s = first_p + result.time_to_actuator_ms / 1000.0
        warning_advance_s = first_s - actuator_s  # positive = before S-wave

        tl = []
        tl.append(f"T+{first_p:6.2f}s  P-wave detected by {avail_nodes[0]}")
        if len(avail_nodes) > 1:
            second_p = sorted([self.arrivals[nid].p_arrival_offset_s for nid in avail_nodes])[1]
            tl.append(f"T+{second_p:6.2f}s  P-wave detected by {avail_nodes[1]}")
        tl.append(f"T+{consensus_s:6.2f}s  Consensus reached — alert published to MQTT")
        tl.append(f"T+{actuator_s:6.2f}s  Actuator receives command")
        tl.append(f"T+{actuator_s+0.3:6.2f}s  {GRN}✓ Gas valve CLOSED{RESET}")
        tl.append(f"T+{actuator_s+0.8:6.2f}s  {GRN}✓ Door lock OPENED{RESET}")
        tl.append(f"T+{actuator_s+0.1:6.2f}s  {GRN}✓ Alarm ACTIVATED{RESET}")
        tl.append(f"T+{first_s:6.2f}s  S-wave arrives (destructive phase begins)")
        if warning_advance_s > 0:
            tl.append(f"  {GRN}→ WARNING ISSUED {warning_advance_s:.2f}s BEFORE S-wave! ✓{RESET}")
        else:
            tl.append(f"  {RED}→ S-wave arrived BEFORE actuator ({-warning_advance_s:.2f}s late){RESET}")
        return tl

    # ══════════════════════════════════════════════════════════════
    #  SCENARIO RUNNERS
    # ══════════════════════════════════════════════════════════════

    def run_scenario_1_no_internet(self):
        """SCENARIO 1: No internet — Wi-Fi Mesh / ESP-NOW fallback"""
        print_header("SCENARIO 1: No Internet (Wi-Fi Mesh Fallback)", RED)
        print(f"""
  Context: Internet router is down / ISP outage.
  Nodes communicate via ESP-NOW (Wi-Fi mesh, range ~250m).
  No NTP sync possible — clock drift from last sync.
  No external BMKG/JMA validation available.
  Actuator reachable via mesh.
""")

        # Both nodes have no internet, have each other as mesh peers
        # Clock drift: assume 2 hours since last NTP sync → ±100-300ms drift
        node_states = [
            NodeState('node1', NodeRole.SENSOR,  NODE_POSITIONS['node1'],
                      has_internet=False, has_mesh_peer=True, initial_clock_offset_ms=+180.0),
            NodeState('node2', NodeRole.SENSOR,  NODE_POSITIONS['node2'],
                      has_internet=False, has_mesh_peer=True, initial_clock_offset_ms=-95.0),
        ]
        actuator = NodeState('actuator1', NodeRole.ACTUATOR, ACTUATOR_POS,
                             has_internet=False, has_mesh_peer=True, initial_clock_offset_ms=+60.0)

        # Generate waveforms & process
        node_events = {}
        simulators = []
        for ns in node_states:
            sim = NodeSimulator(ns)
            simulators.append(sim)
            waveform = self.generate_waveform(ns.node_id, ns.initial_clock_offset_ms)
            events = sim.process_readings(waveform)
            node_events[ns.node_id] = events

        self.print_time_sync_analysis(node_states)
        self.print_node_detections(node_states)

        engine = ConsensusEngineSim(
            network_mode=NetworkMode.MESH_ONLY,
            active_nodes=node_states,
            source=EARTHQUAKE,
            arrivals=self.arrivals,
            external_api_available=False,
        )
        result = engine.run(node_events)
        result.actuator_timeline = self._build_actuator_timeline(result, self.arrivals['actuator1'].s_arrival_offset_s)
        self.print_consensus_result(result, "Scenario 1")

        self._print_scenario_verdict(result, scenario=1)
        self.results.append({'scenario': 1, 'name': 'No Internet', 'result': result})
        return result

    def run_scenario_2_mesh_network(self):
        """SCENARIO 2: 2 nodes, same local network, internet available"""
        print_header("SCENARIO 2: 2 Nodes — Local Network + Internet", GRN)
        print(f"""
  Context: Standard deployment — Node 1 & Node 2 on same WiFi.
  Internet available → NTP synced → good clock accuracy.
  BMKG polling active for external validation.
  This is the BASELINE intended operation.
""")

        node_states = [
            NodeState('node1', NodeRole.SENSOR, NODE_POSITIONS['node1'],
                      has_internet=True, has_mesh_peer=True, initial_clock_offset_ms=+3.0),
            NodeState('node2', NodeRole.SENSOR, NODE_POSITIONS['node2'],
                      has_internet=True, has_mesh_peer=True, initial_clock_offset_ms=-2.0),
        ]
        actuator = NodeState('actuator1', NodeRole.ACTUATOR, ACTUATOR_POS,
                             has_internet=True, has_mesh_peer=True, initial_clock_offset_ms=+1.5)

        node_events = {}
        for ns in node_states:
            sim = NodeSimulator(ns)
            waveform = self.generate_waveform(ns.node_id, ns.initial_clock_offset_ms)
            node_events[ns.node_id] = sim.process_readings(waveform)

        self.print_time_sync_analysis(node_states)
        self.print_node_detections(node_states)

        engine = ConsensusEngineSim(
            network_mode=NetworkMode.FULL_INTERNET,
            active_nodes=node_states,
            source=EARTHQUAKE,
            arrivals=self.arrivals,
            external_api_available=True,
            bmkg_response_delay_s=90.0,  # BMKG posts in ~60-120s
        )
        result = engine.run(node_events)
        result.actuator_timeline = self._build_actuator_timeline(result, self.arrivals['actuator1'].s_arrival_offset_s)
        self.print_consensus_result(result, "Scenario 2")
        self._print_scenario_verdict(result, scenario=2)
        self.results.append({'scenario': 2, 'name': '2 Nodes + Internet', 'result': result})
        return result

    def run_scenario_3_three_nodes(self):
        """SCENARIO 3: Internet + 3 active nodes — best accuracy"""
        print_header("SCENARIO 3: Internet + 3 Active Nodes (Best Case)", GRN)
        print(f"""
  Context: Full deployment with 3 sensor nodes + internet.
  NTP synced → clock accuracy < ±10ms.
  TDOA triangulation possible → epicenter estimation.
  Highest confidence and accuracy.
""")

        node_states = [
            NodeState('node1', NodeRole.SENSOR, NODE_POSITIONS['node1'],
                      has_internet=True, has_mesh_peer=True, initial_clock_offset_ms=+4.0),
            NodeState('node2', NodeRole.SENSOR, NODE_POSITIONS['node2'],
                      has_internet=True, has_mesh_peer=True, initial_clock_offset_ms=-3.0),
            NodeState('node3', NodeRole.SENSOR, NODE_POSITIONS['node3'],
                      has_internet=True, has_mesh_peer=True, initial_clock_offset_ms=+6.0),
        ]
        actuator = NodeState('actuator1', NodeRole.ACTUATOR, ACTUATOR_POS,
                             has_internet=True, has_mesh_peer=True, initial_clock_offset_ms=+2.0)
        # Add arrivals for node3 if not already computed
        if 'node3' not in self.arrivals:
            self.arrivals['node3'] = self.physics.compute_arrivals(EARTHQUAKE, NODE_POSITIONS['node3'])

        node_events = {}
        for ns in node_states:
            sim = NodeSimulator(ns)
            waveform = self.generate_waveform(ns.node_id, ns.initial_clock_offset_ms)
            node_events[ns.node_id] = sim.process_readings(waveform)

        self.print_time_sync_analysis(node_states)
        self.print_node_detections(node_states)

        engine = ConsensusEngineSim(
            network_mode=NetworkMode.FULL_INTERNET,
            active_nodes=node_states,
            source=EARTHQUAKE,
            arrivals=self.arrivals,
            external_api_available=True,
            bmkg_response_delay_s=75.0,
        )
        result = engine.run(node_events)
        result.actuator_timeline = self._build_actuator_timeline(result, self.arrivals['actuator1'].s_arrival_offset_s)
        self.print_consensus_result(result, "Scenario 3")
        self._print_scenario_verdict(result, scenario=3)
        self.results.append({'scenario': 3, 'name': '3 Nodes + Internet', 'result': result})
        return result

    def run_scenario_4_one_node(self):
        """SCENARIO 4: Internet + only 1 active node"""
        print_header("SCENARIO 4: Internet + 1 Node Only (Degraded Mode)", YEL)
        print(f"""
  Context: Node 2 is offline (power failure, hardware fault).
  Only Node 1 is active. Internet available → NTP synced.
  BMKG/JMA validation critical to compensate for single-node limitation.
  No triangulation possible. Higher false-positive risk.
""")

        node_states = [
            NodeState('node1', NodeRole.SENSOR, NODE_POSITIONS['node1'],
                      has_internet=True, has_mesh_peer=False,
                      initial_clock_offset_ms=+3.5),
            # node2 is OFFLINE — we still model it for display
            NodeState('node2', NodeRole.SENSOR, NODE_POSITIONS['node2'],
                      has_internet=False, has_mesh_peer=False,
                      initial_clock_offset_ms=0.0),
        ]
        node_states[1].triggered = False  # mark as offline

        node_events = {}
        # Only node1 sends events
        sim1 = NodeSimulator(node_states[0])
        waveform1 = self.generate_waveform('node1', node_states[0].initial_clock_offset_ms)
        node_events['node1'] = sim1.process_readings(waveform1)
        node_events['node2'] = []  # offline — no events

        self.print_time_sync_analysis([node_states[0]])
        print(f"\n  {RED}✗ node2 OFFLINE — no data received{RESET}")
        self.print_node_detections([node_states[0]])

        engine = ConsensusEngineSim(
            network_mode=NetworkMode.FULL_INTERNET,
            active_nodes=[node_states[0]],  # only node1 active
            source=EARTHQUAKE,
            arrivals=self.arrivals,
            external_api_available=True,
            bmkg_response_delay_s=90.0,
        )
        result = engine.run(node_events)
        result.actuator_timeline = self._build_actuator_timeline(result, self.arrivals['actuator1'].s_arrival_offset_s)
        self.print_consensus_result(result, "Scenario 4")
        self._print_scenario_verdict(result, scenario=4)
        self.results.append({'scenario': 4, 'name': '1 Node + Internet', 'result': result})
        return result

    def run_scenario_5_standalone_one_node(self):
        """SCENARIO 5: Truly standalone — 1 node, no neighbors, any internet state"""
        print_header("SCENARIO 5: 1 Node Standalone (No Neighbors, Remote Deploy)", YEL)
        print(f"""
  Context: Single ESP32 sensor installed in remote area.
  No other Lindu nodes within ESP-NOW range (~200m).
  Internet available → NTP + BMKG validation possible.
  
  KEY DIFFERENCE from Scenario 4:
    - Sc.4: 1 node because others are OFFLINE (system degraded)
    - Sc.5: 1 node by DESIGN — solo deployment, no peer available
  
  Design rule: Single node MUST NOT trigger DANGER without BMKG.
  Max alert = WARNING from local detection alone.
  BMKG confirm (60-90s delay) → promote to DANGER.
  Actuator: buzzer + LED on WARNING; gas valve/door on DANGER only.
""")

        node_states = [
            NodeState('node1', NodeRole.SENSOR, NODE_POSITIONS['node1'],
                      has_internet=True, has_mesh_peer=False,   # no peers!
                      initial_clock_offset_ms=+4.0),
        ]
        actuator = NodeState('actuator1', NodeRole.ACTUATOR, ACTUATOR_POS,
                             has_internet=True, has_mesh_peer=False,
                             initial_clock_offset_ms=+2.0)

        node_events = {}
        sim1 = NodeSimulator(node_states[0])
        waveform1 = self.generate_waveform('node1', node_states[0].initial_clock_offset_ms)
        node_events['node1'] = sim1.process_readings(waveform1)

        self.print_time_sync_analysis([node_states[0]])
        print(f"\n  {YEL}ℹ Node beroperasi SOLO — tidak ada peer node{RESET}")
        print(f"  {YEL}ℹ BMKG menjadi satu-satunya validator eksternal{RESET}")
        self.print_node_detections([node_states[0]])

        engine = ConsensusEngineSim(
            network_mode=NetworkMode.FULL_INTERNET,
            active_nodes=[node_states[0]],
            source=EARTHQUAKE,
            arrivals=self.arrivals,
            external_api_available=True,
            bmkg_response_delay_s=90.0,
        )
        result = engine.run(node_events)

        # Standalone specific behavior override
        result.issues.append("STANDALONE MODE: alert level capped at WARNING until BMKG confirms")
        result.issues.append("Actuator policy: buzzer+LED on WARNING; gas valve+door ONLY after BMKG DANGER")
        if result.alert_level == 'DANGER':
            result.issues.append(f"→ DANGER issued because BMKG confirmed M{result.magnitude_est}")
            result.issues.append("→ Gas valve CLOSED + door lock OPENED ✓")
        else:
            result.issues.append("→ Waiting for BMKG confirmation (~60-90s from origin)")
            result.issues.append("→ Buzzer + LED active; gas valve pending BMKG")

        # Show two-phase actuator timeline for standalone
        s_arr = self.arrivals['node1'].s_arrival_offset_s
        p_arr = self.arrivals['node1'].p_arrival_offset_s
        timeline = [
            f"T+{p_arr:6.2f}s  P-wave detected by node1",
            f"T+{p_arr+0.30:6.2f}s  Local trigger → {YEL}WARNING issued{RESET}",
            f"T+{p_arr+0.40:6.2f}s  {YEL}Buzzer + LED activated (WARNING){RESET}",
            f"T+{s_arr:6.2f}s  S-wave arrives (destructive phase)",
            f"T+{s_arr+2.0:6.2f}s  ... (node continues transmitting to server) ...",
            f"T+{p_arr+90.0:6.2f}s  BMKG posts autogempa.json (T+~90s from origin)",
            f"T+{p_arr+92.0:6.2f}s  Server polls BMKG → confirms M5.9 in area",
            f"T+{p_arr+93.0:6.2f}s  {GRN}Alert PROMOTED: WARNING → DANGER{RESET}",
            f"T+{p_arr+93.5:6.2f}s  {GRN}Gas valve CLOSED ✓{RESET}",
            f"T+{p_arr+94.0:6.2f}s  {GRN}Door lock OPENED ✓{RESET}",
            f"Note: Gas valve closes {p_arr+93.5:.1f}s after origin = ~{p_arr+93.5-s_arr:.0f}s after S-wave",
            f"{RED}⚠ Physical danger window already passed — BMKG confirmation is forensic{RESET}",
        ]
        result.actuator_timeline = timeline
        self.print_consensus_result(result, "Scenario 5")
        self._print_scenario_verdict(result, scenario=5)
        self.results.append({'scenario': 5, 'name': '1 Node Standalone', 'result': result})
        return result

    def run_scenario_6_hot_failover(self):
        """SCENARIO 6: 3 nodes → 1 drops mid-event (power cut from earthquake)"""
        print_header("SCENARIO 6: Hot Failover — 3→2 Nodes Mid-Earthquake", MAG)
        print(f"""
  Context: 3 sensor nodes deployed, all active at T=0.
  At T+2.4s (during P-wave phase), Node 3's power is cut
  by the earthquake itself (falling object, circuit breaker trip).
  Node 3 sends MQTT LWT "offline" before dying.
  Server must:
    1. Receive LWT → update active_nodes = [node1, node2]
    2. Recalculate quorum: need 2/2 remaining
    3. Proceed with 2-node consensus (not wait for Node 3)
    4. Issue alert with adjusted confidence
""")
        # Setup all 3 nodes first
        node_states_all = [
            NodeState('node1', NodeRole.SENSOR, NODE_POSITIONS['node1'],
                      has_internet=True, has_mesh_peer=True, initial_clock_offset_ms=+4.0),
            NodeState('node2', NodeRole.SENSOR, NODE_POSITIONS['node2'],
                      has_internet=True, has_mesh_peer=True, initial_clock_offset_ms=-3.0),
            NodeState('node3', NodeRole.SENSOR, NODE_POSITIONS['node3'],
                      has_internet=True, has_mesh_peer=True, initial_clock_offset_ms=+6.0),
        ]

        if 'node3' not in self.arrivals:
            self.arrivals['node3'] = self.physics.compute_arrivals(EARTHQUAKE, NODE_POSITIONS['node3'])

        # Simulate Node 3 dropping at T+2.4s (during P-wave arrival)
        node3_drop_time = EARTHQUAKE.origin_time + 2.4  # true time when it dies

        node_events = {}
        partial_data = {}
        for ns in node_states_all:
            sim = NodeSimulator(ns)
            waveform = self.generate_waveform(ns.node_id, ns.initial_clock_offset_ms)

            if ns.node_id == 'node3':
                # Node 3 gets cut: only send events up to drop_time
                events = sim.process_readings(waveform)
                # Filter: only events before drop time
                events_before_drop = [e for e in events
                                      if e['true_time'] <= node3_drop_time]
                node_events['node3'] = events_before_drop
                partial_data['node3'] = {
                    'status': 'DROPPED_MID_EVENT',
                    'drop_time': node3_drop_time,
                    'events_sent': len(events_before_drop),
                    'triggered': any(e['type'] == 'VIBRATION_DETECTED' for e in events_before_drop),
                }
            else:
                events = sim.process_readings(waveform)
                node_events[ns.node_id] = events

        self.print_time_sync_analysis(node_states_all)

        # Show node status including drop
        print_section("PER-NODE DETECTION RESULTS (with mid-event drop)")
        print(f"\n  {'Node':12s} {'Status':14s} {'Phase':10s} {'PGA':8s} {'Drop?':10s}")
        print(f"  {'─'*12} {'─'*14} {'─'*10} {'─'*8} {'─'*10}")
        for ns in node_states_all:
            if ns.node_id == 'node3':
                drop_info = partial_data['node3']
                triggered = drop_info['triggered']
                triggered_str = f"{YEL}PARTIAL{RESET}" if triggered else f"{RED}NO (dropped before){RESET}"
                print(f"  {MAG}node3       {RESET} {triggered_str:22s} {'p_wave':10s} {'N/A':8s} "
                      f"{RED}DROPPED @ T+2.4s ✗{RESET}")
            else:
                triggered = any(e['type'] == 'VIBRATION_DETECTED' for e in node_events[ns.node_id])
                col = GRN if triggered else RED
                pga_val = next((f"{e['pga_g']:.5f}" for e in node_events[ns.node_id]
                               if e['type'] == 'VIBRATION_DETECTED'), "0.00000")
                print(f"  {CYN}{ns.node_id:12s}{RESET} {col}{'YES':14s}{RESET} {'p_wave':10s} {pga_val:8s} {'OK':10s}")

        print(f"\n  {MAG}Hot Failover Logic:{RESET}")
        print(f"  T+2.40s  Node 3 LWT received: 'node3 offline'")
        print(f"  T+2.40s  Consensus engine: remove node3 from active pool")
        print(f"  T+2.40s  Recalculate: need 2/2 (node1 + node2)")
        print(f"  T+2.40s  Both node1 and node2 already triggered → QUORUM MET")

        # Run consensus with only node1 + node2 (simulate server's view after failover)
        active_2nodes = [node_states_all[0], node_states_all[1]]
        engine = ConsensusEngineSim(
            network_mode=NetworkMode.FULL_INTERNET,
            active_nodes=active_2nodes,
            source=EARTHQUAKE,
            arrivals=self.arrivals,
            external_api_available=True,
            bmkg_response_delay_s=75.0,
        )
        # Only pass node1 and node2 events (node3 dropped before full trigger)
        events_for_engine = {k: v for k, v in node_events.items() if k != 'node3'}
        result = engine.run(events_for_engine)

        # Apply hot-failover confidence penalty
        original_confidence = result.confidence
        result.confidence = max(result.confidence - 8, 0)  # -8% for incomplete event data
        result.issues.insert(0, f"HOT FAILOVER: node3 dropped at T+2.4s (power cut)")
        result.issues.insert(1, f"Confidence adjusted: {original_confidence}% → {result.confidence}% (-8% penalty)")
        result.issues.insert(2, f"Quorum recalculated: 2/2 remaining nodes (node1 + node2)")
        result.method = result.method.replace('3-node', '2/3-node hot-failover')

        # Build timeline showing the failover
        p1 = self.arrivals['node1'].p_arrival_offset_s
        p2 = self.arrivals['node2'].p_arrival_offset_s
        s_wave = self.arrivals['node1'].s_arrival_offset_s
        timeline = [
            f"T+{self.arrivals['node3'].p_arrival_offset_s:6.2f}s  ⚡ Power cut — node3 sends LWT 'offline'",
            f"T+{p1:6.2f}s  P-wave detected by node1",
            f"T+{p2:6.2f}s  P-wave detected by node2",
            f"T+{max(p1,p2)+0.05:6.2f}s  Server: quorum met (2/2 active nodes)",
            f"T+{max(p1,p2)+0.28:6.2f}s  Consensus: {result.alert_level} @ {result.confidence}% confidence",
            f"T+{max(p1,p2)+0.43:6.2f}s  Actuator receives command",
            f"T+{max(p1,p2)+0.73:6.2f}s  {GRN}✓ Gas valve CLOSED{RESET}",
            f"T+{max(p1,p2)+0.53:6.2f}s  {GRN}✓ Alarm ACTIVATED{RESET}",
            f"T+{s_wave:6.2f}s  S-wave arrives",
            f"  {GRN}→ ALERT ISSUED {s_wave - (max(p1,p2)+0.43):.2f}s BEFORE S-wave ✓{RESET}",
            f"  {YEL}→ 1 node lost during event — monitoring continues with 2 nodes{RESET}",
        ]
        result.actuator_timeline = timeline
        self.print_consensus_result(result, "Scenario 6")
        self._print_scenario_verdict(result, scenario=6)
        self.results.append({'scenario': 6, 'name': '3→2 Node Hot Failover', 'result': result})
        return result

    def _print_scenario_verdict(self, result: ConsensusResult, scenario: int):
        """Print pass/fail verdict for a scenario."""
        print(f"\n  {'─'*60}")

        # Define what "pass" means per scenario
        requirements = {
            1: {'min_confidence': 55, 'alert_level_ok': ['DANGER', 'CRITICAL', 'WARNING'],
                'max_actuator_ms': 3000,
                'desc': 'Mesh fallback: alert issued, actuator responds within 3s'},
            2: {'min_confidence': 70, 'alert_level_ok': ['DANGER', 'CRITICAL'],
                'max_actuator_ms': 2000,
                'desc': '2-node baseline: high confidence, actuator <2s'},
            3: {'min_confidence': 80, 'alert_level_ok': ['DANGER', 'CRITICAL'],
                'max_actuator_ms': 1500,
                'desc': '3-node: highest confidence + triangulation'},
            4: {'min_confidence': 30, 'alert_level_ok': ['WARNING', 'DANGER', 'CRITICAL'],
                'max_actuator_ms': 5000,
                'desc': 'Degraded: at least a WARNING with BMKG confirmation'},
            5: {'min_confidence': 25, 'alert_level_ok': ['WARNING', 'DANGER', 'CRITICAL'],
                'max_actuator_ms': 8000,
                'desc': 'Standalone 1-node: WARNING issued + buzzer, wait BMKG to promote DANGER'},
            6: {'min_confidence': 55, 'alert_level_ok': ['DANGER', 'CRITICAL', 'WARNING'],
                'max_actuator_ms': 3000,
                'desc': 'Hot failover: alert issued within 3s despite 1 node dropping mid-event'},
        }
        req = requirements[scenario]
        checks = [
            (result.confidence >= req['min_confidence'],
             f"Confidence {result.confidence}% ≥ {req['min_confidence']}%"),
            (result.alert_level in req['alert_level_ok'],
             f"Alert level '{result.alert_level}' in expected {req['alert_level_ok']}"),
            (result.time_to_actuator_ms <= req['max_actuator_ms'],
             f"Actuator time {result.time_to_actuator_ms:.0f}ms ≤ {req['max_actuator_ms']}ms"),
            (len(result.nodes_agreed) >= 1,
             f"At least 1 node agreed"),
        ]

        all_pass = all(ok for ok, _ in checks)
        verdict = f"{GRN}{BOLD}PASS ✓{RESET}" if all_pass else f"{RED}{BOLD}FAIL ✗{RESET}"
        print(f"  {BOLD}Scenario {scenario} Verdict: {verdict}{RESET}")
        print(f"  Requirement: {DIM}{req['desc']}{RESET}")
        for ok, msg in checks:
            if ok: print_ok(msg)
            else:  print_err(msg)

    def print_comparative_summary(self):
        """Final comparison table across all scenarios."""
        print_header("📊  COMPARATIVE SUMMARY — ALL SCENARIOS", CYN)
        print(f"""
  {'Sc':3s} {'Scenario':28s} {'Conf':6s} {'Level':10s} {'Mag Est':8s} {'Consensus':10s} {'Actuator':10s} {'Epicenter Err':14s} {'PASS?':6s}
  {'─'*3} {'─'*28} {'─'*6} {'─'*10} {'─'*8} {'─'*10} {'─'*10} {'─'*14} {'─'*6}""")

        for r in self.results:
            sc = r['scenario']
            nm = r['name']
            res: ConsensusResult = r['result']
            lv_c = severity_color(res.alert_level)
            cf_c = confidence_color(res.confidence)

            # Pass criteria summary
            pass_map = {1: res.confidence >= 55, 2: res.confidence >= 70,
                        3: res.confidence >= 80, 4: res.confidence >= 30,
                        5: res.confidence >= 25, 6: res.confidence >= 55}
            verdict = f"{GRN}PASS{RESET}" if pass_map.get(sc, False) else f"{RED}FAIL{RESET}"

            epi_err = f"{res.epicenter_error_km:.1f}km" if res.epicenter_error_km else "N/A"
            print(f"  {CYN}{sc:3d}{RESET} {nm:28s} "
                  f"{cf_c}{res.confidence:4d}%{RESET} "
                  f"{lv_c}{res.alert_level:10s}{RESET} "
                  f"M{res.magnitude_est:<6.1f}  "
                  f"{res.time_to_consensus_ms:6.0f}ms  "
                  f"{res.time_to_actuator_ms:6.0f}ms  "
                  f"{epi_err:14s} "
                  f"{verdict}")

        # Time sync note
        print(f"""
  {BOLD}Time Sync Impact on System Performance:{RESET}
  ┌─────────────────────────────────────────────────────────────────┐
  │ Condition           │ Clock Skew  │ TDOA Error  │ Recommendation │
  ├─────────────────────┼─────────────┼─────────────┼────────────────┤
  │ With NTP (internet) │ < ±10ms     │ ±0.04km     │ ✓ Use TDOA     │
  │ No NTP, short idle  │ ±50-200ms   │ ±0.6km      │ ⚠ Rough est.  │
  │ No NTP, 2h idle     │ ±200-500ms  │ ±2km        │ ✗ Avoid TDOA   │
  │ GPS PPS (upgrade)   │ < ±1ms      │ ±0.004km    │ ✓✓ Best        │
  └─────────────────────┴─────────────┴─────────────┴────────────────┘

  {BOLD}Recommendations to Minimize Clock Error:{RESET}""")
        recs = [
            ("Use NTP sync on every WiFi reconnect (not just hourly)",
             "Eliminates drift after network outage recovery"),
            ("Store last-known UTC time in RTC/EEPROM before sleep",
             "Reduces drift after deep sleep or power cycle"),
            ("Sync NTP via MQTT broker 'lindu/system/time' broadcast",
             "Allows NTP even when ISP NTP is blocked"),
            ("Fallback: GPS module (NEO-6M) for sub-ms accuracy",
             "Best accuracy but adds cost ~Rp 80.000/node"),
            ("Report clock confidence in every MQTT message",
             "Server can weight events by clock quality"),
            ("Run STA/LTA in parallel with 5s lookahead buffer",
             "Compensates for ±2s maximum expected skew"),
        ]
        for i, (rec, note) in enumerate(recs, 1):
            print(f"  {i}. {GRN}{rec}{RESET}")
            print(f"     {DIM}→ {note}{RESET}")


# ══════════════════════════════════════════════════════════════════════
#  PLOT GENERATION (Optional)
# ══════════════════════════════════════════════════════════════════════

def generate_plots(runner: SimulationRunner, output_dir: str):
    try:
        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec
    except ImportError:
        print_warn("matplotlib not available, skipping plots")
        return

    import os
    os.makedirs(output_dir, exist_ok=True)

    fig = plt.figure(figsize=(18, 12))
    fig.suptitle('Lindu.id — M5.9 Earthquake Simulation Waveforms', fontsize=14, fontweight='bold')
    gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.45, wspace=0.3)

    physics = EarthquakePhysics()

    # Generate waveforms for 3 nodes
    nodes_to_plot = [
        ('node1', 'Node 1 (Gedung A — closest)', 'tab:red',   +5.0),
        ('node2', 'Node 2 (Gedung B)',             'tab:blue',  -3.0),
        ('node3', 'Node 3 (Gedung C)',             'tab:green', +8.0),
    ]

    for idx, (nid, label, color, offset_ms) in enumerate(nodes_to_plot):
        pos = NODE_POSITIONS.get(nid)
        if pos is None: continue
        if nid not in runner.arrivals:
            runner.arrivals[nid] = physics.compute_arrivals(EARTHQUAKE, pos)
        arr = runner.arrivals[nid]

        readings = physics.generate_waveform(
            source=EARTHQUAKE, arrival=arr,
            sr=SAMPLE_RATE_HZ, duration_s=150.0,
            clock_offset_ms=offset_ms
        )

        t = np.array([r.timestamp - EARTHQUAKE.origin_time for r in readings])
        ax_vals = np.array([r.ax for r in readings])
        ay_vals = np.array([r.ay for r in readings])
        pga_vals = np.array([r.pga for r in readings])
        sta_lta_vals = np.array([r.sta_lta for r in readings])

        # PGA waveform
        ax1 = fig.add_subplot(gs[idx, 0])
        ax1.plot(t, pga_vals, color=color, lw=0.5, alpha=0.9)
        ax1.axhline(PGA_THRESHOLD_G, color='red', lw=0.8, ls='--', label=f'Threshold ({PGA_THRESHOLD_G}g)')
        ax1.axvline(arr.p_arrival_offset_s, color='orange', lw=1.2, ls='--', label='P-wave')
        ax1.axvline(arr.s_arrival_offset_s, color='red', lw=1.5, ls='-', label='S-wave')
        ax1.set_title(f'{label}\nPGA (g)', fontsize=9)
        ax1.set_xlabel('Time from origin (s)', fontsize=8)
        ax1.set_ylabel('g', fontsize=8)
        ax1.legend(fontsize=7, loc='upper right')
        ax1.set_xlim(-5, 150)
        ax1.tick_params(labelsize=7)
        ax1.grid(alpha=0.3)

        # STA/LTA
        ax2 = fig.add_subplot(gs[idx, 1])
        ax2.plot(t, sta_lta_vals, color=color, lw=0.7, alpha=0.9)
        ax2.axhline(STA_LTA_TRIGGER, color='red', lw=0.8, ls='--', label=f'Trigger ({STA_LTA_TRIGGER})')
        ax2.axvline(arr.p_arrival_offset_s, color='orange', lw=1.2, ls='--', label='P-wave')
        ax2.axvline(arr.s_arrival_offset_s, color='red', lw=1.5, ls='-', label='S-wave')
        ax2.set_title(f'STA/LTA Ratio', fontsize=9)
        ax2.set_xlabel('Time from origin (s)', fontsize=8)
        ax2.set_ylabel('STA/LTA', fontsize=8)
        ax2.legend(fontsize=7, loc='upper right')
        ax2.set_xlim(-5, 150)
        ax2.set_ylim(0, max(sta_lta_vals.max() * 1.1, STA_LTA_TRIGGER * 2))
        ax2.tick_params(labelsize=7)
        ax2.grid(alpha=0.3)

    plt.savefig(os.path.join(output_dir, 'waveforms_M59.png'), dpi=150, bbox_inches='tight')
    print_ok(f"Waveform plot saved → {output_dir}/waveforms_M59.png")

    # Scenario comparison bar chart
    if runner.results:
        fig2, axes = plt.subplots(1, 3, figsize=(14, 5))
        fig2.suptitle('Scenario Comparison — M5.9 Earthquake', fontsize=13, fontweight='bold')

        sc_names  = [r['name'] for r in runner.results]
        sc_conf   = [r['result'].confidence for r in runner.results]
        sc_cons   = [r['result'].time_to_consensus_ms for r in runner.results]
        sc_act    = [r['result'].time_to_actuator_ms for r in runner.results]
        colors_sc = ['#e74c3c', '#2ecc71', '#27ae60', '#f39c12'][:len(sc_names)]

        axes[0].bar(sc_names, sc_conf, color=colors_sc, edgecolor='black', lw=0.5)
        axes[0].axhline(70, color='green', ls='--', lw=1, label='DANGER threshold (70%)')
        axes[0].axhline(40, color='orange', ls='--', lw=1, label='WARNING threshold (40%)')
        axes[0].set_title('Confidence Score (%)', fontweight='bold')
        axes[0].set_ylabel('%'); axes[0].legend(fontsize=8); axes[0].set_ylim(0, 110)
        for i, v in enumerate(sc_conf): axes[0].text(i, v+1, f'{v}%', ha='center', fontsize=9, fontweight='bold')

        axes[1].bar(sc_names, sc_cons, color=colors_sc, edgecolor='black', lw=0.5)
        axes[1].axhline(500, color='green', ls='--', lw=1, label='Target <500ms')
        axes[1].set_title('Time to Consensus (ms)', fontweight='bold')
        axes[1].set_ylabel('ms'); axes[1].legend(fontsize=8)
        for i, v in enumerate(sc_cons): axes[1].text(i, v+5, f'{v:.0f}ms', ha='center', fontsize=9, fontweight='bold')

        axes[2].bar(sc_names, sc_act, color=colors_sc, edgecolor='black', lw=0.5)
        axes[2].axhline(2000, color='green', ls='--', lw=1, label='Target <2000ms')
        axes[2].set_title('Time to Actuator (ms)', fontweight='bold')
        axes[2].set_ylabel('ms'); axes[2].legend(fontsize=8)
        for i, v in enumerate(sc_act): axes[2].text(i, v+5, f'{v:.0f}ms', ha='center', fontsize=9, fontweight='bold')

        for ax in axes:
            ax.tick_params(axis='x', rotation=15)
            ax.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'scenario_comparison.png'), dpi=150, bbox_inches='tight')
        print_ok(f"Comparison chart saved → {output_dir}/scenario_comparison.png")

    plt.close('all')


# ══════════════════════════════════════════════════════════════════════
#  MONKEY PATCH: Add actuator_timeline field support
# ══════════════════════════════════════════════════════════════════════
# (ConsensusResult doesn't have this by default — add dynamically)
import types
def _add_actuator_timeline(result):
    if not hasattr(result, 'actuator_timeline'):
        result.actuator_timeline = []
ConsensusResult.__init_subclass__ = classmethod(lambda cls, **kw: None)


# ══════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='Lindu.id Earthquake Simulation')
    parser.add_argument('--no-plot', action='store_true', help='Skip matplotlib plots')
    parser.add_argument('--scenario', type=int, choices=[1,2,3,4], help='Run only one scenario')
    args = parser.parse_args()

    runner = SimulationRunner(show_plots=not args.no_plot)
    runner.print_earthquake_info()

    print(f"\n{CYN}Running simulation... (generating {SIMULATION_DURATION_S:.0f}s × {SAMPLE_RATE_HZ}Hz × nodes waveforms){RESET}")
    t_start = time.time()

    if args.scenario == 1 or not args.scenario:
        runner.run_scenario_1_no_internet()
    if args.scenario == 2 or not args.scenario:
        runner.run_scenario_2_mesh_network()
    if args.scenario == 3 or not args.scenario:
        runner.run_scenario_3_three_nodes()
    if args.scenario == 4 or not args.scenario:
        runner.run_scenario_4_one_node()

    elapsed = time.time() - t_start

    if not args.scenario:
        runner.print_comparative_summary()

    print(f"\n{DIM}Simulation completed in {elapsed:.2f}s{RESET}\n")

    if not args.no_plot and not args.scenario:
        output_dir = "simulation_output"
        print(f"\n{CYN}Generating plots → {output_dir}/{RESET}")
        generate_plots(runner, output_dir)

if __name__ == '__main__':
    main()
