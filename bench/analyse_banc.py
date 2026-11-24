#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyse des essais au banc : lit un ou plusieurs CSV produits par banc_essai.ino
(colonnes t_ms,cmd_us,thrust_g,volt_V,curr_A,power_W,rpm,g_per_W), moyenne chaque palier
de gaz, trace poussée/puissance/rendement et vérifie les critères de la Partie A.

Usage : python3 analyse_banc.py essai_3115_10x5.csv [essai_3110_9x45.csv ...]
Sortie : banc_resultats.png + tableau dans le terminal.
"""
import sys, csv, statistics as st
from collections import defaultdict

CRITERES = dict(thrust_min_g=1700, eff_hover_min_g_per_W=6.0, hover_thrust_g=950)   # 3,8 kg / 4 rotors = 950 g par moteur

def load(path):
    rows = list(csv.DictReader((l for l in open(path, encoding="utf-8") if not l.startswith("#"))))
    by = defaultdict(list)
    for r in rows:
        try: by[int(r["cmd_us"])].append({k: float(v) for k, v in r.items()})
        except ValueError: pass
    out = []
    for cmd in sorted(by):
        g = by[cmd][len(by[cmd]) // 2:]           # seconde moitié du palier : régime établi
        if len(g) < 5: continue
        m = {k: st.mean(x[k] for x in g) for k in ("thrust_g", "volt_V", "curr_A", "power_W", "rpm")}
        m["cmd_us"] = cmd; m["g_per_W"] = m["thrust_g"] / m["power_W"] if m["power_W"] > 1 else 0
        out.append(m)
    return out

def interp(points, key_x, x, key_y):
    pts = sorted(points, key=lambda p: p[key_x])
    for a, b in zip(pts, pts[1:]):
        if a[key_x] <= x <= b[key_x]:
            f = (x - a[key_x]) / (b[key_x] - a[key_x] or 1); return a[key_y] + f * (b[key_y] - a[key_y])
    return None

def main(paths):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(13, 4))
    print(f"{'essai':28}{'poussée max (g)':>16}{'P max (W)':>10}{'I max (A)':>10}{'g/W à 950 g':>12}{'verdict':>10}")
    for p in paths:
        d = load(p); name = p.rsplit("/", 1)[-1].replace(".csv", "")
        tmax = max(x["thrust_g"] for x in d); pmax = max(x["power_W"] for x in d); imax = max(x["curr_A"] for x in d)
        eff = interp(d, "thrust_g", CRITERES["hover_thrust_g"], "g_per_W")
        ok = tmax >= CRITERES["thrust_min_g"] and eff is not None and eff >= CRITERES["eff_hover_min_g_per_W"]
        print(f"{name:28}{tmax:16.0f}{pmax:10.0f}{imax:10.1f}{(eff or 0):12.1f}{'OK' if ok else 'non':>10}")
        ax[0].plot([x["cmd_us"] for x in d], [x["thrust_g"] for x in d], "o-", label=name)
        ax[1].plot([x["thrust_g"] for x in d], [x["power_W"] for x in d], "o-", label=name)
        ax[2].plot([x["thrust_g"] for x in d], [x["g_per_W"] for x in d], "o-", label=name)
    ax[0].set_xlabel("commande (µs)"); ax[0].set_ylabel("poussée (g)"); ax[0].axhline(CRITERES["thrust_min_g"], ls="--", c="grey")
    ax[1].set_xlabel("poussée (g)"); ax[1].set_ylabel("puissance (W)")
    ax[2].set_xlabel("poussée (g)"); ax[2].set_ylabel("g/W"); ax[2].axvline(CRITERES["hover_thrust_g"], ls=":", c="grey"); ax[2].axhline(CRITERES["eff_hover_min_g_per_W"], ls="--", c="grey")
    for a in ax: a.grid(alpha=0.3); a.legend(fontsize=8)
    fig.tight_layout(); fig.savefig("banc_resultats.png", dpi=150); print("figure : banc_resultats.png")

if __name__ == "__main__":
    if len(sys.argv) < 2: print(__doc__); sys.exit(1)
    main(sys.argv[1:])
