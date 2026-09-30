"""
QuantumRoute Engine - Benchmarking Suite & Offline Runner
Performs:
1. Convergence Benchmark:
   - N = 15 independent runs over 100 iterations on the same CVRP instance.
   - Calculates iteration-by-iteration mean fitness (mu) and standard deviation (sigma).
   - Generates confidence bands (mu - sigma, mu + sigma).
   - Exports results to public/data/convergence_benchmark.json.

2. Scalability Benchmark:
   - Variable problem sizes: N = 10, 25, 50, 100, 250 stops.
   - Records solver computation time (seconds) and objective cost for QPSO, PSO, GA, Greedy.
   - Exports results to public/data/scalability_benchmark.json.
"""

import json
import math
import os
import random
import time
from typing import Dict, List, Any, Tuple
import numpy as np

from engine.qpso import QPSOCVRPSolver
from engine.baselines import ClassicalPSOCVRPSolver, GeneticAlgorithmCVRPSolver, GreedyNearestNeighborCVRPSolver


def generate_synthetic_instance(num_stops: int, seed: int = 42) -> Tuple[List[List[float]], Dict[int, float]]:
    """Generates a realistic distance/duration matrix and stop demands for CVRP."""
    rng = np.random.RandomState(seed)
    # Total nodes = depot (0) + customer stops
    total_nodes = num_stops + 1

    # Generate 2D coordinates in a simulated 15km x 15km urban grid
    coords = rng.uniform(0.0, 15000.0, (total_nodes, 2))
    coords[0] = [7500.0, 7500.0]  # Place depot near center

    cost_matrix = [[0.0] * total_nodes for _ in range(total_nodes)]
    for i in range(total_nodes):
        for j in range(total_nodes):
            if i != j:
                # Euclidean + Manhattan urban road factor (1.25)
                dist = float(np.linalg.norm(coords[i] - coords[j]) * 1.25)
                cost_matrix[i][j] = round(dist, 2)

    # Demands between 2 and 8 units, depot has 0 demand
    demands: Dict[int, float] = {}
    for i in range(1, total_nodes):
        demands[i] = float(rng.randint(2, 9))

    return cost_matrix, demands


def run_convergence_benchmark(num_runs: int = 15, max_iterations: int = 100, num_stops: int = 30) -> Dict[str, Any]:
    """Runs N=15 runs over 100 iterations comparing QPSO, PSO, GA, and Greedy."""
    print(f"\n[Benchmark] Starting Convergence Test: N={num_runs} runs, {max_iterations} iterations, {num_stops} stops...")
    cost_matrix, demands = generate_synthetic_instance(num_stops, seed=26137)
    vehicle_capacity = 45.0

    qpso_histories = []
    pso_histories = []
    ga_histories = []
    greedy_costs = []

    qpso_runtimes = []
    pso_runtimes = []
    ga_runtimes = []
    greedy_runtimes = []

    for run_idx in range(num_runs):
        run_seed = 1000 + run_idx * 37
        print(f"  -> Run {run_idx + 1}/{num_runs} (seed={run_seed})...")

        # 1. QPSO
        solver_qpso = QPSOCVRPSolver(
            cost_matrix=cost_matrix,
            stop_demands=demands,
            depot_index=0,
            vehicle_capacity=vehicle_capacity,
            num_particles=30,
            max_iterations=max_iterations,
            seed=run_seed
        )
        res_qpso = solver_qpso.solve()
        qpso_histories.append(res_qpso["iterations_history"])
        qpso_runtimes.append(res_qpso["runtime_ms"])

        # 2. Classical PSO
        solver_pso = ClassicalPSOCVRPSolver(
            cost_matrix=cost_matrix,
            stop_demands=demands,
            depot_index=0,
            vehicle_capacity=vehicle_capacity,
            num_particles=30,
            max_iterations=max_iterations,
            seed=run_seed
        )
        res_pso = solver_pso.solve()
        pso_histories.append(res_pso["iterations_history"])
        pso_runtimes.append(res_pso["runtime_ms"])

        # 3. Genetic Algorithm
        solver_ga = GeneticAlgorithmCVRPSolver(
            cost_matrix=cost_matrix,
            stop_demands=demands,
            depot_index=0,
            vehicle_capacity=vehicle_capacity,
            population_size=30,
            max_generations=max_iterations,
            seed=run_seed
        )
        res_ga = solver_ga.solve()
        ga_histories.append(res_ga["iterations_history"])
        ga_runtimes.append(res_ga["runtime_ms"])

        # 4. Greedy Nearest Neighbor
        solver_greedy = GreedyNearestNeighborCVRPSolver(
            cost_matrix=cost_matrix,
            stop_demands=demands,
            depot_index=0,
            vehicle_capacity=vehicle_capacity
        )
        res_greedy = solver_greedy.solve()
        greedy_costs.append(res_greedy["best_cost"])
        greedy_runtimes.append(res_greedy["runtime_ms"])

    # Compute iteration-by-iteration statistics
    qpso_arr = np.array(qpso_histories)  # shape: (num_runs, max_iterations)
    pso_arr = np.array(pso_histories)
    ga_arr = np.array(ga_histories)

    qpso_means = np.mean(qpso_arr, axis=0)
    qpso_stds = np.std(qpso_arr, axis=0)

    pso_means = np.mean(pso_arr, axis=0)
    pso_stds = np.std(pso_arr, axis=0)

    ga_means = np.mean(ga_arr, axis=0)
    ga_stds = np.std(ga_arr, axis=0)

    greedy_baseline_mean = float(np.mean(greedy_costs))

    iterations_data = []
    for it in range(max_iterations):
        q_m = float(qpso_means[it])
        q_s = float(qpso_stds[it])
        p_m = float(pso_means[it])
        p_s = float(pso_stds[it])
        g_m = float(ga_means[it])
        g_s = float(ga_stds[it])

        iterations_data.append({
            "iteration": it + 1,
            "qpso_mean": round(q_m, 2),
            "qpso_std": round(q_s, 2),
            "qpso_upper": round(q_m + q_s, 2),
            "qpso_lower": round(max(0.0, q_m - q_s), 2),
            "pso_mean": round(p_m, 2),
            "pso_std": round(p_s, 2),
            "pso_upper": round(p_m + p_s, 2),
            "pso_lower": round(max(0.0, p_m - p_s), 2),
            "ga_mean": round(g_m, 2),
            "ga_std": round(g_s, 2),
            "ga_upper": round(g_m + g_s, 2),
            "ga_lower": round(max(0.0, g_m - g_s), 2),
            "greedy_baseline": round(greedy_baseline_mean, 2)
        })

    # Find approximate convergence iteration (when within 1% of final)
    def find_convergence_iter(means: np.ndarray) -> int:
        final_val = means[-1]
        threshold = final_val * 1.01
        for idx, val in enumerate(means):
            if val <= threshold:
                return idx + 1
        return len(means)

    summary = {
        "qpso": {
            "name": "QPSO (Quantum PSO)",
            "final_mean_cost": round(float(qpso_means[-1]), 2),
            "final_std_dev": round(float(qpso_stds[-1]), 2),
            "best_found_cost": round(float(np.min(qpso_arr)), 2),
            "avg_runtime_ms": round(float(np.mean(qpso_runtimes)), 2),
            "convergence_iteration": find_convergence_iter(qpso_means)
        },
        "pso": {
            "name": "Classical PSO",
            "final_mean_cost": round(float(pso_means[-1]), 2),
            "final_std_dev": round(float(pso_stds[-1]), 2),
            "best_found_cost": round(float(np.min(pso_arr)), 2),
            "avg_runtime_ms": round(float(np.mean(pso_runtimes)), 2),
            "convergence_iteration": find_convergence_iter(pso_means)
        },
        "ga": {
            "name": "Genetic Algorithm",
            "final_mean_cost": round(float(ga_means[-1]), 2),
            "final_std_dev": round(float(ga_stds[-1]), 2),
            "best_found_cost": round(float(np.min(ga_arr)), 2),
            "avg_runtime_ms": round(float(np.mean(ga_runtimes)), 2),
            "convergence_iteration": find_convergence_iter(ga_means)
        },
        "greedy": {
            "name": "Greedy (Nearest Neighbor)",
            "final_mean_cost": round(greedy_baseline_mean, 2),
            "final_std_dev": round(float(np.std(greedy_costs)), 2),
            "best_found_cost": round(float(np.min(greedy_costs)), 2),
            "avg_runtime_ms": round(float(np.mean(greedy_runtimes)), 2),
            "convergence_iteration": 1
        }
    }

    return {
        "metadata": {
            "problem": "Capacitated Vehicle Routing Problem (CVRP)",
            "benchmark_type": "Convergence Analysis",
            "num_runs": num_runs,
            "max_iterations": max_iterations,
            "num_stops": num_stops,
            "vehicle_capacity": vehicle_capacity
        },
        "summary": summary,
        "iterations": iterations_data
    }


def run_scalability_benchmark(problem_sizes: List[int] = [10, 25, 50, 100, 250]) -> Dict[str, Any]:
    """Runs Scalability Test comparing computation time (seconds) and cost across problem sizes."""
    print(f"\n[Benchmark] Starting Scalability Test across problem sizes: {problem_sizes}...")
    results = []

    for n_stops in problem_sizes:
        print(f"  -> Benchmarking N = {n_stops} stops...")
        cost_matrix, demands = generate_synthetic_instance(n_stops, seed=42 + n_stops)
        vehicle_capacity = max(30.0, float(n_stops) * 1.5)

        # Scale parameters appropriately for size
        p_count = min(40, max(20, n_stops // 3))
        # Keep iterations capped so 250 nodes completes swiftly while producing solid convergence
        iters = 70 if n_stops <= 50 else (50 if n_stops <= 100 else 35)

        # 1. QPSO
        t0 = time.perf_counter()
        qpso_solver = QPSOCVRPSolver(
            cost_matrix=cost_matrix,
            stop_demands=demands,
            depot_index=0,
            vehicle_capacity=vehicle_capacity,
            num_particles=p_count,
            max_iterations=iters,
            seed=42
        )
        qpso_res = qpso_solver.solve()
        qpso_time_sec = round(time.perf_counter() - t0, 3)

        # 2. Classical PSO
        t0 = time.perf_counter()
        pso_solver = ClassicalPSOCVRPSolver(
            cost_matrix=cost_matrix,
            stop_demands=demands,
            depot_index=0,
            vehicle_capacity=vehicle_capacity,
            num_particles=p_count,
            max_iterations=iters,
            seed=42
        )
        pso_res = pso_solver.solve()
        pso_time_sec = round(time.perf_counter() - t0, 3)

        # 3. GA
        t0 = time.perf_counter()
        ga_solver = GeneticAlgorithmCVRPSolver(
            cost_matrix=cost_matrix,
            stop_demands=demands,
            depot_index=0,
            vehicle_capacity=vehicle_capacity,
            population_size=p_count,
            max_generations=iters,
            seed=42
        )
        ga_res = ga_solver.solve()
        ga_time_sec = round(time.perf_counter() - t0, 3)

        # 4. Greedy
        t0 = time.perf_counter()
        greedy_solver = GreedyNearestNeighborCVRPSolver(
            cost_matrix=cost_matrix,
            stop_demands=demands,
            depot_index=0,
            vehicle_capacity=vehicle_capacity
        )
        greedy_res = greedy_solver.solve()
        greedy_time_sec = round(max(0.001, time.perf_counter() - t0), 4)

        results.append({
            "stops": n_stops,
            "qpso_runtime_sec": qpso_time_sec,
            "qpso_cost": qpso_res["best_cost"],
            "pso_runtime_sec": pso_time_sec,
            "pso_cost": pso_res["best_cost"],
            "ga_runtime_sec": ga_time_sec,
            "ga_cost": ga_res["best_cost"],
            "greedy_runtime_sec": greedy_time_sec,
            "greedy_cost": greedy_res["best_cost"],
            # Cost savings of QPSO compared to Greedy (%)
            "qpso_savings_vs_greedy_pct": round(((greedy_res["best_cost"] - qpso_res["best_cost"]) / greedy_res["best_cost"]) * 100.0, 1),
            # Gap of QPSO to Classical PSO (%)
            "qpso_improvement_vs_pso_pct": round(((pso_res["best_cost"] - qpso_res["best_cost"]) / pso_res["best_cost"]) * 100.0, 1)
        })

    return {
        "metadata": {
            "problem": "Capacitated Vehicle Routing Problem (CVRP)",
            "benchmark_type": "Scalability Analysis",
            "evaluated_sizes": problem_sizes
        },
        "results": results
    }


def save_json_outputs(convergence_data: Dict[str, Any], scalability_data: Dict[str, Any]):
    """Saves benchmark results to both web/public/data and public/data."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_dirs = [
        os.path.join(base_dir, "web", "public", "data"),
        os.path.join(base_dir, "public", "data")
    ]

    for d in target_dirs:
        os.makedirs(d, exist_ok=True)
        conv_path = os.path.join(d, "convergence_benchmark.json")
        scal_path = os.path.join(d, "scalability_benchmark.json")

        with open(conv_path, "w", encoding="utf-8") as f:
            json.dump(convergence_data, f, indent=2)
        print(f"[Benchmark] Saved convergence benchmark to {conv_path}")

        with open(scal_path, "w", encoding="utf-8") as f:
            json.dump(scalability_data, f, indent=2)
        print(f"[Benchmark] Saved scalability benchmark to {scal_path}")


def main():
    print("=================================================================")
    print("  SIH PS 26137: QuantumRoute Optimization Benchmarking Suite     ")
    print("=================================================================")
    t_start = time.time()

    # 1. Convergence Test: N=15 runs over 100 iterations
    convergence_results = run_convergence_benchmark(num_runs=15, max_iterations=100, num_stops=30)

    # 2. Scalability Test: N = 10, 25, 50, 100, 250 stops
    scalability_results = run_scalability_benchmark(problem_sizes=[10, 25, 50, 100, 250])

    # 3. Export to JSON
    save_json_outputs(convergence_results, scalability_results)

    total_time = round(time.time() - t_start, 2)
    print(f"\n[Benchmark] Complete in {total_time}s! All benchmark artifacts successfully generated.")


if __name__ == "__main__":
    main()
