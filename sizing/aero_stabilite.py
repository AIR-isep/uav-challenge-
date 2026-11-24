#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aérodynamique, stabilité longitudinale, centrage et points de fonctionnement — v3.
Lit resultats/dimensionnement_v3.json (sortie de dimensionnement_v3.py) et écrit
resultats/aero_stabilite.md + figures.

Méthodes : ligne portante simplifiée (pente de portance finie), polaire parabolique,
point neutre par volume d'empennage avec déflexion, marge statique, centrage par
inventaire des masses, contraintes dans les poutres, points de fonctionnement moteurs
par théorie du disque. Ordres de grandeur pour un dossier étudiant ; à recaler sur
XFLR5 / essais en vol.
"""
import json, math, os
RHO, G = 1.225, 9.81
here = os.path.dirname(os.path.abspath(__file__)); res_dir = os.path.join(here, "resultats")
D = json.load(open(os.path.join(res_dir, "dimensionnement_v3.json"), encoding="utf-8"))
p = D["reference"]["perf"]; aero = D["aero"]
m, S, b, c = p["mass_kg"], p["S_m2"], p["span_m"], p["chord_m"]
AR, e, CD0 = aero["AR"], aero["e"], aero["CD0"]

# --- Profil et aile (Clark Y imprimé, hypothèses)
a0 = 5.7            # pente de portance 2D (1/rad), un peu sous 2*pi pour un profil imprimé
alpha0 = -3.0       # incidence de portance nulle (deg)
CLmax = aero["CLmax"]
aw = a0 / (1 + a0 / (math.pi * AR * e))   # pente de portance aile finie (1/rad)

def polar():
    rows = []
    for al in range(-4, 15):
        CL = min(CLmax, aw * math.radians(al - alpha0))
        CD = CD0 + CL ** 2 / (math.pi * AR * e)
        rows.append(dict(alpha=al, CL=round(CL, 3), CD=round(CD, 4), LD=round(CL / CD, 1) if CL > 0 else 0))
    return rows

# --- Empennage porté par les poutres
lt = 0.80           # bras de levier CG -> 25 % de l'empennage horizontal (m)
Vh, Vv = 0.50, 0.04 # coefficients de volume (avion lent stable)
St = Vh * S * c / lt
Sv = Vv * S * b / lt
ARt = 4.0
at = a0 / (1 + a0 / (math.pi * ARt * 0.9))
deps = 2 * aw / (math.pi * AR)              # d(epsilon)/d(alpha), déflexion
eta_t = 0.9
x_ac = 0.25                                 # foyer aile en fraction de corde
x_np = x_ac + eta_t * Vh * (at / aw) * (1 - deps)   # point neutre (fraction de corde, sans contribution fuselage)
x_np_fus = x_np - 0.03                       # fuselage déstabilisant : -3 % de corde (estimation)
SM_target = 0.12
x_cg_target = x_np_fus - SM_target           # en fraction de corde depuis le bord d'attaque

# --- Inventaire des masses pour le centrage (x depuis le nez du fuselage, m ; l'aile est posée avec son bord
#     d'attaque à x_LE). Positions = proposition d'implantation, à ajuster en CAO.
x_LE = 0.18
comp = [  # (nom, masse g, x m)
    ("Caméra + LiDAR (nez)", 115, 0.03), ("Contrôleur de vol + GPS + RX", 47, 0.14),
    ("Raspberry Pi 5 + BEC", 90, 0.20), ("Pack 6S2P (sous l'aile, réglable)", 958, 0.19),
    ("Soute : charge 250 g + second drone 250 g", 500, 0.29), ("Fuselage + patins", 220, 0.22),
    ("Aile (peau, nervures, longerons, servos)", 700, x_LE + 0.40 * c), ("Poutres x2 (1,2 m)", 200, 0.52),
    ("Moteurs avant + nacelles tilt + servos (x2)", 2 * (118 + 17 + 25 + 73 + 20), -0.06),
    ("Moteurs arrière + nacelles (x2)", 2 * (118 + 17 + 25), 0.58),
    ("ESC + câblage", 115, 0.24), ("Empennage + servos", int(0.2 * S * 800) + 40, x_LE + lt + 0.10),
]
mt = sum(w for _, w, _ in comp)
x_cg = sum(w * x for _, w, x in comp) / mt
x_cg_c = (x_cg - x_LE) / c
SM = x_np_fus - x_cg_c

# --- Vitesses caractéristiques
W = m * G
V_stall = math.sqrt(2 * W / (RHO * S * CLmax))
V_trans = math.sqrt(2 * W / (RHO * S * 0.8))      # CL 0,8 : l'aile porte tout avec marge
V_md = math.sqrt(2 * W / (RHO * S)) / (math.pi * AR * e * CD0) ** 0.25  # vitesse de traînée mini
V_mp = V_md / 3 ** 0.25                            # puissance mini

# --- Poutres : flexion sous poussée max d'un moteur (arrêt brutal, rafale) et sous atterrissage
T_max = 2.4 * G
arm_front, arm_rear = 0.30, 0.35
def tube_sigma(M, Do, Di):
    I = math.pi / 64 * (Do ** 4 - Di ** 4); return M * (Do / 2) / I
sig_boom = tube_sigma(T_max * arm_rear * 1.5, 14e-3, 12e-3) / 1e6
sig_boom_12 = tube_sigma(T_max * arm_rear * 1.5, 12e-3, 10e-3) / 1e6

# --- Points de fonctionnement moteurs (par moteur)
P_h = p["P_hover_W"] / 4
P_trans = p["batt_watt_max_param"] / 4
P_cruise_front = p["P_cruise_W"] / 2
I6S = lambda P: P / 22.2
# puissance réelle estimée en croisière si les 2 moteurs arrière restent en rotation (pas d'arrêt) : +15 % traînée
P_cruise_all4 = p["P_cruise_W"] * 1.15

# --- Second drone : micro quad 3,5", 250 g, 3S 850 mAh
m2 = 0.25; d2 = 3.5 * 0.0254; A2 = math.pi * (d2 / 2) ** 2
P2 = 4 * (m2 * G / 4) ** 1.5 / math.sqrt(2 * RHO * A2) / 0.55 / 0.75
E2 = 3 * 3.7 * 0.85 * 0.8
t2 = E2 / P2 * 60

L = ["# Aérodynamique, stabilité, centrage, points de fonctionnement (v3)", ""]
L += [f"Aile : S = {S} m², b = {b} m, c = {c*100:.1f} cm, AR = {AR}. Pente de portance aile finie a = {aw:.2f} /rad (profil 2D {a0} /rad, α0 = {alpha0}°).", ""]
L += ["## Polaire estimée", "", "| α (°) | CL | CD | L/D |", "|---|---|---|---|"] + [f"| {r['alpha']} | {r['CL']} | {r['CD']} | {r['LD']} |" for r in polar()]
L += ["", "## Vitesses caractéristiques", "", f"- Décrochage : {V_stall:.1f} m/s (CLmax {CLmax})", f"- Fin de transition (aile porte tout à CL 0,8) : {V_trans:.1f} m/s → régler AIRSPEED_MIN ≈ {V_stall*1.25:.0f} m/s, Q_ASSIST_SPEED ≈ {V_stall*1.25-3:.0f} m/s",
      f"- Traînée minimale (finesse max) : {V_md:.1f} m/s ; puissance minimale : {V_mp:.1f} m/s ; croisière retenue 15 m/s", ""]
L += ["## Empennage et stabilité longitudinale", "", f"- Bras de levier {lt} m (poutres), Vh = {Vh}, Vv = {Vv} → stabilisateur {St*1e4:.0f} cm² (ex. {math.sqrt(St*ARt)*100:.0f} × {math.sqrt(St/ARt)*100:.0f} cm), dérive {Sv*1e4:.0f} cm² au total (2 dérives sur poutres de {Sv/2*1e4:.0f} cm²)",
      f"- Point neutre : {x_np_fus*100:.0f} % de la corde (aile+empennage {x_np*100:.0f} %, fuselage −3 %)", f"- CG cible pour une marge statique de {SM_target*100:.0f} % : **{x_cg_target*100:.0f} % de la corde**, soit {x_LE*100 + x_cg_target*c*100:.0f} cm du nez", ""]
L += ["## Centrage avec l'implantation proposée", "", "| Élément | Masse (g) | x depuis le nez (cm) |", "|---|---|---|"] + [f"| {n} | {w} | {x*100:.0f} |" for n, w, x in comp]
L += [f"| **Total** | **{mt}** | **{x_cg*100:.1f}** |", "", f"CG obtenu : {x_cg_c*100:.0f} % de la corde → marge statique **{SM*100:.0f} %** ({'OK' if 0.08 <= SM <= 0.18 else 'À CORRIGER : déplacer le pack'}). Le pack (958 g) coulisse dans le fuselage : 1 cm de pack = {958/mt*1*100/ (c*100):.1f} % de corde de CG.", ""]
x_rot = (-0.06 + 0.58) / 2
L += [f"**Stationnaire** : le centre des 4 rotors (moteurs avant à −6 cm, arrière à 58 cm du nez) est à {x_rot*100:.0f} cm du nez : il coïncide avec le CG avion à ±{abs(x_rot-x_cg)*100:.1f} cm. Entraxe des rotors 64 × 64 cm, garde hélice 10\" au bord de fuite ≈ 3 cm.", ""]
L += ["## Contraintes dans les tubes", "", f"- Longeron principal Ø{p['spar']['Do_mm']:.0f}/{p['spar']['Di_mm']:.0f} : {p['spar']['sigma_MPa']:.0f} MPa à 4 g × 1,5 (admissible 400 MPa)",
      f"- Poutre moteur Ø14/12 sous poussée max arrière (2,4 kg × 1,5 à 0,35 m) : {sig_boom:.0f} MPa ; en Ø12/10 : {sig_boom_12:.0f} MPa → Ø14/12 retenu pour la rigidité en torsion", ""]
L += ["## Points de fonctionnement moteurs (par moteur, 6S)", "", "| Phase | Puissance (W) | Courant (A) | Commentaire |", "|---|---|---|---|",
      f"| Stationnaire | {P_h:.0f} | {I6S(P_h):.1f} | 4 moteurs, {p['hover_g_per_W']} g/W |",
      f"| Transition / rafale (plafond BATT_WATT_MAX) | {P_trans:.0f} | {I6S(P_trans):.1f} | pack 70 A continus, pointes courtes |",
      f"| Croisière, 2 moteurs avant | {P_cruise_front:.0f} | {I6S(P_cruise_front):.1f} | hélices arrière arrêtées et alignées |",
      f"| Croisière si 4 moteurs tournent | {P_cruise_all4/4:.0f} | {I6S(P_cruise_all4/4):.1f} | +15 % de traînée estimée |", ""]
L += ["## Second drone (micro quad 3,5\", 250 g, 3S 850 mAh)", "", f"- Puissance stationnaire ≈ {P2:.0f} W, énergie utile ≈ {E2:.1f} Wh → **≈ {t2:.0f} min** de vol", "- Rôle : suivi du maître puis mission propre courte ; pas d'emport de charge.", ""]
open(os.path.join(res_dir, "aero_stabilite.md"), "w", encoding="utf-8").write("\n".join(L)); print("\n".join(L))

import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
P = polar(); fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
ax[0].plot([r["CD"] for r in P], [r["CL"] for r in P], "o-", color="#1f4e79"); ax[0].set_xlabel("CD"); ax[0].set_ylabel("CL"); ax[0].set_title("Polaire estimée")
ax[1].plot([r["alpha"] for r in P], [r["LD"] for r in P], "o-", color="#1f4e79"); ax[1].set_xlabel("α (°)"); ax[1].set_ylabel("L/D"); ax[1].set_title("Finesse")
fig.tight_layout(); fig.savefig(os.path.join(res_dir, "polaire.png"), dpi=150)
fig, ax = plt.subplots(figsize=(8, 2.2)); ax.axhline(0, color="k", lw=1)
for n, w, x in comp: ax.scatter(x * 100, 0, s=w / 4, alpha=0.6, color="#1f4e79")
ax.axvline(x_cg * 100, color="#c00"); ax.text(x_cg * 100 + 0.5, 0.3, f"CG {x_cg*100:.0f} cm", color="#c00")
ax.axvline((x_LE + x_np_fus * c) * 100, color="grey", ls="--"); ax.text((x_LE + x_np_fus * c) * 100 + 0.5, -0.45, "point neutre", color="grey")
ax.axvspan(x_LE * 100, (x_LE + c) * 100, color="#ddd", alpha=0.5); ax.text(x_LE * 100 + 1, 0.4, "corde", color="#666")
ax.set_xlabel("x depuis le nez (cm)"); ax.set_yticks([]); ax.set_title("Centrage : masses (taille = masse), CG et point neutre"); fig.tight_layout(); fig.savefig(os.path.join(res_dir, "centrage.png"), dpi=150)
