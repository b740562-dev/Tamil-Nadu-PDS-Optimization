import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ── load model setup (cells 1-5 from model_enhancements.ipynb) ──────────────
exec(open('big_sweep_base.py', encoding='utf-8').read(), globals())

# ── BIG sweep ────────────────────────────────────────────────────────────────
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

BIG_VALUES = [10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000]

results = []
for big in BIG_VALUES:
    print(f'Solving BIG={big} ...', flush=True)
    # patch global BIG used inside solve_model
    globals()['BIG'] = big
    r = solve_model(d_km=150, u_min=0.0, enforce_rh_cap=True,
                    rh_cap_scale=1.0, msg=False, time_limit=600)
    transport = r.get('transport', 0.0) or 0.0
    unmet     = r.get('unmet', 0.0)     or 0.0
    status    = r.get('status', '?')
    obj       = r.get('objective', None)
    results.append({'big': big, 'transport': transport,
                    'unmet': unmet, 'status': status, 'objective': obj})
    print(f'  status={status}  transport={transport/1e6:.3f}M  unmet={unmet/1e6:.4f}M')

# ── plot ──────────────────────────────────────────────────────────────────────
bigs       = [r['big']       for r in results]
transports = [r['transport'] / 1e6 for r in results]   # M quintal-km
unmets     = [r['unmet']     / 1e6 for r in results]   # M quintals

fig, ax1 = plt.subplots(figsize=(8, 4.5))

color_t = '#1a6b2e'   # dark green  – transport cost
color_u = '#c0392b'   # red         – unmet demand

ax1.set_xlabel('Penalty coefficient λ (₹ per unmet quintal-km)', fontsize=11)
ax1.set_ylabel('Transport cost (million quintal-km)', color=color_t, fontsize=11)
l1, = ax1.semilogx(bigs, transports, 'o-', color=color_t,
                   linewidth=2, markersize=6, label='Transport cost')
ax1.tick_params(axis='y', labelcolor=color_t)
ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.1f'))

ax2 = ax1.twinx()
ax2.set_ylabel('Unmet demand (million quintals)', color=color_u, fontsize=11)
l2, = ax2.semilogx(bigs, unmets, 's--', color=color_u,
                   linewidth=2, markersize=6, label='Unmet demand')
ax2.tick_params(axis='y', labelcolor=color_u)
ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.3f'))

# mark chosen lambda=2000
chosen_idx = bigs.index(2000)
ax1.axvline(x=2000, color='navy', linestyle=':', linewidth=1.4, alpha=0.7)
# annotation placed in the stable zone (right of vertical line) to avoid overlap
ax1.annotate('λ = 2,000\n(chosen)',
             xy=(2000, transports[chosen_idx]),
             xytext=(5000, transports[chosen_idx] - 20),
             fontsize=8.5, color='navy',
             arrowprops=dict(arrowstyle='->', color='navy', lw=1.1,
                             connectionstyle='arc3,rad=0.3'))

# shade stable zone (lambda >= 2000)
ax1.axvspan(2000, 60000, alpha=0.07, color='navy', label='Stable zone')

ax1.set_xlim(8, 60000)
ax1.set_xticks(bigs)
ax1.set_xticklabels([str(b) for b in bigs], rotation=35, ha='right', fontsize=8)

lines = [l1, l2]
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='center right', fontsize=9, framealpha=0.9)

plt.title('λ Penalty Sensitivity: Transport Cost vs. Unmet Demand', fontsize=12, pad=10)
plt.tight_layout()
outpath = os.path.join('Final Report', 'fig_big_sweep.pdf')
plt.savefig(outpath, bbox_inches='tight', dpi=200)
print(f'\nPlot saved to {outpath}')

# print table
print('\nBIG | Transport (M qkm) | Unmet (M qt) | Status')
print('-'*55)
for r in results:
    print(f"{r['big']:>6} | {r['transport']/1e6:>18.3f} | {r['unmet']/1e6:>12.4f} | {r['status']}")
