"""
simulate_tdoa_scale.py
======================
Simulates the impact of Node Density (3, 5, 10, 50 nodes) on Earthquake
Epicenter Triangulation (TDOA) accuracy.

Uses scipy.optimize to solve the hyperbolic TDOA equations.
"""

import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import time

# Wave velocity
VP = 6.0  # km/s (P-wave speed in crust)

# True Earthquake
TRUE_LAT = -6.150
TRUE_LON = 106.800
TRUE_DEPTH = 12.0
TRUE_T0 = 100.0

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlam = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlam/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))

def generate_nodes(n_nodes, center_lat=-6.200, center_lon=106.810, spread=0.05):
    """Generate random node locations around Jakarta."""
    lats = center_lat + np.random.uniform(-spread, spread, n_nodes)
    lons = center_lon + np.random.uniform(-spread, spread, n_nodes)
    return list(zip(lats, lons))

def simulate_arrivals(nodes, clock_skew_ms=10.0):
    """Simulate P-wave arrival times at each node with clock skew."""
    arrivals = []
    for lat, lon in nodes:
        dist_epi = haversine(lat, lon, TRUE_LAT, TRUE_LON)
        dist_hypo = np.sqrt(dist_epi**2 + TRUE_DEPTH**2)
        travel_time = dist_hypo / VP
        
        # Add clock sync error (e.g. NTP ±10ms)
        err = np.random.normal(0, clock_skew_ms / 1000.0)
        arrival_t = TRUE_T0 + travel_time + err
        arrivals.append(arrival_t)
    return arrivals

def estimate_epicenter(nodes, arrivals):
    """Solve TDOA using scipy optimization (Geiger-like)."""
    # Initial guess (center of network, T0 = earliest arrival - 2s)
    g_lat = np.mean([n[0] for n in nodes])
    g_lon = np.mean([n[1] for n in nodes])
    g_t0 = min(arrivals) - 2.0
    
    def loss(guess):
        lat_g, lon_g, t0_g = guess
        err_sq = 0
        for (n_lat, n_lon), arr_t in zip(nodes, arrivals):
            d = np.sqrt(haversine(lat_g, lon_g, n_lat, n_lon)**2 + TRUE_DEPTH**2)
            exp_t = t0_g + (d / VP)
            err_sq += (exp_t - arr_t)**2
        return err_sq
    
    res = minimize(loss, [g_lat, g_lon, g_t0], method='Nelder-Mead')
    return res.x[0], res.x[1]

def run_scale_test():
    scales = [3, 5, 10, 50]
    errors = []
    
    print("\n--- TDOA Node Density Accuracy Test ---")
    print(f"True Epicenter: {TRUE_LAT}, {TRUE_LON}")
    
    plt.figure(figsize=(10, 8))
    
    colors = ['red', 'orange', 'blue', 'green']
    
    for i, n in enumerate(scales):
        # Generate network
        nodes = generate_nodes(n)
        arrivals = simulate_arrivals(nodes, clock_skew_ms=15.0) # 15ms NTP error
        
        # Solve
        est_lat, est_lon = estimate_epicenter(nodes, arrivals)
        err_km = haversine(TRUE_LAT, TRUE_LON, est_lat, est_lon)
        errors.append(err_km)
        
        print(f"Nodes: {n:2d} | Est: {est_lat:.4f}, {est_lon:.4f} | Error: {err_km:6.2f} km")
        
        # Plot
        plt.subplot(2, 2, i+1)
        # Plot true
        plt.scatter(TRUE_LON, TRUE_LAT, marker='*', color='red', s=200, label='True Epicenter')
        # Plot nodes
        n_lons = [x[1] for x in nodes]
        n_lats = [x[0] for x in nodes]
        plt.scatter(n_lons, n_lats, color='gray', s=20, alpha=0.5, label='Nodes')
        # Plot estimate
        plt.scatter(est_lon, est_lat, marker='X', color=colors[i], s=100, label=f'Estimate (Err: {err_km:.1f}km)')
        
        plt.title(f"{n} Nodes")
        plt.legend(fontsize=8)
        plt.grid(True, alpha=0.3)
        plt.axis('equal')
        
    plt.tight_layout()
    plt.savefig('tdoa_scale.png', dpi=150)
    print("\nPlot saved to tdoa_scale.png")

if __name__ == '__main__':
    np.random.seed(42)
    run_scale_test()
