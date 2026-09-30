import time
import math
from typing import List, Dict, Any
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import random
from backend.graph_model import CityNetwork
from backend.baselines import ClassicalPSOOptimizer, GeneticAlgorithmOptimizer
try:
    from backend.qpso import QPSOOptimizer
except ImportError:
    from qpso import QPSOOptimizer


def run_scalability_benchmark(
    network_nodes: int = 48,
    stop_counts: List[int] = None,
    congestion_mode: str = "rush_hour",
    num_particles: int = 25,
    max_iterations: int = 60
) -> Dict[str, Any]:
    """
    Executes a multi-scale benchmark across 10, 20, 30, 40 stops.
    All algorithms evaluate the identical network and stop demands.
    """
    if stop_counts is None:
        stop_counts = [10, 20, 30, 40]

    # Filter stop_counts to ensure we have enough nodes in network
    valid_stop_counts = [s for s in stop_counts if s < network_nodes]
    if not valid_stop_counts:
        valid_stop_counts = [min(10, network_nodes - 2)]

    # Generate synthetic benchmark city network
    city = CityNetwork(num_nodes=network_nodes, congestion_mode=congestion_mode, seed=1337)
    
    algorithms = ["QPSO", "Classical PSO", "Genetic Algorithm"]
    
    results = {
        "stops_tested": valid_stop_counts,
        "algorithms": algorithms,
        "congestion_mode": congestion_mode,
        "cost_by_stop_count": {alg: [] for alg in algorithms},
        "runtime_by_stop_count": {alg: [] for alg in algorithms},
        "convergence_iter_by_stop_count": {alg: [] for alg in algorithms},
        "detailed_runs": []
    }

    depot = 0
    all_available_stops = list(range(1, city.num_nodes))

    for stop_count in valid_stop_counts:
        # Select deterministic subset of stops for consistency
        random.seed(42 + stop_count)
        selected_stops = random.sample(all_available_stops, stop_count)
        demands = {s: city.nodes_data[s]["demand"] for s in selected_stops}

        all_stops_with_depot = [depot] + selected_stops
        cost_matrix, _ = city.get_cost_matrix(all_stops_with_depot)

        # 1. Run QPSO
        qpso = QPSOOptimizer(
            cost_matrix=cost_matrix,
            stop_nodes=selected_stops,
            start_node=depot,
            demands=demands,
            vehicle_capacity=35,
            num_particles=num_particles,
            max_iterations=max_iterations,
            seed=42
        )
        res_qpso = qpso.optimize()

        # 2. Run Classical PSO
        pso = ClassicalPSOOptimizer(
            cost_matrix=cost_matrix,
            stop_nodes=selected_stops,
            start_node=depot,
            demands=demands,
            vehicle_capacity=35,
            num_particles=num_particles,
            max_iterations=max_iterations,
            seed=42
        )
        res_pso = pso.optimize()

        # 3. Run Genetic Algorithm
        ga = GeneticAlgorithmOptimizer(
            cost_matrix=cost_matrix,
            stop_nodes=selected_stops,
            start_node=depot,
            demands=demands,
            vehicle_capacity=35,
            population_size=num_particles,
            max_generations=max_iterations,
            seed=42
        )
        res_ga = ga.optimize()

        # Define Best-Known Proxy Optimum f* = min(QPSO, PSO, GA)
        best_known_fitness = min(res_qpso["best_cost"], res_pso["best_cost"], res_ga["best_cost"])
        target_fitness = best_known_fitness * 1.05  # Within 5% of best-known

        def get_iter_to_target(convergence: List[float], target: float) -> int:
            for idx, val in enumerate(convergence):
                if val <= target:
                    return idx + 1
            return len(convergence)

        iter_qpso = get_iter_to_target(res_qpso["convergence"], target_fitness)
        iter_pso = get_iter_to_target(res_pso["convergence"], target_fitness)
        iter_ga = get_iter_to_target(res_ga["convergence"], target_fitness)

        # Append to aggregates
        results["cost_by_stop_count"]["QPSO"].append(res_qpso["best_cost"])
        results["cost_by_stop_count"]["Classical PSO"].append(res_pso["best_cost"])
        results["cost_by_stop_count"]["Genetic Algorithm"].append(res_ga["best_cost"])

        results["runtime_by_stop_count"]["QPSO"].append(res_qpso["runtime_ms"])
        results["runtime_by_stop_count"]["Classical PSO"].append(res_pso["runtime_ms"])
        results["runtime_by_stop_count"]["Genetic Algorithm"].append(res_ga["runtime_ms"])

        results["convergence_iter_by_stop_count"]["QPSO"].append(iter_qpso)
        results["convergence_iter_by_stop_count"]["Classical PSO"].append(iter_pso)
        results["convergence_iter_by_stop_count"]["Genetic Algorithm"].append(iter_ga)

        results["detailed_runs"].append({
            "stops": stop_count,
            "best_known_proxy": best_known_fitness,
            "qpso": {"cost": res_qpso["best_cost"], "runtime_ms": res_qpso["runtime_ms"], "converged_iter": iter_qpso},
            "pso": {"cost": res_pso["best_cost"], "runtime_ms": res_pso["runtime_ms"], "converged_iter": iter_pso},
            "ga": {"cost": res_ga["best_cost"], "runtime_ms": res_ga["runtime_ms"], "converged_iter": iter_ga},
        })

    return results



def solve_ortools(cost_matrix: List[List[float]], demands: Dict[int, int], vehicle_capacity: int, stop_nodes: List[int], start_node: int) -> Dict[str, Any]:
    start_time = time.perf_counter()
    
    # OR-Tools requires integer matrices
    int_matrix = [[int(val * 1000) for val in row] for row in cost_matrix]
    
    manager = pywrapcp.RoutingIndexManager(len(cost_matrix), 1, stop_nodes.index(start_node))
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        # Map back to stop ID
        real_stop = stop_nodes[from_node]
        return demands.get(real_stop, 0)

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        [vehicle_capacity],  # vehicle maximum capacities
        True,  # start cumul to zero
        'Capacity')

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    search_parameters.local_search_metaheuristic = (routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.FromSeconds(2) # 2 second time limit for fair comparison

    solution = routing.SolveWithParameters(search_parameters)

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    if solution:
        index = routing.Start(0)
        route = []
        route_cost = 0
        while not routing.IsEnd(index):
            node_idx = manager.IndexToNode(index)
            route.append(stop_nodes[node_idx])
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_cost += cost_matrix[manager.IndexToNode(previous_index)][manager.IndexToNode(index)]
        route.append(stop_nodes[manager.IndexToNode(index)]) # Add depot at end
        
        return {
            "algorithm": "OR-Tools (GLS)",
            "cost": round(route_cost, 2),
            "runtime_ms": elapsed_ms,
            "route": route
        }
    return {
        "algorithm": "OR-Tools (GLS)",
        "cost": float('inf'),
        "runtime_ms": elapsed_ms,
        "route": []
    }


def solve_nearest_neighbor(cost_matrix: List[List[float]], demands: Dict[int, int], vehicle_capacity: int, stop_nodes: List[int], start_node: int) -> Dict[str, Any]:
    start_time = time.perf_counter()
    
    unvisited = set(stop_nodes)
    if start_node in unvisited:
        unvisited.remove(start_node)
        
    current = start_node
    route = [start_node]
    total_cost = 0.0
    current_load = 0
    
    while unvisited:
        # Find nearest
        curr_idx = stop_nodes.index(current)
        nearest = None
        min_dist = float('inf')
        
        for n in unvisited:
            dist = cost_matrix[curr_idx][stop_nodes.index(n)]
            if dist < min_dist:
                min_dist = dist
                nearest = n
                
        d = demands.get(nearest, 0)
        if current_load + d > vehicle_capacity:
            # Must return to depot
            total_cost += cost_matrix[curr_idx][stop_nodes.index(start_node)]
            route.append(start_node)
            current = start_node
            current_load = 0
        else:
            total_cost += min_dist
            route.append(nearest)
            unvisited.remove(nearest)
            current = nearest
            current_load += d
            
    # Return to depot at the end
    total_cost += cost_matrix[stop_nodes.index(current)][stop_nodes.index(start_node)]
    route.append(start_node)
    
    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
    
    return {
        "algorithm": "Nearest Neighbor",
        "cost": round(total_cost, 2),
        "runtime_ms": elapsed_ms,
        "route": route
    }
