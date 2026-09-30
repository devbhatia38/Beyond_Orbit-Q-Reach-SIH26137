"""
QuantumRoute - Baseline Optimizers for Comparative Benchmarking
Implements:
1. Classical PSO (velocity + inertia update, same SPV encoding).
2. Genetic Algorithm (OX crossover, inversion mutation, elitism).
3. Greedy Nearest-Neighbor heuristic (Dijkstra-guided).
"""

import time
import random
from typing import List, Dict, Tuple, Any, Optional
import numpy as np


def evaluate_baseline_metrics(
    permutation: List[int],
    start_node: int,
    demands: Dict[int, int],
    vehicle_capacity: int,
    cost_matrix: List[List[float]],
    distance_matrix: Optional[List[List[float]]],
    node_to_idx: Dict[int, int],
    routing_preference: str = "fastest",
    vehicle_type: str = "ice",
    penalty_weight: float = 50.0
) -> Tuple[float, List[List[int]], float, float, float]:
    """
    Unified multi-objective CVRP evaluation shared with QPSO:
    Calculates total travel time, physical road distance, and dynamic load-dependent emissions.
    """
    if not permutation:
        return 0.0, [[start_node, start_node]], 0.0, 0.0, 0.0

    trips: List[List[int]] = []
    current_trip: List[int] = []
    current_load = 0
    penalty = 0.0

    for stop_id in permutation:
        d = demands.get(stop_id, 0)
        if current_load + d > vehicle_capacity and len(current_trip) > 0:
            trips.append(current_trip)
            current_trip = [stop_id]
            current_load = d
        else:
            current_trip.append(stop_id)
            current_load += d

        if d > vehicle_capacity:
            penalty += (d - vehicle_capacity) * penalty_weight

    if current_trip:
        trips.append(current_trip)

    total_time = 0.0
    total_emissions = 0.0
    total_dist = 0.0
    depot_idx = node_to_idx[start_node]

    base_emissions_per_km = 150.0 if vehicle_type == "ice" else 50.0
    load_emissions_per_km = 10.0 if vehicle_type == "ice" else 3.0

    for trip in trips:
        trip_load = sum(demands.get(s, 0) for s in trip)
        prev_idx = depot_idx
        for stop_id in trip:
            curr_idx = node_to_idx[stop_id]
            leg_time = cost_matrix[prev_idx][curr_idx]
            leg_dist_km = (distance_matrix[prev_idx][curr_idx] / 1000.0) if distance_matrix else (leg_time * 0.008)

            total_time += leg_time
            total_emissions += leg_dist_km * (base_emissions_per_km + (trip_load * load_emissions_per_km))
            total_dist += (leg_dist_km * 1000.0)

            trip_load -= demands.get(stop_id, 0)
            prev_idx = curr_idx

        # Return to depot empty
        leg_time = cost_matrix[prev_idx][depot_idx]
        leg_dist_km = (distance_matrix[prev_idx][depot_idx] / 1000.0) if distance_matrix else (leg_time * 0.008)
        total_time += leg_time
        total_emissions += leg_dist_km * base_emissions_per_km
        total_dist += (leg_dist_km * 1000.0)

        trip.insert(0, start_node)
        trip.append(start_node)

    if routing_preference == "greenest":
        fitness = total_emissions + penalty * 50.0
    elif routing_preference == "balanced":
        fitness = (total_time * 0.5) + (total_emissions * 0.5) + penalty * 50.0
    else: # fastest
        fitness = total_time + penalty * 50.0

    return fitness, trips, total_time, total_emissions, total_dist


class ClassicalPSOOptimizer:
    """
    Standard Classical Particle Swarm Optimization (Kennedy & Eberhart 1995).
    Uses traditional velocity update with inertia weight (w), cognitive parameter (c1),
    and social parameter (c2). Operates on the exact same SPV encoding space as QPSO.
    """

    def __init__(
        self,
        cost_matrix: List[List[float]],
        stop_nodes: List[int],
        start_node: int,
        demands: Dict[int, int],
        vehicle_capacity: int = 35,
        num_particles: int = 30,
        max_iterations: int = 80,
        distance_matrix: Optional[List[List[float]]] = None,
        routing_preference: str = "fastest",
        vehicle_type: str = "ice",
        w: float = 0.729,
        c1: float = 1.49445,
        c2: float = 1.49445,
        seed: Optional[int] = None
    ):
        self.cost_matrix = cost_matrix
        self.distance_matrix = distance_matrix or cost_matrix
        self.stop_nodes = stop_nodes
        self.start_node = start_node
        self.demands = demands
        self.vehicle_capacity = vehicle_capacity
        self.num_particles = num_particles
        self.max_iterations = max_iterations
        self.routing_preference = routing_preference
        self.vehicle_type = vehicle_type
        self.w = w
        self.c1 = c1
        self.c2 = c2
        self.seed = seed

        self.all_nodes = [start_node] + [s for s in stop_nodes if s != start_node]
        self.node_to_idx = {node: i for i, node in enumerate(self.all_nodes)}
        self.dimension = len(stop_nodes)

    def evaluate_fitness(self, permutation: List[int]) -> Tuple[float, List[List[int]], float, float, float]:
        return evaluate_baseline_metrics(
            permutation=permutation,
            start_node=self.start_node,
            demands=self.demands,
            vehicle_capacity=self.vehicle_capacity,
            cost_matrix=self.cost_matrix,
            distance_matrix=self.distance_matrix,
            node_to_idx=self.node_to_idx,
            routing_preference=self.routing_preference,
            vehicle_type=self.vehicle_type
        )

    def spv_decode(self, continuous_vector: np.ndarray) -> List[int]:
        order_indices = np.argsort(continuous_vector)
        return [self.stop_nodes[i] for i in order_indices]

    def optimize(self) -> Dict[str, Any]:
        if self.seed is not None:
            np.random.seed(self.seed)
            random.seed(self.seed)

        start_time = time.perf_counter()
        D = self.dimension
        M = self.num_particles

        if D <= 1:
            perm = self.stop_nodes[:]
            fit, trips, t_time, t_emiss, t_dist = self.evaluate_fitness(perm)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            flattened = [node for trip in trips for node in trip[:-1]] + [self.start_node]
            return {
                "algorithm": "Classical PSO",
                "best_cost": round(fit, 2),
                "raw_cost": round(t_time, 2),
                "emissions_g": round(t_emiss, 2),
                "distance_m": round(t_dist, 2),
                "best_route": flattened,
                "trips": trips,
                "convergence": [round(fit, 2)] * self.max_iterations,
                "runtime_ms": elapsed_ms,
                "iterations": self.max_iterations,
                "num_trips": len(trips),
            }

        X = np.random.uniform(-4.0, 4.0, size=(M, D))
        V = np.random.uniform(-1.0, 1.0, size=(M, D))
        P = np.copy(X)
        pbest_fit = np.full(M, float('inf'))

        gbest_pos = np.copy(X[0])
        gbest_fit = float('inf')
        gbest_trips: List[List[int]] = []
        gbest_raw_cost = 0.0
        gbest_emissions = 0.0
        gbest_dist = 0.0

        convergence_history: List[float] = []

        for i in range(M):
            perm = self.spv_decode(X[i])
            fit, trips, t_time, t_emiss, t_dist = self.evaluate_fitness(perm)
            pbest_fit[i] = fit
            if fit < gbest_fit:
                gbest_fit = fit
                gbest_pos = np.copy(X[i])
                gbest_trips = trips
                gbest_raw_cost = t_time
                gbest_emissions = t_emiss
                gbest_dist = t_dist

        convergence_history.append(round(gbest_fit, 2))

        for it in range(1, self.max_iterations):
            r1 = np.random.uniform(0.0, 1.0, size=(M, D))
            r2 = np.random.uniform(0.0, 1.0, size=(M, D))

            V = self.w * V + self.c1 * r1 * (P - X) + self.c2 * r2 * (gbest_pos - X)
            V = np.clip(V, -3.0, 3.0)
            X = X + V
            X = np.clip(X, -8.0, 8.0)

            for i in range(M):
                perm = self.spv_decode(X[i])
                fit, trips, t_time, t_emiss, t_dist = self.evaluate_fitness(perm)

                if fit < pbest_fit[i]:
                    pbest_fit[i] = fit
                    P[i] = np.copy(X[i])

                    if fit < gbest_fit:
                        gbest_fit = fit
                        gbest_pos = np.copy(X[i])
                        gbest_trips = trips
                        gbest_raw_cost = t_time
                        gbest_emissions = t_emiss
                        gbest_dist = t_dist

            convergence_history.append(round(gbest_fit, 2))

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        flattened_route: List[int] = []
        for trip_idx, trip in enumerate(gbest_trips):
            if trip_idx == 0:
                flattened_route.extend(trip)
            else:
                flattened_route.extend(trip[1:])

        return {
            "algorithm": "Classical PSO",
            "best_cost": round(gbest_fit, 2),
            "raw_cost": round(gbest_raw_cost, 2),
            "emissions_g": round(gbest_emissions, 2),
            "distance_m": round(gbest_dist, 2),
            "best_route": flattened_route,
            "trips": gbest_trips,
            "convergence": convergence_history,
            "runtime_ms": elapsed_ms,
            "iterations": self.max_iterations,
            "num_trips": len(gbest_trips),
        }


class GeneticAlgorithmOptimizer:
    """
    Genetic Algorithm with Order Crossover (OX), Inversion Mutation, and Elitism.
    Evaluates solutions across the same fitness landscape.
    """

    def __init__(
        self,
        cost_matrix: List[List[float]],
        stop_nodes: List[int],
        start_node: int,
        demands: Dict[int, int],
        vehicle_capacity: int = 35,
        population_size: int = 30,
        max_generations: int = 80,
        distance_matrix: Optional[List[List[float]]] = None,
        routing_preference: str = "fastest",
        vehicle_type: str = "ice",
        crossover_rate: float = 0.85,
        mutation_rate: float = 0.20,
        elitism_count: int = 2,
        seed: Optional[int] = None
    ):
        self.cost_matrix = cost_matrix
        self.distance_matrix = distance_matrix or cost_matrix
        self.stop_nodes = stop_nodes
        self.start_node = start_node
        self.demands = demands
        self.vehicle_capacity = vehicle_capacity
        self.pop_size = population_size
        self.max_generations = max_generations
        self.routing_preference = routing_preference
        self.vehicle_type = vehicle_type
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.elitism_count = elitism_count
        self.seed = seed

        self.all_nodes = [start_node] + [s for s in stop_nodes if s != start_node]
        self.node_to_idx = {node: i for i, node in enumerate(self.all_nodes)}

    def evaluate_fitness(self, permutation: List[int]) -> Tuple[float, List[List[int]], float, float, float]:
        return evaluate_baseline_metrics(
            permutation=permutation,
            start_node=self.start_node,
            demands=self.demands,
            vehicle_capacity=self.vehicle_capacity,
            cost_matrix=self.cost_matrix,
            distance_matrix=self.distance_matrix,
            node_to_idx=self.node_to_idx,
            routing_preference=self.routing_preference,
            vehicle_type=self.vehicle_type
        )

    def order_crossover(self, parent1: List[int], parent2: List[int]) -> List[int]:
        size = len(parent1)
        if size <= 2:
            return parent1[:]
        cx1 = random.randint(0, size - 2)
        cx2 = random.randint(cx1 + 1, size - 1)

        child: List[Optional[int]] = [None] * size
        child[cx1:cx2 + 1] = parent1[cx1:cx2 + 1]
        copied_set = set(child[cx1:cx2 + 1])

        p2_idx = 0
        for i in range(size):
            if child[i] is None:
                while parent2[p2_idx] in copied_set:
                    p2_idx += 1
                child[i] = parent2[p2_idx]
                p2_idx += 1
        return [c for c in child if c is not None]

    def mutate_inversion(self, individual: List[int]) -> List[int]:
        if len(individual) <= 2:
            return individual
        i = random.randint(0, len(individual) - 2)
        j = random.randint(i + 1, len(individual) - 1)
        res = individual[:]
        res[i:j + 1] = reversed(res[i:j + 1])
        return res

    def optimize(self) -> Dict[str, Any]:
        if self.seed is not None:
            random.seed(self.seed)

        start_time = time.perf_counter()
        n = len(self.stop_nodes)

        if n <= 1:
            perm = self.stop_nodes[:]
            fit, trips, t_time, t_emiss, t_dist = self.evaluate_fitness(perm)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            flattened = [node for trip in trips for node in trip[:-1]] + [self.start_node]
            return {
                "algorithm": "Genetic Algorithm",
                "best_cost": round(fit, 2),
                "raw_cost": round(t_time, 2),
                "emissions_g": round(t_emiss, 2),
                "distance_m": round(t_dist, 2),
                "best_route": flattened,
                "trips": trips,
                "convergence": [round(fit, 2)] * self.max_generations,
                "runtime_ms": elapsed_ms,
                "iterations": self.max_generations,
                "num_trips": len(trips),
            }

        population: List[List[int]] = []
        for _ in range(self.pop_size):
            ind = self.stop_nodes[:]
            random.shuffle(ind)
            population.append(ind)

        scored_pop = [(self.evaluate_fitness(ind), ind) for ind in population]
        scored_pop.sort(key=lambda x: x[0][0])

        best_fit = scored_pop[0][0][0]
        best_trips = scored_pop[0][0][1]
        best_time = scored_pop[0][0][2]
        best_emiss = scored_pop[0][0][3]
        best_dist = scored_pop[0][0][4]

        convergence_history: List[float] = [round(best_fit, 2)]

        for gen in range(1, self.max_generations):
            new_population: List[List[int]] = []

            for i in range(self.elitism_count):
                new_population.append(scored_pop[i][1][:])

            while len(new_population) < self.pop_size:
                tourn1 = random.sample(scored_pop, 3)
                parent1 = min(tourn1, key=lambda x: x[0][0])[1]

                tourn2 = random.sample(scored_pop, 3)
                parent2 = min(tourn2, key=lambda x: x[0][0])[1]

                if random.random() < self.crossover_rate:
                    child = self.order_crossover(parent1, parent2)
                else:
                    child = parent1[:]

                if random.random() < self.mutation_rate:
                    child = self.mutate_inversion(child)

                new_population.append(child)

            population = new_population
            scored_pop = [(self.evaluate_fitness(ind), ind) for ind in population]
            scored_pop.sort(key=lambda x: x[0][0])

            curr_best_fit = scored_pop[0][0][0]
            if curr_best_fit < best_fit:
                best_fit = curr_best_fit
                best_trips = scored_pop[0][0][1]
                best_time = scored_pop[0][0][2]
                best_emiss = scored_pop[0][0][3]
                best_dist = scored_pop[0][0][4]

            convergence_history.append(round(best_fit, 2))

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        flattened_route: List[int] = []
        for trip_idx, trip in enumerate(best_trips):
            if trip_idx == 0:
                flattened_route.extend(trip)
            else:
                flattened_route.extend(trip[1:])

        return {
            "algorithm": "Genetic Algorithm",
            "best_cost": round(best_fit, 2),
            "raw_cost": round(best_time, 2),
            "emissions_g": round(best_emiss, 2),
            "distance_m": round(best_dist, 2),
            "best_route": flattened_route,
            "trips": best_trips,
            "convergence": convergence_history,
            "runtime_ms": elapsed_ms,
            "iterations": self.max_generations,
            "num_trips": len(best_trips),
        }


class GreedyNearestNeighborOptimizer:
    """
    Greedy Nearest-Neighbor heuristic guided by Dijkstra graph weights.
    Provides deterministic baseline comparison.
    """

    def __init__(
        self,
        cost_matrix: List[List[float]],
        stop_nodes: List[int],
        start_node: int,
        demands: Dict[int, int],
        vehicle_capacity: int = 35,
        distance_matrix: Optional[List[List[float]]] = None,
        routing_preference: str = "fastest",
        vehicle_type: str = "ice"
    ):
        self.cost_matrix = cost_matrix
        self.distance_matrix = distance_matrix or cost_matrix
        self.stop_nodes = stop_nodes
        self.start_node = start_node
        self.demands = demands
        self.vehicle_capacity = vehicle_capacity
        self.routing_preference = routing_preference
        self.vehicle_type = vehicle_type
        self.all_nodes = [start_node] + [s for s in stop_nodes if s != start_node]
        self.node_to_idx = {node: i for i, node in enumerate(self.all_nodes)}

    def optimize(self) -> Dict[str, Any]:
        start_time = time.perf_counter()
        unvisited = set(self.stop_nodes)
        curr_node = self.start_node
        greedy_permutation = []

        while unvisited:
            curr_idx = self.node_to_idx[curr_node]
            closest_stop = min(unvisited, key=lambda candidate: self.cost_matrix[curr_idx][self.node_to_idx[candidate]])
            greedy_permutation.append(closest_stop)
            unvisited.remove(closest_stop)
            curr_node = closest_stop

        fitness, trips, t_time, t_emiss, t_dist = evaluate_baseline_metrics(
            permutation=greedy_permutation,
            start_node=self.start_node,
            demands=self.demands,
            vehicle_capacity=self.vehicle_capacity,
            cost_matrix=self.cost_matrix,
            distance_matrix=self.distance_matrix,
            node_to_idx=self.node_to_idx,
            routing_preference=self.routing_preference,
            vehicle_type=self.vehicle_type
        )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        flattened = [node for trip in trips for node in trip[:-1]] + [self.start_node]

        return {
            "algorithm": "Greedy Nearest Neighbor",
            "best_cost": round(fitness, 2),
            "raw_cost": round(t_time, 2),
            "emissions_g": round(t_emiss, 2),
            "distance_m": round(t_dist, 2),
            "best_route": flattened,
            "trips": trips,
            "convergence": [round(fitness, 2)],
            "runtime_ms": elapsed_ms,
            "iterations": 1,
            "num_trips": len(trips),
        }
