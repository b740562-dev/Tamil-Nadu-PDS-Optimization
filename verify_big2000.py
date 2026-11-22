import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

exec(open('big_sweep_base.py', encoding='utf-8').read(), globals())

globals()['BIG'] = 2000

print("Solving with BIG=2000 ...")
r = solve_model(d_km=150, u_min=0.0, enforce_rh_cap=True, rh_cap_scale=1.0, msg=False)

transport = r['transport']
unmet     = r['unmet']
status    = r['status']

print()
print("=" * 55)
print(f"  Status            : {status}")
print(f"  Transport cost    : {transport:,.0f} qkm  ({transport/1e6:.3f} M)")
print(f"  Unmet demand      : {unmet:,.0f} qt   ({unmet/1e6:.4f} M)")
print(f"  Rail share        : (read from arc flows below)")
print("=" * 55)
print()
print("REPORT TABLE VALUES (for comparison):")
print("  Transport cost    : 743,484,987 qkm  (743.485 M)")
print("  Unmet demand      : 2,527,672 qt     (2.5277 M)")
print()

diff_t = abs(transport - 743_484_987)
diff_u = abs(unmet - 2_527_672)
print(f"  Difference transport : {diff_t:,.0f} qkm")
print(f"  Difference unmet     : {diff_u:,.0f} qt")
print()
if diff_t < 1000 and diff_u < 1000:
    print("  CONFIRMED: BIG=2000 produces identical results to report tables.")
else:
    print("  DIFFERENCE DETECTED - tables need updating.")
