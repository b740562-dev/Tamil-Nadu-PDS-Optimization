# Tamil Nadu PDS Optimization — BTP Project

**Bachelor Thesis Project (BTP) | IIT Madras**

Optimization of the Tamil Nadu Public Distribution System (PDS) procurement and logistics network using linear programming and network flow techniques.

---

## 📁 Repository Structure

```
├── Notebooks/                         # Jupyter analysis notebooks
│   ├── mycode_final_completed.ipynb   # Main optimization model
│   ├── model_enhancements.ipynb       # Model extensions & analysis
│   ├── weighbridge_routing.ipynb      # Weighbridge routing analysis
│   └── nw_1_-_combine_RH_to_test_done.ipynb
├── Scripts/                           # Python scripts
│   ├── big_sweep.py                   # Parameter sweep (full run)
│   ├── big_sweep_base.py              # Base sweep configuration
│   ├── replot_lambda.py               # Lambda sensitivity plots
│   └── verify_big2000.py              # Result verification
├── Data/                              # Input & output data
│   ├── railvia.csv                    # Rail route data
│   ├── rail_shares.csv                # Rail mode shares
│   ├── optimal_flows.csv              # Optimized flow results
│   ├── weighbridge_plan.csv           # Weighbridge allocation plan
│   ├── weighbridge_legs.csv
│   ├── weighbridge_rail_legs.csv
│   └── Backend/Data_11.xlsx           # Processed input dataset
├── Reports/
│   ├── Final Report/main.pdf          # Final BTP report
│   └── I9 Mid-Term Report.pdf         # Mid-term report
└── Presentations/
    ├── EndTerm_BTP_I9_Presentation.pptx
    └── I9_Midterm_Report.pptx
```

---

## 🔧 Requirements

- Python 3.8+
- IBM CPLEX (or `docplex`)
- `pandas`, `numpy`, `matplotlib`, `networkx`

---

## 📄 Reports

| Document | Description |
|---|---|
| [Final Report](Final%20Report/main.pdf) | End-term BTP report |
| [Mid-Term Report](I9%20Mid-Term%20Report.pdf) | Mid-term progress report |
| [End-Term Presentation](EndTerm_BTP_I9_Presentation.pptx) | Final presentation slides |
| [Mid-Term Presentation](I9_Midterm_Report.pptx) | Mid-term presentation slides |
