"""
QuantumRoute Engine - Dedicated Optimization & Graph Microservice
FastAPI Microservice (SIH PS 26137)
Exposes:
- POST /api/graph/matrix (Central Delhi OSMnx road graph distance/time matrix)
- POST /api/optimize (QPSO CVRP route solver)
- GET /api/benchmark/convergence (Convergence benchmark results)
- GET /api/benchmark/scalability (Scalability benchmark results)
- GET /health (Microservice health check)
"""

import os
import json
from typing import List, Dict, Any, Optional, Union
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from engine.graph_service import road_graph_service
from engine.qpso import QPSOCVRPSolver

app = FastAPI(
    title="QuantumRoute Engine Microservice",
    description="Dedicated OSMnx Real Road Graph & QPSO Optimization Microservice for SIH PS 26137",
    version="1.0.0"
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MatrixRequest(BaseModel):
    coords: List[List[float]] = Field(
        ...,
        description="List of [latitude, longitude] coordinate pairs",
        example=[[28.6316, 77.2217], [28.6330, 77.2190], [28.6280, 77.2250]]
    )
    traffic_shock: Optional[bool] = Field(
        default=False,
        description="Whether to apply edge-weight congestion shock penalties"
    )


class OptimizeCVRPRequest(BaseModel):
    coords: Optional[List[List[float]]] = None
    demands: Optional[Dict[str, float]] = None
    vehicle_capacity: float = Field(default=50.0, ge=10.0, le=500.0)
    traffic_shock: Optional[bool] = False
    num_particles: int = Field(default=35, ge=10, le=100)
    max_iterations: int = Field(default=100, ge=20, le=300)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "QuantumRoute Optimization & Graph Microservice",
        "graph_source": road_graph_service.loaded_source,
        "nodes_loaded": len(road_graph_service.node_ids)
    }


@app.post("/api/graph/matrix")
def get_graph_matrix(
    payload: Union[MatrixRequest, List[List[float]]] = Body(...)
):
    """
    Accepts an array of [lat, lng] coordinates (either directly or via { coords, traffic_shock }).
    Snaps coordinates to the nearest network nodes in Central Delhi,
    applies edge-weight congestion penalties when traffic_shock=True,
    and returns a true road-network distance and travel-time matrix.
    """
    if isinstance(payload, list):
        coords = payload
        traffic_shock = False
    else:
        coords = payload.coords
        traffic_shock = bool(payload.traffic_shock)

    if not coords or len(coords) < 1:
        raise HTTPException(status_code=400, detail="Coordinate list cannot be empty")

    matrix_result = road_graph_service.compute_matrix(coords, traffic_shock=traffic_shock)
    return matrix_result


@app.post("/api/optimize")
def optimize_cvrp(req: OptimizeCVRPRequest):
    """
    Optimizes a CVRP instance using the QPSO Engine on the true road graph matrix.
    """
    coords = req.coords or [
        [28.6316, 77.2217],
        [28.6330, 77.2190],
        [28.6280, 77.2250],
        [28.6350, 77.2220]
    ]

    # Compute graph matrix
    matrix_res = road_graph_service.compute_matrix(coords, traffic_shock=bool(req.traffic_shock))
    cost_matrix = matrix_res["duration_matrix"]
    dist_matrix = matrix_res["distance_matrix"]

    # Demands dictionary
    demands: Dict[int, float] = {}
    if req.demands:
        demands = {int(k): float(v) for k, v in req.demands.items()}
    else:
        for i in range(1, len(coords)):
            demands[i] = 5.0

    solver = QPSOCVRPSolver(
        cost_matrix=cost_matrix,
        distance_matrix=dist_matrix,
        stop_demands=demands,
        depot_index=0,
        vehicle_capacity=req.vehicle_capacity,
        num_particles=req.num_particles,
        max_iterations=req.max_iterations
    )
    result = solver.solve()
    result["matrix_source"] = matrix_res["source"]
    result["traffic_shock"] = req.traffic_shock
    return result


@app.get("/api/benchmark/convergence")
def get_convergence_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_path = os.path.join(base_dir, "web", "public", "data", "convergence_benchmark.json")
    if os.path.exists(target_path):
        with open(target_path, "r", encoding="utf-8") as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Convergence benchmark not yet generated. Run benchmark_suite.py first.")


@app.get("/api/benchmark/scalability")
def get_scalability_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_path = os.path.join(base_dir, "web", "public", "data", "scalability_benchmark.json")
    if os.path.exists(target_path):
        with open(target_path, "r", encoding="utf-8") as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Scalability benchmark not yet generated. Run benchmark_suite.py first.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("engine.main:app", host="127.0.0.1", port=8001, reload=True)
