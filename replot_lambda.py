"""Regenerate fig_big_sweep.pdf from known sweep results (no CPLEX needed)."""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# --- known sweep results from the calibration run ---
bigs       = [10,   50,    100,   200,   500,   1000,  2000,  5000,  10000, 20000, 50000]
transports = [648.73, 702.48, 719.53, 730.07, 731.52, 734.04, 743.49, 743.49, 743.49, 743.49, 743.49]
unmets     = [5.0943, 2.8740, 2.6210, 2.5441, 2.5380, 2.5349, 2.5277, 2.5277, 2.5277, 2.5277, 2.5277]

color_t = '#1a6b2e'   # dark green  – transport cost
color_u = '#c0392b'   # red         – unmet demand

fig, ax1 = plt.subplots(figsize=(8, 5.0))

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

# mark chosen λ=2000
chosen_idx = bigs.index(2000)
ax1.axvline(x=2000, color='navy', linestyle=':', linewidth=1.4, alpha=0.7)

# annotation in stable zone (right of vertical line), clear of both curves
ax1.annotate('λ = 2,000\n(chosen)',
             xy=(2000, transports[chosen_idx]),
             xytext=(5500, transports[chosen_idx] - 22),
             fontsize=8.5, color='navy',
             arrowprops=dict(arrowstyle='->', color='navy', lw=1.1,
                             connectionstyle='arc3,rad=0.3'))

# shade stable zone
ax1.axvspan(2000, 60000, alpha=0.07, color='navy')

ax1.set_xlim(8, 60000)
ax1.set_xticks(bigs)
ax1.set_xticklabels([str(b) for b in bigs], rotation=35, ha='right', fontsize=8)

# legend BELOW the x-axis — avoids all overlap
lines  = [l1, l2]
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels,
           loc='upper center',
           bbox_to_anchor=(0.5, -0.28),
           ncol=2, fontsize=10, framealpha=0.9)

plt.title('λ Penalty Sensitivity: Transport Cost vs. Unmet Demand', fontsize=12, pad=10)
plt.tight_layout()

outpath = os.path.join('Final Report', 'fig_big_sweep.pdf')
plt.savefig(outpath, bbox_inches='tight', dpi=200)
print(f'Saved to {outpath}')
