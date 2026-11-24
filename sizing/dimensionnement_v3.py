#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dimensionnement v3 — VTOL quadriplan 4 moteurs (2 basculants), Dassault UAV Challenge 2026-27
Équipe ISEP. Boucle masse -> aile -> structure -> propulsion -> batterie -> autonomie -> COÛT -> SCORE.

Usage :  python3 dimensionnement_v3.py            (écrit resultats/ : json, md, png)
         python3 dimensionnement_v3.py --no-plot  (sans figures)

Toutes les hypothèses sont dans la section PARAMÈTRES. Les prix viennent de la recherche
du 4/11/2026 (pages ouvertes) ; les masses des fiches constructeur ; les rendements sont
des hypothèses d'ingénierie signalées comme telles.
"""
import json, math, os, sys, argparse

RHO = 1.225      # kg/m3, air au niveau de la mer, 15 °C
G = 9.81

# ----------------------------------------------------------------------------- PARAMÈTRES
MISSION = dict(
    t_hover_min=3.0,          # min de stationnaire par mission (décollage, largages, atterrissage)
    v_cruise=15.0,            # m/s, vitesse de croisière visée
    v_stall=11.0,             # m/s, décrochage visé
    reserve=0.20,             # réserve d'énergie
    dod=0.85,                 # profondeur de décharge Li-ion
    target_range_km=30.0,     # objectif distance (10 pts)
    target_endurance_min=45.0 # objectif autonomie
)
AERO = dict(
    CLmax=1.2,     # profil type Clark Y / NACA 4412 imprimé, sans volets (prudent)
    AR=7.0,        # allongement (corde élargie à la demande de l'équipe, v2 = 8)
    CD0=0.035,     # traînée parasite avion complet (fuselage, poutres, 4 nacelles)
    e=0.80,        # Oswald
    eta_cruise=0.50,  # hélice multirotor 10" hors point de conception + moteur + ESC (hypothèse)
    FM=0.65,       # figure de mérite rotor 10" tripale (hypothèse)
    eta_motor=0.80 # rendement moteur+ESC en stationnaire (hypothèse)
)
STRUCT = dict(
    skin_thk_mm=0.6, skin_rho=0.45,     # LW-PLA moussé g/cm3
    foam_frac=0.15, foam_rho=35.0,      # mousse PU kg/m3, 15 % du volume d'aile
    t_c=0.12,                           # épaisseur relative
    n_z=4.0, sf=1.5, sigma_adm=400e6,   # facteur de charge, sécurité, contrainte tube carbone (Pa)
    tube_rho=1600.0,                    # kg/m3 carbone pultrudé
)
# Candidats composants : masse (g), prix (€), notes. Sources : recherche du 4/11/2026.
MOTORS = {
    "3115 900KV low-cost (BrotherHobby SE / FlashHobby Mars)": dict(m=118, price=27.0, kv=900, prop_in=10, thrust_max_kg=2.4, note="poussée max 4 kg annoncée par FlashHobby, on retient 2,4 kg à 24 V avec 10x5 tripale (prudent)"),
    "3110 900KV léger (BrotherHobby Avenger / iFlight)": dict(m=77, price=41.0, kv=900, prop_in=9, thrust_max_kg=1.9, note="9-10\" ; moins lourd, plus cher"),
    "T-Motor Velox V3115 900KV": dict(m=113, price=49.9, kv=900, prop_in=10, thrust_max_kg=2.5, note="studiosport, en stock, 83 A pic"),
}
ESC = {"Sequre Blueson A2 65A 4-en-1 AM32": dict(m=25, price=44.9), "TBS Lucid 60A 4-en-1": dict(m=20, price=59.9), "4 x ESC 40A individuels": dict(m=40, price=100.0)}
PROPS = {"Gemfan 1050-3 tripale": dict(m=17, price_pair=9.39, d_in=10), "Gemfan 9045-3 tripale": dict(m=16.5, price_pair=9.9, d_in=9), "APC 11x5.5E bipale": dict(m=20, price_pair=12.0, d_in=11, verified=False)}
FC = {"SpeedyBee F405 Wing APP": dict(m=24.5, price=48.9, pwm=11), "Holybro Kakute H743-Wing": dict(m=28, price=120.0, pwm=14), "Pixhawk 6C Mini": dict(m=39, price=200.0, pwm=14)}
GPS = {"Holybro Micro M10": dict(m=14, price=33.0), "Matek M10Q-5883": dict(m=8, price=44.9), "Holybro M10 Ø50": dict(m=32, price=52.0)}
RX = {"RadioMaster RP3 récupéré du stock FPV (ELRS MAVLink)": dict(m=5, price=0.0, note="HYPOTHÈSE : récepteur ELRS déjà possédé par Quentin ; sinon 24,90 €"),
      "RadioMaster RP3 neuf (ELRS MAVLink)": dict(m=5, price=24.9), "RadioMaster ER8G": dict(m=12, price=41.0), "RP3 + radio SiK": dict(m=35, price=85.0)}
SERVO_TILT = {"Readytosky TD-8130MG 30 kg": dict(m=73, price=17.29), "DS3225 25 kg": dict(m=60, price=20.0, verified=False), "KST X10 Pro 11,5 kg": dict(m=25, price=50.0, verified=False)}
SERVO_CTRL = {"Emax ES3054HV": dict(m=20, price=16.39), "Emax ES08MD II": dict(m=13, price=14.49), "SG90-class": dict(m=9, price=3.0, note="déconseillé, pignons plastique")}
CELLS = {
    "Molicel P45B": dict(m=68, price=3.76, ah=4.5, i_cont=45),
    "Samsung 50S": dict(m=72, price=3.57, ah=5.0, i_cont=35),
    "Molicel P50B": dict(m=70, price=6.75, ah=5.0, i_cont=50),
    "Samsung 40T5": dict(m=67, price=3.18, ah=4.0, i_cont=35),
}
OBC = {"Raspberry Pi 5 4 Go + cooler + BEC": dict(m=90, price=163.0, watts=12, note="kubii 136,80 € + Active Cooler 6 € + Matek BEC12S-PRO 20,19 €"),
       "Raspberry Pi 5 8 Go + cooler + BEC": dict(m=90, price=215.0, watts=12, note="berrybase 189 € + cooler + BEC"),
       "Orange Pi 5 8 Go": dict(m=85, price=130.0, watts=10, verified=False), "Jetson Orin Nano (prêt réel)": dict(m=175, price=0.0, watts=15)}
LIDAR = {"LDRobot D500 (LD19)": dict(m=44, price=136.5, range_m=12), "Slamtec RPLidar C1": dict(m=110, price=81.12, range_m=12), "YDLIDAR T-mini Plus": dict(m=45, price=90.0, range_m=12, verified=False)}
CAMERA = {"Pi Camera Module 3 standard": dict(m=5, price=30.9, hfov_deg=66), "Pi Camera Module 3 Wide": dict(m=5, price=30.9, hfov_deg=102), "HQ Camera + 16 mm": dict(m=180, price=114.0, hfov_deg=22)}
FIXED = dict(  # masses/prix communs à toutes les variantes
    wiring=dict(m=90, price=40.0, note="inclut un second BEC 5 V pour LiDAR/caméra ; pas de batterie séparée pour l'ordinateur de bord"),
    drop_mech=dict(m=36, price=20.0),
    structure_mat=dict(m=0, price=150.0, note="3 m tube 14x12 (38 €), 2 bobines LW-PLA (53 €), 1 kg PETG (25 €), mousse PU (15 €), visserie et colle (19 €)"), misc=dict(m=0, price=5.0),
)
PAYLOAD_DROP_G = 250.0      # charge larguée
SECOND_DRONE_G = 250.0      # second drone embarqué (< 250 g)
SECOND_DRONE_PRICE = 90.0   # kit 3,5" : FC+ESC AIO ~45 €, moteurs ~30 €, GPS ~15 € ; récepteur, hélices, caméra récupérés du stock FPV (HYPOTHÈSE)
SECOND_DRONE_PRICE_NEW = 150.0
ASSOC_FUNDING_EUR = 500.0   # part financée par l'association (Numeris / AIR), le reste par la dotation Dassault
RECOVERED = dict(radio=0.0, charger=0.0)  # déjà possédés : 0 € dans le coût déclaré

# ----------------------------------------------------------------------------- SCORING
def score_points(perf, cost_eur, arch):
    """Points de la table officielle que le dimensionnement influence. perf = dict."""
    if cost_eur > 1000.0:
        return dict(total=0, eliminated=True, detail={"Coût total > 1000 € (MANDATORY)": 0})
    d = {}
    t = perf["endurance_min_with_reserve"]
    d["15 min (I)"] = 3 if t >= 15 else 0
    d["30 min (N)"] = 5 if t >= 30 else 0
    d["60 min (N)"] = 10 if t >= 60 else 0
    r = perf["range_km_with_reserve"]
    d["10 km (I)"] = 5 if r >= 10 else 0
    d["30 km (N)"] = 10 if r >= 30 else 0
    d["150 g charge (I)"] = 5 if perf["payload_g"] >= 150 else 0
    d["500 g charge (N)"] = 5 if perf["payload_g"] >= 500 else 0
    d["Bruit < 75 dB (I)"] = 5 if perf["prop_in"] >= 9 else 0   # heuristique : à mesurer
    d["Décollage/atterrissage auto voilure fixe (N)"] = 10 if arch["vtol"] else 0
    d["Vertical VTOL (N)"] = 10 if arch["vtol"] else 0
    d["Plateforme voilure fixe (N)"] = 10 if arch["fixed_wing"] else 0
    d["Second drone embarqué (N)"] = 5 if arch["second_drone"] else 0
    da = min(500.0, max(0.0, cost_eur - ASSOC_FUNDING_EUR))   # part demandée à Dassault
    d["Économies de dotation (I)"] = round(10 * (1 - da / 500), 1)
    d["Dépenses de l'équipe = 0 € (I)"] = 10
    return dict(total=sum(d.values()), eliminated=False, detail=d)

# ----------------------------------------------------------------------------- MODÈLES
def wing_geometry(m_kg):
    S = m_kg * G / (0.5 * RHO * MISSION["v_stall"] ** 2 * AERO["CLmax"])
    b = math.sqrt(AERO["AR"] * S)
    c = S / b
    return S, b, c

def cruise_power(m_kg, S):
    V = MISSION["v_cruise"]
    q = 0.5 * RHO * V ** 2
    CL = m_kg * G / (q * S)
    CD = AERO["CD0"] + CL ** 2 / (math.pi * AERO["AR"] * AERO["e"])
    D = q * S * CD
    P_elec = D * V / AERO["eta_cruise"]
    return dict(CL=CL, CD=CD, LD=CL / CD, drag_N=D, P_elec_W=P_elec)

def hover_power(m_kg, prop_in, n_rotors=4):
    d = prop_in * 0.0254
    A = math.pi * (d / 2) ** 2
    T = m_kg * G / n_rotors
    P_ideal = T ** 1.5 / math.sqrt(2 * RHO * A)
    P_elec = n_rotors * P_ideal / AERO["FM"] / AERO["eta_motor"]
    return dict(P_elec_W=P_elec, g_per_W=m_kg * 1000 / P_elec, thrust_per_rotor_kg=T / G)

def structure_mass(m_kg, S, b, c):
    """Masse structure (g) : aile peau+nervures+mousse+longerons, fuselage, poutres, empennage, nacelles, patins."""
    st = STRUCT
    skin = 2.04 * S * (st["skin_thk_mm"] / 1000) * st["skin_rho"] * 1e6  # g : S_mouillée (m²) * t (m) * rho (g/m³)
    ribs = 0.25 * skin
    wing_vol = 0.6 * S * c * st["t_c"]           # m3 approx du volume d'aile
    foam = wing_vol * st["foam_frac"] * st["foam_rho"] * 1000
    # longeron : moment d'emplanture ~ n*sf*m*g*b/8 (charge elliptique)
    M = st["n_z"] * st["sf"] * m_kg * G * b / 8
    spar = None
    for Do, Di in ((12e-3, 10e-3), (14e-3, 12e-3), (16e-3, 14e-3), (20e-3, 18e-3)):
        I = math.pi / 64 * (Do ** 4 - Di ** 4)
        sigma = M * (Do / 2) / I
        if sigma <= st["sigma_adm"]:
            spar = dict(Do_mm=Do * 1e3, Di_mm=Di * 1e3, sigma_MPa=sigma / 1e6,
                        m_g=math.pi / 4 * (Do ** 2 - Di ** 2) * b * st["tube_rho"] * 1000)
            break
    rear_spar = math.pi / 4 * (8e-3 ** 2 - 6e-3 ** 2) * b * st["tube_rho"] * 1000
    wing = skin + ribs + foam + spar["m_g"] + rear_spar + 40
    fuselage = 170.0                                   # coque 0,8 mm LW-PLA 40x14x12 cm + cadres PETG
    booms = 2 * (math.pi / 4 * (14e-3 ** 2 - 12e-3 ** 2) * 0.9 * st["tube_rho"] * 1000)  # 2 poutres 14/12 de 0,9 m
    tail = 0.20 * S * 800                              # empennage ~20 % de S à 0,8 kg/m2
    nacelles = 4 * 25 + 2 * 20                         # 4 nacelles imprimées + 2 mécanismes de basculement
    skids = 50.0
    hardware = 0.08 * (wing + fuselage + booms + tail + nacelles)
    total = wing + fuselage + booms + tail + nacelles + skids + hardware
    return dict(total_g=total, wing_g=wing, skin_g=skin, foam_g=foam, spar=spar, fuselage_g=fuselage,
                booms_g=booms, tail_g=tail, nacelles_g=nacelles, hardware_g=hardware)

def battery_pack(cell_name, parallel):
    c = CELLS[cell_name]
    n = 6 * parallel
    return dict(name=f"6S{parallel}P {cell_name}", cells=n, m_g=n * c["m"] * 1.08 + 25,   # gaine, nickel, connecteurs
                wh=6 * 3.6 * c["ah"] * parallel, i_cont=c["i_cont"] * parallel, price=n * c["price"] + 12.0)

def energy_required(P_hover, P_cruise, t_cruise_min):
    E_mission = P_hover * MISSION["t_hover_min"] / 60 + P_cruise * t_cruise_min / 60
    return E_mission * (1 + MISSION["reserve"]) / MISSION["dod"]

# ----------------------------------------------------------------------------- BOUCLE
def size(cfg, verbose=False):
    """cfg : dict des choix. Retourne l'historique d'itérations et le résultat convergé."""
    saved = (AERO["AR"], MISSION["v_cruise"])
    if cfg.get("AR"): AERO["AR"] = cfg["AR"]
    if cfg.get("v_cruise"): MISSION["v_cruise"] = cfg["v_cruise"]
    try:
        return _size(cfg)
    finally:
        AERO["AR"], MISSION["v_cruise"] = saved

def _size(cfg):
    motor = MOTORS[cfg["motor"]]; prop = PROPS[cfg["prop"]]; fc = FC[cfg["fc"]]; gps = GPS[cfg["gps"]]
    rx = RX[cfg["rx"]]; st = SERVO_TILT[cfg["servo_tilt"]]; sc = SERVO_CTRL[cfg["servo_ctrl"]]
    obc = OBC[cfg["obc"]]; lidar = LIDAR[cfg["lidar"]]; cam = CAMERA[cfg["camera"]]; esc = ESC[cfg["esc"]]
    n_tilt = cfg.get("n_tilt", 2)
    payload = PAYLOAD_DROP_G + (SECOND_DRONE_G if cfg.get("second_drone", True) else 0)
    fixed_m = 4 * motor["m"] + esc["m"] + 4 * prop["m"] + fc["m"] + gps["m"] + rx["m"] + n_tilt * st["m"] + 4 * sc["m"] \
        + obc["m"] + lidar["m"] + cam["m"] + sum(v["m"] for v in FIXED.values()) + payload
    cost = 4 * motor["price"] + esc["price"] + 3 * prop["price_pair"] + fc["price"] + gps["price"] + rx["price"] \
        + n_tilt * st["price"] + 4 * sc["price"] + obc["price"] + lidar["price"] + cam["price"] \
        + sum(v["price"] for v in FIXED.values()) + ((cfg.get("second_drone_price", SECOND_DRONE_PRICE)) if cfg.get("second_drone", True) else 0)
    t_cruise = cfg.get("t_cruise_min", MISSION["target_range_km"] * 1000 / MISSION["v_cruise"] / 60)
    m = (fixed_m + 1000) / 1000.0   # estimation initiale avec 1 kg structure+batterie
    hist = []
    for it in range(25):
        S, b, c = wing_geometry(m)
        cr = cruise_power(m, S); hv = hover_power(m, prop["d_in"])
        E_req = energy_required(hv["P_elec_W"], cr["P_elec_W"], t_cruise)
        pack = None
        for p in ((cfg["parallel"],) if cfg.get("parallel") else (1, 2, 3)):
            cand = battery_pack(cfg["cell"], p)
            i_hover = hv["P_elec_W"] / 22.2
            if cfg.get("parallel") or (cand["wh"] >= E_req and cand["i_cont"] >= 1.5 * i_hover):
                pack = cand; break
        if pack is None:
            pack = battery_pack(cfg["cell"], 3)
        struct = structure_mass(m, S, b, c)
        m_new = (fixed_m + struct["total_g"] + pack["m_g"]) / 1000.0
        hist.append(dict(it=it, m_in=round(m, 3), S=round(S, 3), b=round(b, 2), struct_g=round(struct["total_g"]),
                         pack=pack["name"], pack_g=round(pack["m_g"]), m_out=round(m_new, 3),
                         cost=round(cost + pack["price"], 0)))
        if abs(m_new - m) < 0.005:
            m = m_new; break
        m = m_new
    # résultat convergé
    S, b, c = wing_geometry(m); cr = cruise_power(m, S); hv = hover_power(m, prop["d_in"]); struct = structure_mass(m, S, b, c)
    E_usable = pack["wh"] * MISSION["dod"]
    E_hover = hv["P_elec_W"] * MISSION["t_hover_min"] / 60
    t_cruise_avail = (E_usable / (1 + MISSION["reserve"]) - E_hover) / cr["P_elec_W"] * 60
    endurance = MISSION["t_hover_min"] + max(0, t_cruise_avail)
    rng = max(0, t_cruise_avail) * 60 * MISSION["v_cruise"] / 1000
    total_cost = cost + pack["price"]
    twr = 4 * motor["thrust_max_kg"] / m
    p_pack_max = pack["i_cont"] * 21.6                      # W continus admissibles par le pack (6S à 3,6 V/élément)
    twr_pack = (p_pack_max / hv["P_elec_W"]) ** (2.0 / 3.0)  # poussée/poids atteignable sous la limite du pack (P ~ T^1.5)
    i_hover = hv["P_elec_W"] / 22.2
    perf = dict(mass_kg=round(m, 3), span_m=round(b, 2), chord_m=round(c, 3), S_m2=round(S, 3),
                wing_loading=round(m / S, 2), CL_cruise=round(cr["CL"], 2), LD=round(cr["LD"], 1),
                P_cruise_W=round(cr["P_elec_W"]), P_hover_W=round(hv["P_elec_W"]), hover_g_per_W=round(hv["g_per_W"], 1),
                i_hover_A=round(i_hover, 1), pack=pack["name"], pack_wh=round(pack["wh"]), pack_g=round(pack["m_g"]),
                endurance_min_with_reserve=round(endurance, 1), range_km_with_reserve=round(rng, 1),
                twr=round(twr, 2), pack_i_cont_A=pack["i_cont"], pack_P_max_W=round(p_pack_max), twr_under_pack_limit=round(twr_pack, 2),
                batt_watt_max_param=round(p_pack_max * 0.9, -1), thrust_needed_per_motor_kg=round(2 * m / 4, 2), prop_in=prop["d_in"], payload_g=payload,
                struct_g=round(struct["total_g"]), spar=struct["spar"], cost_eur=round(total_cost, 0))
    perf["cost_breakdown"] = {"Moteurs x4": 4 * motor["price"], "ESC": esc["price"], "Hélices (3 paires)": 3 * prop["price_pair"], "Contrôleur de vol": fc["price"],
        "GPS": gps["price"], "Récepteur": rx["price"], f"Servos basculement x{n_tilt}": n_tilt * st["price"], "Servos gouvernes x4": 4 * sc["price"],
        "Ordinateur de bord": obc["price"], "LiDAR": lidar["price"], "Caméra": cam["price"], **{k: v["price"] for k, v in FIXED.items()},
        "Second drone": (cfg.get("second_drone_price", SECOND_DRONE_PRICE)) if cfg.get("second_drone", True) else 0, "Pack batterie": pack["price"]}
    arch = dict(vtol=True, fixed_wing=True, second_drone=cfg.get("second_drone", True))
    sc_ = score_points(perf, total_cost, arch)
    return dict(cfg=cfg, hist=hist, perf=perf, struct=struct, score=sc_)

BASELINE = dict(motor="3115 900KV low-cost (BrotherHobby SE / FlashHobby Mars)", prop="Gemfan 1050-3 tripale",
                esc="Sequre Blueson A2 65A 4-en-1 AM32", fc="SpeedyBee F405 Wing APP", gps="Holybro Micro M10",
                rx="RadioMaster RP3 récupéré du stock FPV (ELRS MAVLink)", servo_tilt="Readytosky TD-8130MG 30 kg", servo_ctrl="Emax ES3054HV",
                obc="Raspberry Pi 5 4 Go + cooler + BEC", lidar="Slamtec RPLidar C1", camera="Pi Camera Module 3 standard",
                cell="Samsung 50S", parallel=2, second_drone=True, n_tilt=2)

def variants():
    V = {"v3 référence": dict(BASELINE)}
    V["Moteurs 3110 légers"] = dict(BASELINE, motor="3110 900KV léger (BrotherHobby Avenger / iFlight)", prop="Gemfan 9045-3 tripale")
    V["Moteurs T-Motor V3115"] = dict(BASELINE, motor="T-Motor Velox V3115 900KV")
    V["FC Kakute H743-Wing"] = dict(BASELINE, fc="Holybro Kakute H743-Wing")
    V["LiDAR D500 léger"] = dict(BASELINE, lidar="LDRobot D500 (LD19)")
    V["Pack 6S1P Molicel P45B (léger, puissance limitée)"] = dict(BASELINE, cell="Molicel P45B", parallel=1)
    V["Pack 6S1P Molicel P50B"] = dict(BASELINE, cell="Molicel P50B", parallel=1)
    V["Pack 6S2P Samsung 40T5"] = dict(BASELINE, cell="Samsung 40T5", parallel=2)
    V["4 moteurs basculants"] = dict(BASELINE, n_tilt=4)
    V["Sans second drone"] = dict(BASELINE, second_drone=False)
    V["Caméra HQ + 16 mm"] = dict(BASELINE, camera="HQ Camera + 16 mm")
    V["Jetson prêtée"] = dict(BASELINE, obc="Jetson Orin Nano (prêt réel)")
    V["Pi 5 8 Go"] = dict(BASELINE, obc="Raspberry Pi 5 8 Go + cooler + BEC")
    V["Tout neuf (RX 25 €, second drone 150 €)"] = dict(BASELINE, rx="RadioMaster RP3 neuf (ELRS MAVLink)", second_drone_price=SECOND_DRONE_PRICE_NEW)
    V["Pack 6S2P Molicel P45B"] = dict(BASELINE, cell="Molicel P45B", parallel=2)
    V["AR 8 (envergure plus grande)"] = dict(BASELINE, AR=8.0)
    V["Croisière 13 m/s"] = dict(BASELINE, v_cruise=13.0)
    return V

def sensitivities(base_cfg):
    out = {}
    global AERO, STRUCT, PAYLOAD_DROP_G
    saved = (dict(AERO), dict(STRUCT), PAYLOAD_DROP_G)
    def run(label):
        r = size(base_cfg); out[label] = dict(perf=r["perf"], score=r["score"]["total"])
    run("Référence")
    AERO["CD0"] = 0.045; run("Traînée parasite +30 %"); AERO["CD0"] = saved[0]["CD0"]
    AERO["eta_cruise"] = 0.40; run("Rendement croisière 0,40"); AERO["eta_cruise"] = saved[0]["eta_cruise"]
    AERO["CLmax"] = 1.0; run("CLmax 1,0 (profil moins bon)"); AERO["CLmax"] = saved[0]["CLmax"]
    STRUCT["skin_thk_mm"] = 0.8; run("Peau d'aile 0,8 mm"); STRUCT["skin_thk_mm"] = saved[1]["skin_thk_mm"]
    STRUCT["foam_frac"] = 1.0; run("Aile entièrement moussée"); STRUCT["foam_frac"] = saved[1]["foam_frac"]
    PAYLOAD_DROP_G = 150.0; run("Charge larguée 150 g"); PAYLOAD_DROP_G = saved[2]
    AERO["AR"] = 8.0; run("Allongement 8"); AERO["AR"] = saved[0]["AR"]
    AERO["AR"] = 6.0; run("Allongement 6"); AERO["AR"] = saved[0]["AR"]
    return out

def wind_effect(perf):
    """Portée avec vent de face/arrière constant sur l'aller et retour (vol aller-retour)."""
    V = MISSION["v_cruise"]; t = perf["endurance_min_with_reserve"] - MISSION["t_hover_min"]
    rows = []
    for w in (0, 3, 5, 8):
        # aller-retour : distance totale D, temps = D/2/(V-w) + D/2/(V+w)
        D = t * 60 / (0.5 / (V - w) + 0.5 / (V + w)) / 1000 if V > w else 0
        rows.append(dict(wind_ms=w, range_km=round(D, 1)))
    return rows

# ----------------------------------------------------------------------------- SORTIES
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--no-plot", action="store_true"); a = ap.parse_args()
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultats"); os.makedirs(out_dir, exist_ok=True)
    ref = size(BASELINE)
    vars_ = {k: size(v) for k, v in variants().items()}
    sens = sensitivities(BASELINE)
    wind = wind_effect(ref["perf"])
    res = dict(mission=MISSION, aero=AERO, struct=STRUCT, reference=ref, variants={k: dict(perf=v["perf"], score=v["score"]) for k, v in vars_.items()},
               sensitivities=sens, wind=wind)
    with open(os.path.join(out_dir, "dimensionnement_v3.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    # Markdown
    L = ["# Résultats dimensionnement v3", ""]
    p = ref["perf"]
    L += ["## Référence convergée", "", f"- Masse au décollage : **{p['mass_kg']} kg** (structure {p['struct_g']} g, pack {p['pack']} {p['pack_g']} g)",
          f"- Aile : {p['S_m2']} m², envergure **{p['span_m']} m**, corde {p['chord_m']*100:.0f} cm, charge alaire {p['wing_loading']} kg/m²",
          f"- Croisière {MISSION['v_cruise']} m/s : CL {p['CL_cruise']}, finesse {p['LD']}, **{p['P_cruise_W']} W**",
          f"- Stationnaire : **{p['P_hover_W']} W**, {p['hover_g_per_W']} g/W, {p['i_hover_A']} A sur 6S ; poussée/poids moteurs {p['twr']}",
          f"- Pack {p['pack']} : {p['pack_i_cont_A']} A continus = {p['pack_P_max_W']} W ; poussée/poids atteignable sous cette limite **{p['twr_under_pack_limit']}** ; régler BATT_WATT_MAX ≈ {p['batt_watt_max_param']:.0f} W",
          f"- Autonomie avec réserve : **{p['endurance_min_with_reserve']} min**, distance **{p['range_km_with_reserve']} km**",
          f"- Longeron : Ø{p['spar']['Do_mm']:.0f}/{p['spar']['Di_mm']:.0f} mm à {p['spar']['sigma_MPa']:.0f} MPa",
          f"- Coût déclaré : **{p['cost_eur']:.0f} €** ; score dimensionnement : **{ref['score']['total']} pts**", ""]
    L += ["## Itérations", "", "| Tour | Masse entrée (kg) | S (m²) | Envergure (m) | Structure (g) | Pack | Pack (g) | Masse sortie (kg) | Coût (€) |", "|---|---|---|---|---|---|---|---|---|"]
    for h in ref["hist"]:
        L.append(f"| {h['it']} | {h['m_in']} | {h['S']} | {h['b']} | {h['struct_g']} | {h['pack']} | {h['pack_g']} | {h['m_out']} | {h['cost']:.0f} |")
    L += ["", "## Coût déclaré (référence)", "", "| Poste | € |", "|---|---|"] + [f"| {k} | {v:.2f} |" for k, v in p["cost_breakdown"].items()] + [f"| **Total** | **{p['cost_eur']:.0f}** |"]
    L += ["", "## Points détaillés (référence)", ""] + [f"- {k} : {v}" for k, v in ref["score"]["detail"].items()]
    L += ["", "## Variantes", "", "| Variante | Masse (kg) | Envergure (m) | P stat. (W) | T/W sous limite pack | Autonomie (min) | Distance (km) | Coût (€) | Score | Δ score |", "|---|---|---|---|---|---|---|---|---|---|"]
    s0 = ref["score"]["total"]
    for k, v in vars_.items():
        q = v["perf"]; s = v["score"]["total"] if not v["score"]["eliminated"] else "ÉLIMINÉ"
        d = round(s - s0, 1) if isinstance(s, (int, float)) else "-"
        L.append(f"| {k} | {q['mass_kg']} | {q['span_m']} | {q['P_hover_W']} | {q['twr_under_pack_limit']} | {q['endurance_min_with_reserve']} | {q['range_km_with_reserve']} | {q['cost_eur']:.0f} | {s} | {d} |")
    L += ["", "## Sensibilités", "", "| Scénario | Masse (kg) | Envergure (m) | Autonomie (min) | Distance (km) | Score |", "|---|---|---|---|---|---|"]
    for k, v in sens.items():
        q = v["perf"]; L.append(f"| {k} | {q['mass_kg']} | {q['span_m']} | {q['endurance_min_with_reserve']} | {q['range_km_with_reserve']} | {v['score']} |")
    L += ["", "## Vent (aller-retour, croisière constante)", "", "| Vent (m/s) | Distance aller-retour (km) |", "|---|---|"] + [f"| {w['wind_ms']} | {w['range_km']} |" for w in wind]
    with open(os.path.join(out_dir, "dimensionnement_v3.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print("\n".join(L))
    if not a.no_plot:
        plots(ref, vars_, out_dir)

def plots(ref, vars_, out_dir):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    # 1. Puissance requise vs vitesse
    m = ref["perf"]["mass_kg"]; S = ref["perf"]["S_m2"]
    Vs = [v / 10 for v in range(90, 251, 5)]; P = []; LD = []
    for V in Vs:
        q = 0.5 * RHO * V ** 2; CL = m * G / (q * S); CD = AERO["CD0"] + CL ** 2 / (math.pi * AERO["AR"] * AERO["e"])
        P.append(q * S * CD * V / AERO["eta_cruise"]); LD.append(CL / CD)
    fig, ax = plt.subplots(figsize=(7, 4)); ax.plot(Vs, P, color="#1f4e79"); ax.set_xlabel("Vitesse (m/s)"); ax.set_ylabel("Puissance électrique (W)")
    ax.axvline(MISSION["v_stall"], ls="--", color="grey"); ax.text(MISSION["v_stall"] + 0.2, max(P) * 0.9, "décrochage", color="grey")
    ax.axvline(MISSION["v_cruise"], ls=":", color="#c00"); ax.text(MISSION["v_cruise"] + 0.2, max(P) * 0.8, "croisière", color="#c00")
    ax2 = ax.twinx(); ax2.plot(Vs, LD, color="#888"); ax2.set_ylabel("Finesse L/D", color="#888")
    ax.set_title(f"Puissance requise en palier, {m} kg, S = {S} m²"); fig.tight_layout(); fig.savefig(os.path.join(out_dir, "puissance_vs_vitesse.png"), dpi=150); plt.close(fig)
    # 2. Convergence
    fig, ax = plt.subplots(figsize=(6, 3.5)); ax.plot([h["it"] for h in ref["hist"]], [h["m_out"] for h in ref["hist"]], "o-", color="#1f4e79")
    ax.set_xlabel("Itération"); ax.set_ylabel("Masse (kg)"); ax.set_title("Convergence de la boucle de dimensionnement"); fig.tight_layout(); fig.savefig(os.path.join(out_dir, "convergence.png"), dpi=150); plt.close(fig)
    # 3. Score vs coût des variantes
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for k, v in vars_.items():
        q = v["perf"]; s = v["score"]["total"]; col = "#c00" if v["score"]["eliminated"] else "#1f4e79"
        ax.scatter(q["cost_eur"], s, color=col); ax.annotate(k, (q["cost_eur"], s), fontsize=7, xytext=(3, 3), textcoords="offset points")
    ax.axvline(1000, ls="--", color="#c00"); ax.text(1003, ax.get_ylim()[0] + 2, "1 000 € éliminatoire", color="#c00", fontsize=8)
    ax.set_xlabel("Coût déclaré (€)"); ax.set_ylabel("Points liés au dimensionnement"); ax.set_title("Variantes : points contre coût"); fig.tight_layout(); fig.savefig(os.path.join(out_dir, "score_vs_cout.png"), dpi=150); plt.close(fig)

if __name__ == "__main__":
    main()
