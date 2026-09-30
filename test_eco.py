import sys
import json
import asyncio

from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

from backend.graph_model import CityNetwork
from backend.distance_provider import HaversineProvider
from backend.qpso import QPSOOptimizer

def run_test():
    # 1. Create a synthetic network
    network = CityNetwork(num_nodes=36, congestion_mode="normal", seed=42)
    
    # 3-node asymmetric scenario to prove divergence
    # Depot = 0, A = 1, B = 2
    # Fastest prefers 0 -> 1 -> 2 -> 0 (time 30) over 0 -> 2 -> 1 -> 0 (time 50)
    # Greenest prefers 0 -> 2 -> 1 -> 0 because B has massive demand (100) and dropping it early saves emissions!
    
    start_node = 0
    stop_nodes = [1, 2]
    demands = {
        1: 1,    # Node A: light package
        2: 100   # Node B: heavy package
    }
    
    # Asymmetric duration matrix (seconds)
    dur_mat = [
        [0, 10, 20],  # 0->1 is 10, 0->2 is 20
        [20, 0, 10],  # 1->0 is 20, 1->2 is 10
        [10, 10, 0],  # 2->0 is 10, 2->1 is 10
    ]
    
    # Symmetric distance matrix (meters) - all legs are 10km
    dist_mat = [
        [0, 10000, 10000],
        [10000, 0, 10000],
        [10000, 10000, 0],
    ]
    
    print("--- ICE Vehicle ---")
    
    # Fastest
    qpso_fast = QPSOOptimizer(
        cost_matrix=dur_mat, distance_matrix=dist_mat,
        stop_nodes=stop_nodes, start_node=start_node, demands=demands,
        vehicle_capacity=150, num_particles=30, max_iterations=100,
        routing_preference="fastest", vehicle_type="ice", seed=100
    )
    res_fast = qpso_fast.optimize()
    print("FASTEST ROUTE:", res_fast["best_route"])
    print(f"Time: {res_fast['raw_cost']:.1f}s, Emissions: {res_fast['emissions_g']:.1f}g")
    
    # Greenest
    qpso_green = QPSOOptimizer(
        cost_matrix=dur_mat, distance_matrix=dist_mat,
        stop_nodes=stop_nodes, start_node=start_node, demands=demands,
        vehicle_capacity=150, num_particles=30, max_iterations=100,
        routing_preference="greenest", vehicle_type="ice", seed=100
    )
    res_green = qpso_green.optimize()
    print("GREENEST ROUTE:", res_green["best_route"])
    print(f"Time: {res_green['raw_cost']:.1f}s, Emissions: {res_green['emissions_g']:.1f}g")

if __name__ == "__main__":
    run_test()
