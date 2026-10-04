# Q-Reach: Quantum-Inspired Intelligent Traffic Route Optimization

> **Smart India Hackathon 2026 — SIH26137**

Q-Reach is a traffic-aware route optimization platform designed for **urban transportation, vehicle routing, and intelligent transportation systems**. It uses **Quantum Particle Swarm Optimization (QPSO)** to solve routing problems on a weighted road network under changing traffic conditions.

The system combines a road-network graph, dynamic traffic conditions, shortest-path computation, vehicle-routing constraints, and metaheuristic optimization into a single workflow.

The objective is to find feasible routes that reduce **travel time, distance, and traffic congestion** while evaluating the performance of QPSO against conventional optimization methods.

---

## Problem Statement

**SIH26137 — Quantum-Inspired Intelligent Traffic Route Optimization in Transportation Systems Using Metaheuristic Optimization**

Large urban transportation networks create difficult routing problems because the number of possible vehicle routes grows rapidly as the number of destinations increases. Static shortest-path routing can also become inefficient when traffic conditions change.

Q-Reach addresses this problem by representing the transportation network as a **weighted graph** and applying a **quantum-inspired metaheuristic optimization framework** for vehicle routing and shortest-path problems.

The framework supports both **simulated traffic conditions** for reproducible experiments and integration with live traffic data when an external traffic provider is configured.

The optimization considers:

- Travel time
- Road distance
- Traffic congestion
- Vehicle capacity
- Delivery demand
- Route feasibility
- Changing traffic conditions

---

## How It Works

```text
                    ┌─────────────────────┐
                    │  Road Network Data  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Weighted Graph     │
                    │  Nodes + Road Edges │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Traffic Conditions  │
                    │ Live / Simulated     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Dynamic Edge Costs  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ VRP / Shortest Path │
                    │ Formulation         │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Constraint Handling │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │       QPSO          │
                    │ Optimization Engine │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Route Evaluation    │
                    └──────────┬──────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
          Route on Map    Convergence    Benchmarking
```

---

## Key Features

### Traffic-Aware Routing

Each road segment is assigned a dynamic cost based on its distance, travel time, and congestion level.

This allows the route optimizer to respond to changing traffic conditions instead of relying only on static road distances.

### Quantum Particle Swarm Optimization

Q-Reach uses **Quantum Particle Swarm Optimization (QPSO)** as its primary metaheuristic.

QPSO uses a quantum-inspired position update based on the mean-best position, personal best, global best, and a contraction-expansion parameter.

Unlike classical PSO, the implementation does not use the conventional velocity update.

### Vehicle Routing

The system supports multi-stop routing with a central depot and vehicle constraints.

For capacitated routing, delivery demand and vehicle capacity are considered when constructing feasible routes.

### Shortest-Path Computation

Shortest-path computation is used to determine road-level paths between routing nodes.

The system therefore separates two related problems:

```text
Which stops should the vehicle visit?
                +
How should the vehicle travel between them?
                =
Complete Vehicle Route
```

### Interactive Visualization

The frontend provides an interactive map for displaying:

- Road networks
- Selected stops
- Optimized routes
- Traffic conditions
- Route information
- Optimization results

Convergence and benchmark results can also be displayed through interactive charts.

---

## Mathematical Model

### Weighted Road Network

The transportation network is represented as a graph:

```text
G = (V, E)
```

where `V` represents routing nodes and `E` represents road segments.

Each edge contains routing attributes such as:

```text
distance
travel_time
congestion
speed
cost
```

The edge weight changes according to the current traffic conditions.

### Dynamic Routing Cost

For a road segment `(u,v)` at time `t`, the routing cost can be expressed as:

```text
C(u,v,t)
=
αD(u,v)
+
βT(u,v,t)
+
γH(u,v,t)
```

where:

- `D(u,v)` is road distance
- `T(u,v,t)` is travel time
- `H(u,v,t)` represents congestion cost
- `α`, `β`, and `γ` control the contribution of each objective

The total route objective combines the costs of the road segments forming the route.

---

## QPSO Formulation

For a swarm containing `M` particles, the mean-best position is calculated as:

```text
mbest(t) = (1/M) Σ Pi(t)
```

where `Pi` is the personal-best position of particle `i`.

A local attractor is generated using the particle's personal best and the swarm's global best:

```text
pi,d(t)
=
φPi,d(t)
+
(1 - φ)Gd(t)
```

The quantum-inspired position update is then:

```text
Xi,d(t+1)
=
pi,d(t)
±
α |mbestd(t) - Xi,d(t)|
ln(1/u)
```

where `u` is a random value in `(0,1)` and `α` controls the contraction-expansion behaviour of the search.

---

## Continuous-to-Discrete Route Mapping

QPSO operates on continuous particle positions, while a Vehicle Routing Problem requires a discrete ordering of stops.

Q-Reach uses **Smallest Position Value (SPV) encoding** to convert a particle into a routing permutation.

For example:

```text
Particle:
[0.71, 0.12, 0.53, 0.31]

Ascending order:
[2, 4, 3, 1]

Visiting sequence:
Stop 2 → Stop 4 → Stop 3 → Stop 1
```

This representation provides a direct mapping between the continuous optimization space and the discrete routing sequence.

---

## Constraint Handling

Vehicle routing is subject to practical constraints. Q-Reach considers constraints including:

- Vehicle capacity
- Delivery demand
- Valid stop permutations
- Depot returns
- Route feasibility
- Capacity violations

For a vehicle with capacity `C`, a feasible route must satisfy the configured demand constraint:

```text
Σ demand(i) ≤ C
```

When a vehicle reaches its capacity limit, the route can be split into feasible trips according to the routing configuration.

Penalty terms can be included in the objective function for constraint violations.

---

## Traffic Simulation

Traffic conditions can be generated as a function of time so that the same road network can be evaluated under different traffic states.

A simulated congestion factor can be represented as:

```text
c(u,v,t)
=
clip(
    c0 + A sin(2πt/T + θu,v),
    cmin,
    cmax
)
```

This provides a controlled environment for testing how route selection changes when congestion changes.

Because the traffic conditions are reproducible, the same routing instance can be supplied to different algorithms during benchmarking.

---

## Benchmarking

Q-Reach includes a benchmarking framework for comparing different routing approaches on the same problem instances.

The framework can evaluate:

- QPSO
- Classical PSO
- Genetic Algorithm
- Ant Colony Optimization
- Greedy routing baselines
- Exact optimization methods on suitable small instances

Each algorithm can be evaluated using the same:

- Transportation graph
- Routing instance
- Traffic conditions
- Objective function
- Vehicle constraints

This makes the comparison focused on the optimization method rather than changes in the input problem.

### Evaluation Metrics

| Metric | Description |
|---|---|
| Travel Time | Estimated time required to complete the route |
| Distance | Total road distance |
| Congestion Cost | Cost contributed by traffic conditions |
| Objective Value | Combined routing objective |
| Runtime | Time required by the algorithm |
| Iterations | Number of optimization iterations |
| Feasibility | Whether routing constraints are satisfied |
| Convergence | Change in objective value during optimization |
| Scalability | Behaviour as the number of stops increases |

---

## Convergence Analysis

The optimization engine records the objective value across iterations.

This makes it possible to compare the convergence behaviour of different algorithms on the same routing instance.

```text
Objective
   │
   │\
   │ \
   │  \____
   │       \____
   │            \___
   │
   └──────────────────── Iterations
```

The resulting convergence curves can be used to study:

- Improvement during optimization
- Convergence behaviour
- Solution stability
- Final objective value
- Effect of increasing problem size

---

## Scalability Testing

The system can evaluate routing instances with increasing numbers of stops.

For example:

```text
10 stops
   ↓
20 stops
   ↓
30 stops
   ↓
40 stops
   ↓
Larger instances
```

For each instance, the system can record runtime, objective value, convergence behaviour, feasibility, and other configured metrics.

This provides an experimental basis for studying the behaviour of the optimization framework on larger Vehicle Routing Problems.

---

## System Architecture

```text
┌──────────────────────┐
│   User / Operator    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ React Frontend       │
│                      │
│ • Interactive Map    │
│ • Route Controls     │
│ • Results            │
│ • Charts             │
└──────────┬───────────┘
           │ REST API
           ▼
┌──────────────────────┐
│ FastAPI Backend      │
└──────────┬───────────┘
           │
     ┌─────┴──────┐
     ▼            ▼
┌───────────┐ ┌───────────────┐
│ Graph     │ │ Optimization  │
│ Engine    │ │ Engine        │
│           │ │               │
│ NetworkX  │ │ QPSO          │
│ OSM data  │ │ PSO           │
│ Shortest  │ │ GA            │
│ Path      │ │ ACO           │
└─────┬─────┘ └───────┬───────┘
      │               │
      └───────┬───────┘
              ▼
     ┌──────────────────┐
     │ Route Evaluation │
     │                  │
     │ Time             │
     │ Distance         │
     │ Congestion       │
     │ Constraints      │
     └────────┬─────────┘
              │
              ▼
     ┌──────────────────┐
     │ Results & Maps   │
     └──────────────────┘
```

---

## Technology Stack

### Frontend

- React
- Vite
- JavaScript
- Leaflet
- Interactive charts

### Backend

- Python
- FastAPI
- NumPy
- NetworkX
- QPSO
- Classical metaheuristic algorithms

### Road Network

- OpenStreetMap road network data
- Graph-based road representation
- Dynamic traffic weights

### Development

- Git
- GitHub
- Python
- Node.js
- npm

---

## Project Structure

```text
Beyond_Orbit-Q-Reach-SIH26137/
│
├── backend/
│   ├── api.py
│   ├── graph_model.py
│   ├── qpso.py
│   ├── baselines.py
│   ├── benchmark.py
│   ├── main.py
│   ├── requirements.txt
│   └── test_algorithms.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── ControlPanel.jsx
│   │   │   ├── GraphView.jsx
│   │   │   ├── ConvergenceChart.jsx
│   │   │   ├── ResultsTable.jsx
│   │   │   ├── ScalabilityChart.jsx
│   │   │   └── HowItWorksModal.jsx
│   │   │
│   │   ├── App.jsx
│   │   └── index.css
│   │
│   ├── package.json
│   └── vite.config.js
│
├── .env.example
├── run_app.bat
├── run_app.sh
└── README.md
```

---

## Getting Started

### Prerequisites

Make sure the following are installed:

- Python 3.10 or later
- Node.js 18 or later
- npm
- Git

### Clone the Repository

```bash
git clone https://github.com/devbhatia38/Beyond_Orbit-Q-Reach-SIH26137.git
cd Beyond_Orbit-Q-Reach-SIH26137
```

### Backend

Create a virtual environment:

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Install the Python dependencies:

```bash
pip install -r backend/requirements.txt
```

Start the FastAPI server:

```bash
python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend is available at:

```text
http://127.0.0.1:5173
```

The backend runs at:

```text
http://127.0.0.1:8000
```

---

## Environment Variables

If the project configuration includes an external traffic-data provider, create a `.env` file from `.env.example` and add the required API credentials.

```bash
cp .env.example .env
```

API keys should remain local and should never be committed to the repository.

For development and benchmarking, simulated traffic can be used without requiring a live traffic service.

---

## Running Tests

The backend includes algorithm tests that can be executed with:

```bash
python -m backend.test_algorithms
```

---

## Reproducible Experiments

For meaningful algorithm comparisons, experiments should use identical input conditions.

```text
Same Road Network
        ↓
Same Stops
        ↓
Same Traffic State
        ↓
Same Vehicle Constraints
        ↓
Same Objective Function
        ↓
Different Algorithms
        ↓
Compare Results
```

This setup allows QPSO, classical metaheuristics, and exact reference methods to be evaluated on the same routing problem.

---

## Applications

Q-Reach can be used as a research and prototype platform for:

- Urban delivery routing
- Fleet route planning
- Traffic-aware logistics
- Multi-stop vehicle routing
- Congestion-aware route planning
- Smart-city logistics
- Intelligent Transportation Systems
- Dynamic transportation optimization

The framework can be adapted to different road networks, traffic scenarios, vehicle capacities, and routing requirements.

---

## Project Status

Q-Reach is being developed as a **Smart India Hackathon 2026 prototype for SIH26137**.

The current implementation focuses on the optimization engine, graph-based routing, traffic simulation, route visualization, benchmarking, convergence analysis, and scalability evaluation.

Performance results should be interpreted from the benchmark experiments generated by the implementation rather than from fixed values stated in this document.

---

## Repository

**Beyond Orbit — Q-Reach**

GitHub: https://github.com/devbhatia38/Beyond_Orbit-Q-Reach-SIH26137

Built for **Smart India Hackathon 2026**.

## License

This project is licensed under the MIT License.
