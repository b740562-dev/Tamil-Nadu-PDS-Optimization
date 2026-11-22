# Tamil Nadu PDS Optimization

**Bachelor Thesis Project (BTP) | Department of Mechanical Engineering, IIT Delhi**

**Team:** Hemang Mathur · Krish Kalra · Kumari Bebo
**Supervisor:** Prof. Nomesh Bhojkumar Bolia
**Academic Year:** 2026–27

---

## Overview

India's Public Distribution System (PDS) is one of the largest food-grain distribution networks in the world. In Tamil Nadu, the **Tamil Nadu Civil Supplies Corporation (TNCSC)** operates a decentralised procurement model where paddy is procured locally, milled into rice, and distributed to consumers through a vast multi-echelon logistics network.

This project builds a **full-scale Linear Programming (LP) model** to find the minimum-cost paddy routing plan across the entire Tamil Nadu network — from individual procurement centres all the way to district warehouses — incorporating real weighbridge routing constraints and multi-modal transport.

---

## Problem Statement

TNCSC's paddy logistics network spans **13 surplus districts** (Cauvery delta and adjoining districts where local procurement far exceeds consumption) and **26 deficit districts** (districts with large milling capacity but insufficient local paddy). Every year, a large volume of surplus paddy must be transported across regions before milling — the routing of this paddy is a large-scale combinatorial optimisation problem.

**Given:**
- Annual supply at 2,508 procurement centres (PCs)
- Annual rice demand across 252 warehouses
- Capacities of 621 rice mills, 155 storage points, and 27 railheads
- Haversine inter-node distances, railhead route shares

**Objective:** Find a minimum-cost paddy routing plan (measured in quintal-km) that:

1. **Empties every surplus-region PC** completely
2. **Satisfies rice demand** at every warehouse, as far as possible
3. **Respects** mill capacity, paddy-to-rice outturn ratio (CONV = 0.67), and railhead throughput limits
4. **Routes inter-regional flow by road** if distance ≤ 150 km, and **by rail** otherwise
5. **Routes all road flows** through the nearest feasible weighbridge

---

## Network Structure

![Paddy logistics network](Final%20Report/figures/network.png)

The network is a multi-echelon structure with two operationally distinct regions:

| Node | Symbol | Count |
|---|---|---|
| Procurement Centre | PC | 2,508 |
| Rice Mill | Mill | 621 |
| Storage Point | SP | 155 |
| Railhead | RH | 27 |
| Warehouse | WH | 252 |

**Surplus region:** Paddy procured at a PC is dispatched to (i) local milling (PC → Mill → Warehouse), (ii) inter-regional transfer to the deficit region by road (d ≤ 150 km) or rail (d > 150 km), or (iii) buffer storage at a surplus SP for later milling.

**Deficit region:** Draws paddy from limited local procurement and from surplus-region inflows. Paddy is then milled (PC/SP/RH → Mill → Warehouse) or held in storage.

**Weighbridges:** Every road movement passes through a weighbridge. For each origin–destination pair, the weighbridge nearest to the origin (wb1) and nearest to the destination (wb2) are identified, and the route via the shorter total distance is selected.

---

## Model Scale & Results

| Metric | Value |
|---|---|
| Decision variables | 229,501 |
| Constraints | 4,905 |
| Solver | IBM CPLEX (dual-simplex) |
| Solve time | < 35 seconds |
| Optimal transport cost | **743.5 million quintal-km** |
| Inter-regional flow by rail | **21.6%** |
| Non-zero road movements (post-opt.) | 3,733 |
| Mean weighbridge detour per movement | 3.86 km |
| Network-wide road quintal-km increase | +17.6% |

---

## Model Enhancements

Three extensions to the base model were developed and evaluated:

| Enhancement | Description |
|---|---|
| **E1 — Minimum Mill Utilisation** | Adds a lower bound on each mill's inflow to prevent idle mills |
| **E2 — Road Accessibility** | Introduces a road-condition penalty on arc costs to route paddy away from flood-prone or poorly-maintained roads |
| **E3 — Railhead Capacity Scaling** | Scales per-railhead throughput cap by factor ρ to quantify the cost impact of hypothetical rail-terminal infrastructure investment |

---

## Repository Contents

| File | Description |
|---|---|
| `optimization_model.ipynb` | Main LP model implementation |
| `model_enhancements.ipynb` | Model extensions (E1, E2, E3) and analysis |
| `weighbridge_routing.ipynb` | Post-optimisation weighbridge routing |
| `parameter_sweep.py` | Full parameter sweep across model scenarios |
| `parameter_sweep_config.py` | Base sweep configuration and settings |
| `lambda_sensitivity_plot.py` | Lambda parameter sensitivity analysis plots |
| `solution_verification.py` | Result verification and validation |
| `input_dataset.xlsx` | Processed input dataset |
| `rail_routes.csv` | Rail route network data |
| `rail_shares.csv` | Railhead-to-railhead flow share data |
| `optimal_flows.csv` | Optimised commodity flow results |
| `weighbridge_plan.csv` | Weighbridge allocation plan |

---

## Tech Stack

- **Optimisation:** IBM CPLEX via `docplex`
- **Data processing:** Python (`pandas`, `numpy`)
- **Visualisation:** `matplotlib`, `networkx`
- **Notebooks:** Jupyter

---

## Reports & Presentations

| Document | Description |
|---|---|
| [Final Report](Final%20Report/BTP_Final_Report.pdf) | End-term BTP report |
| [Mid-Term Report](BTP_MidTerm_Report.pdf) | Mid-term progress report |
| [End-Term Presentation](BTP_EndTerm_Presentation.pptx) | Final presentation slides |
| [Mid-Term Presentation](BTP_MidTerm_Presentation.pptx) | Mid-term presentation slides |
