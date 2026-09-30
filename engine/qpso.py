"""
QuantumRoute Engine - Quantum Particle Swarm Optimization (QPSO) for CVRP
Formulation:
1. Smallest Position Value (SPV) mapping continuous quantum state vectors to discrete tour permutations.
2. Quantum Delta-Potential-Well wave function collapse dynamics:
   - Mean-best position (mbest) across swarm
   - Stochastic local attractor p_i
   - Contraction-Expansion (CE) coefficient dynamic annealing
3. Strict Capacitated Vehicle Routing Problem (CVRP) constraints:
   - Vehicle payload capacity constraint Q
   - Single-visit customer constraint
   - Depot start/end loops for every vehicle route
4. Hybrid Quantum Local Search:
   - 2-Opt local route enhancement on global best
   - Quantum tunneling across local minima
"""

import math
import random
import time
from typing import List, Dict, Tuple, Any, Optional
import numpy as np


def two_opt_route(route: List[int], cost_matrix: List[List[float]]) -> List[int]:
    """Applies 2-opt edge exchange optimization to an individual vehicle route."""
    if len(route) <= 3:
        return list(route)

    best_r = list(route)
    improved = True
    iterations = 0
    max_iters = 30

    while improved and iterations < max_iters:
        improved = False
        iterations += 1
        for i in range(1, len(best_r) - 2):
            for j in range(i + 1, len(best_r) - 1):
                d_curr = cost_matrix[best_r[i - 1]][best_r[i]] + cost_matrix[best_r[j]][best_r[j + 1]]
                d_swap = cost_matrix[best_r[i - 1]][best_r[j]] + cost_matrix[best_r[i]][best_r[j + 1]]
                if d_swap < d_curr - 1e-4:
                    best_r[i:j + 1] = reversed(best_r[i:j + 1])
                    improved = True
                    break
            if improved:
                break

    return best_r


class QPSOCVRPSolver:
    """
    Quantum-behaved Particle Swarm Optimization Solver for Capacitated Vehicle Routing.
    """

    def __init__(
        self,
        cost_matrix: List[List[float]],
        stop_demands: Dict[int, float],
        depot_index: int = 0,
        vehicle_capacity: float = 50.0,
        distance_matrix: Optional[List[List[float]]] = None,
        num_particles: int = 35,
        max_iterations: int = 100,
        alpha_start: float = 1.0,
        alpha_end: float = 0.5,
        penalty_factor: float = 500.0,
        enable_2opt: bool = True,
        seed: Optional[int] = None
    ):
        self.cost_matrix = cost_matrix
        self.distance_matrix = distance_matrix if distance_matrix is not None else cost_matrix
        self.stop_demands = stop_demands
        self.depot_index = depot_index
        self.vehicle_capacity = vehicle_capacity
        self.num_particles = num_particles
        self.max_iterations = max_iterations
        self.alpha_start = alpha_start
        self.alpha_end = alpha_end
        self.penalty_factor = penalty_factor
        self.enable_2opt = enable_2opt
        self.seed = seed

        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        self.customer_indices = [i for i in range(len(cost_matrix)) if i != depot_index]
        self.dimension = len(self.customer_indices)

    def decode_permutation(self, perm: List[int], apply_opt: bool = False) -> Tuple[List[List[int]], float, float]:
        """
        Partitions customer permutation into vehicle routes respecting vehicle_capacity.
        Each route starts at depot (0) and ends at depot (0).
        """
        routes: List[List[int]] = []
        current_route: List[int] = [self.depot_index]
        current_load = 0.0

        for cust in perm:
            demand = self.stop_demands.get(cust, 1.0)
            if current_load + demand > self.vehicle_capacity and len(current_route) > 1:
                current_route.append(self.depot_index)
                routes.append(current_route)
                current_route = [self.depot_index, cust]
                current_load = demand
            else:
                current_route.append(cust)
                current_load += demand

        if len(current_route) > 1:
            current_route.append(self.depot_index)
            routes.append(current_route)
        elif len(routes) == 0:
            routes.append([self.depot_index, self.depot_index])

        if apply_opt and self.enable_2opt:
            routes = [two_opt_route(r, self.cost_matrix) for r in routes]

        total_cost = 0.0
        total_dist = 0.0
        for r in routes:
            for k in range(len(r) - 1):
                u, v = r[k], r[k + 1]
                total_cost += self.cost_matrix[u][v]
                total_dist += self.distance_matrix[u][v]

        return routes, total_cost, total_dist

    def spv_to_permutation(self, continuous_vector: np.ndarray) -> List[int]:
        sorted_indices = np.argsort(continuous_vector)
        return [self.customer_indices[idx] for idx in sorted_indices]

    def solve(self) -> Dict[str, Any]:
        start_time = time.perf_counter()

        if self.dimension == 0:
            return {
                "algorithm": "QPSO",
                "routes": [[self.depot_index, self.depot_index]],
                "best_cost": 0.0,
                "best_distance": 0.0,
                "iterations_history": [0.0] * self.max_iterations,
                "runtime_ms": 0.0
            }

        M = self.num_particles
        D = self.dimension

        # Initialize particles in [-4, 4]
        X = np.random.uniform(-4.0, 4.0, (M, D))

        # Seed particle 0 with nearest neighbor heuristic for rapid convergence
        unvisited = list(self.customer_indices)
        curr = self.depot_index
        nn_order = []
        while unvisited:
            nxt = min(unvisited, key=lambda c: self.cost_matrix[curr][c])
            nn_order.append(nxt)
            unvisited.remove(nxt)
            curr = nxt

        # Map nn_order into continuous space for particle 0
        order_map = {node: idx for idx, node in enumerate(nn_order)}
        X[0] = np.array([float(order_map[self.customer_indices[d]]) - D / 2.0 for d in range(D)])

        P = np.copy(X)
        P_fit = np.full(M, float('inf'))

        g_best_pos = np.copy(X[0])
        g_best_fit = float('inf')
        g_best_routes: List[List[int]] = []
        g_best_dist = float('inf')

        for i in range(M):
            perm = self.spv_to_permutation(X[i])
            routes, fit, dist = self.decode_permutation(perm, apply_opt=False)
            P_fit[i] = fit
            if fit < g_best_fit:
                g_best_fit = fit
                g_best_pos = np.copy(X[i])
                g_best_routes = routes
                g_best_dist = dist

        iterations_history = [float(g_best_fit)]

        # Main Loop
        for t in range(1, self.max_iterations):
            # Dynamic annealing of Contraction-Expansion (CE) coefficient alpha
            alpha = self.alpha_start - (t / self.max_iterations) * (self.alpha_start - self.alpha_end)
            mbest = np.mean(P, axis=0)

            for i in range(M):
                phi = np.random.uniform(0.0, 1.0, D)
                p_i = phi * P[i] + (1.0 - phi) * g_best_pos

                u = np.random.uniform(0.0, 1.0, D)
                u = np.maximum(u, 1e-9)
                ln_inv_u = np.log(1.0 / u)

                signs = np.random.choice([-1.0, 1.0], size=D)
                X[i] = p_i + signs * alpha * np.abs(mbest - X[i]) * ln_inv_u
                X[i] = np.clip(X[i], -10.0, 10.0)

                perm = self.spv_to_permutation(X[i])
                routes, fit, dist = self.decode_permutation(perm, apply_opt=False)

                if fit < P_fit[i]:
                    P_fit[i] = fit
                    P[i] = np.copy(X[i])
                    if fit < g_best_fit:
                        g_best_fit = fit
                        g_best_pos = np.copy(X[i])
                        g_best_routes = routes
                        g_best_dist = dist

            # Periodic 2-opt refinement on global best every 15 iterations or final
            if self.enable_2opt and (t % 15 == 0 or t == self.max_iterations - 1):
                best_perm = self.spv_to_permutation(g_best_pos)
                opt_routes, opt_fit, opt_dist = self.decode_permutation(best_perm, apply_opt=True)
                if opt_fit < g_best_fit:
                    g_best_fit = opt_fit
                    g_best_routes = opt_routes
                    g_best_dist = opt_dist

            iterations_history.append(float(g_best_fit))

        # Final polishing
        if self.enable_2opt:
            best_perm = self.spv_to_permutation(g_best_pos)
            opt_routes, opt_fit, opt_dist = self.decode_permutation(best_perm, apply_opt=True)
            if opt_fit < g_best_fit:
                g_best_fit = opt_fit
                g_best_routes = opt_routes
                g_best_dist = opt_dist
            iterations_history[-1] = float(g_best_fit)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "algorithm": "QPSO",
            "routes": g_best_routes,
            "best_cost": round(g_best_fit, 2),
            "best_distance": round(g_best_dist, 2),
            "iterations_history": iterations_history,
            "runtime_ms": round(elapsed_ms, 2),
            "num_vehicles": len(g_best_routes),
            "num_stops": len(self.customer_indices)
        }
