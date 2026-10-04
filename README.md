# Q-Reach: Quantum-Inspired Intelligent Traffic Route Optimization

> **Smart India Hackathon 2026 — SIH26137**

Q-Reach is a traffic-aware route optimization platform designed for **urban transportation, vehicle routing, and intelligent transportation systems**. It uses **Quantum Particle Swarm Optimization (QPSO)** to solve routing problems on a weighted road network under changing traffic conditions.

The system combines a road-network graph, dynamic traffic conditions, shortest-path computation, vehicle-routing constraints, and metaheuristic optimization into a single workflow.

The objective is to find feasible routes that reduce **travel time, distance, and traffic congestion** while evaluating the performance of QPSO against conventional optimization methods.

---

## Key Features

### Traffic-Aware Routing

Each road segment is assigned a dynamic cost based on its distance, travel time, and congestion level.

This allows the route optimizer to respond to changing traffic conditions instead of relying only on static road distances.

### Quantum Particle Swarm Optimization

Q-Reach uses **Quantum Particle Swarm Optimization (QPSO)** as its primary metaheuristic.

QPSO uses a quantum-inspired position update based on the mean-best position, personal best, global best, and a contraction-expansion parameter.

### Interactive Map & Clean Light UI/UX

The web application provides a clean, modern **Light-Theme UI** featuring:

- **Interactive Leaflet Map** with OpenStreetMap / CartoDB light tiles, custom stop pins, depot marker, and vehicle route polylines.
- **Turn-by-turn guidance** for fleet drivers.
- **Convergence & Scalability charts** powered by Recharts.
- **Scenario presets** (Connaught Place Rush Hour, EV Green Fleet, Hospital Emergency Corridor).
- **Vercel deployment ready** with integrated Python serverless functions.

---

## Quick Start (Local Development)

### Prerequisites

- **Node.js** (v18+)
- **Python** (3.10+)

### 1. Run using One-Click Launcher

- **Linux / macOS**:
  ```bash
  chmod +x run_app.sh
  ./run_app.sh
  ```

- **Windows**:
  ```cmd
  run_app.bat
  ```

### 2. Manual Startup

**Terminal 1 (Python FastAPI Backend)**:
```bash
pip install -r backend/requirements.txt
PYTHONPATH=. python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 (Next.js Frontend)**:
```bash
npm install
npm run dev
```

Visit the app at `http://localhost:3000`.

---

## Vercel Deployment

This project is configured for **1-click Vercel deployment** with Next.js frontend and Python serverless functions under `api/index.py`.

1. Import this repository in [Vercel](https://vercel.com/new).
2. Framework Preset: **Next.js**.
3. Deploy!

---

## Running Tests

### Backend Optimization Tests

```bash
PYTHONPATH=. python backend/test_algorithms.py
python test_eco.py
```

### Frontend Build Test

```bash
npm run build
```

---

## License

MIT License.
