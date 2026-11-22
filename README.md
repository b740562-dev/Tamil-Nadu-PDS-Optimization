# Tamil Nadu PDS Optimization — BTP Project

**Bachelor Thesis Project (BTP) | IIT Delhi**

Optimization of the Tamil Nadu Public Distribution System (PDS) procurement and logistics network using linear programming and network flow techniques.

---

## 📁 Repository Structure

```
├── optimization_model.ipynb          # Main LP optimization model
├── model_enhancements.ipynb          # Model extensions & sensitivity analysis
├── weighbridge_routing.ipynb         # Weighbridge routing analysis
├── network_routing_combined.ipynb    # Combined network routing model
│
├── parameter_sweep.py                # Full parameter sweep across scenarios
├── parameter_sweep_config.py         # Sweep configuration & base settings
├── lambda_sensitivity_plot.py        # Lambda parameter sensitivity plots
├── solution_verification.py          # Result verification & validation
│
├── rail_routes.csv                   # Rail route network data
├── rail_shares.csv                   # Rail mode share data
├── optimal_flows.csv                 # Optimized commodity flow results
├── weighbridge_plan.csv              # Weighbridge allocation plan
├── weighbridge_legs.csv              # Route leg data for weighbridges
├── weighbridge_rail_legs.csv         # Rail leg data for weighbridges
│
├── Backend/
│   └── input_dataset.xlsx            # Processed input dataset
│
├── Final Report/
│   └── BTP_Final_Report.pdf          # Final BTP report
│
├── BTP_MidTerm_Report.pdf            # Mid-term progress report
├── BTP_EndTerm_Presentation.pptx     # End-term presentation slides
└── BTP_MidTerm_Presentation.pptx    # Mid-term presentation slides
```

---

## 🔧 Requirements

- Python 3.8+
- IBM CPLEX (or `docplex`)
- `pandas`, `numpy`, `matplotlib`, `networkx`

---

## 📄 Reports & Presentations

| Document | Description |
|---|---|
| [Final Report](Final%20Report/BTP_Final_Report.pdf) | End-term BTP report |
| [Mid-Term Report](BTP_MidTerm_Report.pdf) | Mid-term progress report |
| [End-Term Presentation](BTP_EndTerm_Presentation.pptx) | Final presentation slides |
| [Mid-Term Presentation](BTP_MidTerm_Presentation.pptx) | Mid-term presentation slides |
