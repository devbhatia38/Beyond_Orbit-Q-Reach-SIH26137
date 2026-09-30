"""
QuantumRoute Engine - Baseline Algorithms for CVRP
Implementations for comparative benchmarking:
1. Classical PSO (Inertia weight, cognitive/social velocity updates, SPV)
2. Genetic Algorithm (GA) (Order Crossover OX, Swap/Inversion mutation, Elitism)
3. Greedy Heuristic (Nearest Neighbor with vehicle capacity constraints)
"""

import math
import random
import time
from typing import List, Dict, Tuple, Any, Optional
import numpy as np


class ClassicalPSOCVRPSolver:
    """Standard velocity-position Particle Swarm Optimization for CVRP."""

    def __init__(
        self,
        cost_matrix: List[List[float]],
        stop_demands: Dict[int, float],
        depot_index: int = 0,
        vehicle_capacity: float = 50.0,
        num_particles: int = 35,
        max_iterations: int = 100,
        w: float = 0.729,      # Inertia weight
        c1: float = 1.49445,   # Cognitive acceleration
        c2: float = 1.49445,   # Social acceleration
        seed: Optional[int] = None
    ):
        self.cost_matrix = cost_matrix
        self.stop_demands = stop_demands
        self.depot_index = depot_index
        self.vehicle_capacity = vehicle_capacity
        self.num_particles = num_particles
        self.max_iterations = max_iterations
        self.w = w
        self.c1 = c1
        self.c2 = c2
        self.seed = seed

        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        self.customer_indices = [i for i in range(len(cost_matrix)) if i != depot_index]
        self.dimension = len(self.customer_indices)

    def decode_permutation(self, perm: List[int]) -> Tuple[List[List[int]], float]:
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

        total_cost = 0.0
        for r in routes:
            for k in range(len(r) - 1):
                total_cost += self.cost_matrix[r[k]][r[k + 1]]

        return routes, total_cost

    def spv_to_permutation(self, continuous_vector: np.ndarray) -> List[int]:
        sorted_indices = np.argsort(continuous_vector)
        return [self.customer_indices[idx] for idx in sorted_indices]

    def solve(self) -> Dict[str, Any]:
        start_time = time.perf_counter()
        if self.dimension == 0:
            return {"algorithm": "Classical PSO", "best_cost": 0.0, "iterations_history": [0.0] * self.max_iterations, "runtime_ms": 0.0}

        M, D = self.num_particles, self.dimension
        X = np.random.uniform(-4.0, 4.0, (M, D))
        V = np.random.uniform(-1.0, 1.0, (M, D))

        P = np.copy(X)
        P_fit = np.full(M, float('inf'))

        g_best_pos = np.copy(X[0])
        g_best_fit = float('inf')
        g_best_routes: List[List[int]] = []

        for i in range(M):
            perm = self.spv_to_permutation(X[i])
            routes, fit = self.decode_permutation(perm)
            P_fit[i] = fit
            if fit < g_best_fit:
                g_best_fit = fit
                g_best_pos = np.copy(X[i])
                g_best_routes = routes

        iterations_history = [float(g_best_fit)]

        for _ in range(1, self.max_iterations):
            for i in range(M):
                r1 = np.random.uniform(0.0, 1.0, D)
                r2 = np.random.uniform(0.0, 1.0, D)

                # Classical velocity update
                V[i] = self.w * V[i] + self.c1 * r1 * (P[i] - X[i]) + self.c2 * r2 * (g_best_pos - X[i])
                V[i] = np.clip(V[i], -3.0, 3.0)

                # Classical position update
                X[i] = X[i] + V[i]
                X[i] = np.clip(X[i], -10.0, 10.0)

                perm = self.spv_to_permutation(X[i])
                routes, fit = self.decode_permutation(perm)

                if fit < P_fit[i]:
                    P_fit[i] = fit
                    P[i] = np.copy(X[i])
                    if fit < g_best_fit:
                        g_best_fit = fit
                        g_best_pos = np.copy(X[i])
                        g_best_routes = routes

            iterations_history.append(float(g_best_fit))

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "algorithm": "Classical PSO",
            "routes": g_best_routes,
            "best_cost": round(g_best_fit, 2),
            "iterations_history": iterations_history,
            "runtime_ms": round(elapsed_ms, 2)
        }


class GeneticAlgorithmCVRPSolver:
    """Genetic Algorithm for CVRP with Order Crossover (OX) and Inversion Mutation."""

    def __init__(
        self,
        cost_matrix: List[List[float]],
        stop_demands: Dict[int, float],
        depot_index: int = 0,
        vehicle_capacity: float = 50.0,
        population_size: int = 35,
        max_generations: int = 100,
        crossover_rate: float = 0.85,
        mutation_rate: float = 0.20,
        elitism_count: int = 2,
        seed: Optional[int] = None
    ):
        self.cost_matrix = cost_matrix
        self.stop_demands = stop_demands
        self.depot_index = depot_index
        self.vehicle_capacity = vehicle_capacity
        self.pop_size = population_size
        self.max_generations = max_generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.elitism_count = elitism_count
        self.seed = seed

        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        self.customer_indices = [i for i in range(len(cost_matrix)) if i != depot_index]
        self.dimension = len(self.customer_indices)

    def decode_permutation(self, perm: List[int]) -> Tuple[List[List[int]], float]:
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

        total_cost = 0.0
        for r in routes:
            for k in range(len(r) - 1):
                total_cost += self.cost_matrix[r[k]][r[k + 1]]

        return routes, total_cost

    def _order_crossover(self, parent1: List[int], parent2: List[int]) -> List[int]:
        """Order Crossover (OX) for valid tour permutations."""
        size = len(parent1)
        if size <= 2:
            return list(parent1)

        idx1, idx2 = sorted(random.sample(range(size), 2))
        child = [None] * size
        child[idx1:idx2] = parent1[idx1:idx2]

        p2_remaining = [item for item in parent2 if item not in child[idx1:idx2]]
        pos = idx2
        for item in p2_remaining:
            if pos >= size:
                pos = 0
            if pos == idx1:
                pos = idx2
                if pos >= size:
                    pos = 0
            while child[pos] is not None:
                pos = (pos + 1) % size
            child[pos] = item

        return child

    def _mutate(self, individual: List[int]):
        """Inversion / 2-opt segment mutation."""
        if len(individual) > 2 and random.random() < self.mutation_rate:
            i, j = sorted(random.sample(range(len(individual)), 2))
            individual[i:j + 1] = reversed(individual[i:j + 1])

    def solve(self) -> Dict[str, Any]:
        start_time = time.perf_counter()
        if self.dimension == 0:
            return {"algorithm": "Genetic Algorithm", "best_cost": 0.0, "iterations_history": [0.0] * self.max_generations, "runtime_ms": 0.0}

        # Initialize random population of permutations
        population = []
        for _ in range(self.pop_size):
            perm = list(self.customer_indices)
            random.shuffle(perm)
            population.append(perm)

        g_best_perm = population[0]
        g_best_routes, g_best_fit = self.decode_permutation(g_best_perm)

        # Initial evaluation
        fitnesses = []
        for ind in population:
            _, fit = self.decode_permutation(ind)
            fitnesses.append(fit)
            if fit < g_best_fit:
                g_best_fit = fit
                g_best_perm = list(ind)

        iterations_history = [float(g_best_fit)]

        for _ in range(1, self.max_generations):
            # Sort population by fitness
            sorted_indices = sorted(range(len(population)), key=lambda k: fitnesses[k])
            population = [population[k] for k in sorted_indices]
            fitnesses = [fitnesses[k] for k in sorted_indices]

            if fitnesses[0] < g_best_fit:
                g_best_fit = fitnesses[0]
                g_best_perm = list(population[0])

            # Elitism: retain top individuals
            new_population = [list(population[k]) for k in range(self.elitism_count)]

            # Tournament Selection and Crossover
            while len(new_population) < self.pop_size:
                # Tournament size 3
                t1 = random.sample(range(self.pop_size), 3)
                t2 = random.sample(range(self.pop_size), 3)
                p1_idx = min(t1, key=lambda idx: fitnesses[idx])
                p2_idx = min(t2, key=lambda idx: fitnesses[idx])

                p1, p2 = population[p1_idx], population[p2_idx]

                if random.random() < self.crossover_rate:
                    child = self._order_crossover(p1, p2)
                else:
                    child = list(p1)

                self._mutate(child)
                new_population.append(child)

            population = new_population
            fitnesses = []
            for ind in population:
                _, fit = self.decode_permutation(ind)
                fitnesses.append(fit)
                if fit < g_best_fit:
                    g_best_fit = fit
                    g_best_perm = list(ind)

            iterations_history.append(float(g_best_fit))

        g_best_routes, _ = self.decode_permutation(g_best_perm)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "algorithm": "Genetic Algorithm",
            "routes": g_best_routes,
            "best_cost": round(g_best_fit, 2),
            "iterations_history": iterations_history,
            "runtime_ms": round(elapsed_ms, 2)
        }


class GreedyNearestNeighborCVRPSolver:
    """Greedy Nearest Neighbor with vehicle payload capacity constraint."""

    def __init__(
        self,
        cost_matrix: List[List[float]],
        stop_demands: Dict[int, float],
        depot_index: int = 0,
        vehicle_capacity: float = 50.0
    ):
        self.cost_matrix = cost_matrix
        self.stop_demands = stop_demands
        self.depot_index = depot_index
        self.vehicle_capacity = vehicle_capacity
        self.customer_indices = [i for i in range(len(cost_matrix)) if i != depot_index]

    def solve(self) -> Dict[str, Any]:
        start_time = time.perf_counter()
        unvisited = set(self.customer_indices)
        routes: List[List[int]] = []
        total_cost = 0.0

        while unvisited:
            route = [self.depot_index]
            current_node = self.depot_index
            current_load = 0.0

            while unvisited:
                # Find feasible candidates that fit capacity
                feasible = [
                    c for c in unvisited
                    if current_load + self.stop_demands.get(c, 1.0) <= self.vehicle_capacity
                ]

                if not feasible:
                    # If vehicle full or no candidates fit, return to depot
                    break

                # Select closest feasible candidate
                next_node = min(feasible, key=lambda c: self.cost_matrix[current_node][c])
                route.append(next_node)
                total_cost += self.cost_matrix[current_node][next_node]
                current_load += self.stop_demands.get(next_node, 1.0)
                unvisited.remove(next_node)
                current_node = next_node

            # Return back to depot
            route.append(self.depot_index)
            total_cost += self.cost_matrix[current_node][self.depot_index]
            routes.append(route)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "algorithm": "Greedy (Nearest Neighbor)",
            "routes": routes,
            "best_cost": round(total_cost, 2),
            "iterations_history": [round(total_cost, 2)],
            "runtime_ms": round(elapsed_ms, 2)
        }
