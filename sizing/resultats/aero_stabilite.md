# Aérodynamique, stabilité, centrage, points de fonctionnement (v3)

Aile : S = 0.418 m², b = 1.71 m, c = 24.4 cm, AR = 7.0. Pente de portance aile finie a = 4.31 /rad (profil 2D 5.7 /rad, α0 = -3.0°).

## Polaire estimée

| α (°) | CL | CD | L/D |
|---|---|---|---|
| -4 | -0.075 | 0.0353 | 0 |
| -3 | 0.0 | 0.035 | 0 |
| -2 | 0.075 | 0.0353 | 2.1 |
| -1 | 0.15 | 0.0363 | 4.1 |
| 0 | 0.225 | 0.0379 | 5.9 |
| 1 | 0.301 | 0.0401 | 7.5 |
| 2 | 0.376 | 0.043 | 8.7 |
| 3 | 0.451 | 0.0466 | 9.7 |
| 4 | 0.526 | 0.0507 | 10.4 |
| 5 | 0.601 | 0.0555 | 10.8 |
| 6 | 0.676 | 0.061 | 11.1 |
| 7 | 0.751 | 0.0671 | 11.2 |
| 8 | 0.827 | 0.0738 | 11.2 |
| 9 | 0.902 | 0.0812 | 11.1 |
| 10 | 0.977 | 0.0892 | 10.9 |
| 11 | 1.052 | 0.0979 | 10.7 |
| 12 | 1.127 | 0.1072 | 10.5 |
| 13 | 1.2 | 0.1169 | 10.3 |
| 14 | 1.2 | 0.1169 | 10.3 |

## Vitesses caractéristiques

- Décrochage : 11.0 m/s (CLmax 1.2)
- Fin de transition (aile porte tout à CL 0,8) : 13.5 m/s → régler AIRSPEED_MIN ≈ 14 m/s, Q_ASSIST_SPEED ≈ 11 m/s
- Traînée minimale (finesse max) : 13.6 m/s ; puissance minimale : 10.3 m/s ; croisière retenue 15 m/s

## Empennage et stabilité longitudinale

- Bras de levier 0.8 m (poutres), Vh = 0.5, Vv = 0.04 → stabilisateur 637 cm² (ex. 50 × 13 cm), dérive 357 cm² au total (2 dérives sur poutres de 179 cm²)
- Point neutre : 46 % de la corde (aile+empennage 49 %, fuselage −3 %)
- CG cible pour une marge statique de 12 % : **34 % de la corde**, soit 26 cm du nez

## Centrage avec l'implantation proposée

| Élément | Masse (g) | x depuis le nez (cm) |
|---|---|---|
| Caméra + LiDAR (nez) | 115 | 3 |
| Contrôleur de vol + GPS + RX | 47 | 14 |
| Raspberry Pi 5 + BEC | 90 | 20 |
| Pack 6S2P (sous l'aile, réglable) | 958 | 19 |
| Soute : charge 250 g + second drone 250 g | 500 | 29 |
| Fuselage + patins | 220 | 22 |
| Aile (peau, nervures, longerons, servos) | 700 | 28 |
| Poutres x2 (1,2 m) | 200 | 52 |
| Moteurs avant + nacelles tilt + servos (x2) | 506 | -6 |
| Moteurs arrière + nacelles (x2) | 320 | 58 |
| ESC + câblage | 115 | 24 |
| Empennage + servos | 106 | 108 |
| **Total** | **3877** | **25.8** |

CG obtenu : 32 % de la corde → marge statique **14 %** (OK). Le pack (958 g) coulisse dans le fuselage : 1 cm de pack = 1.0 % de corde de CG.

**Stationnaire** : le centre des 4 rotors (moteurs avant à −6 cm, arrière à 58 cm du nez) est à 26 cm du nez : il coïncide avec le CG avion à ±0.2 cm. Entraxe des rotors 64 × 64 cm, garde hélice 10" au bord de fuite ≈ 3 cm.

## Contraintes dans les tubes

- Longeron principal Ø14/12 : 385 MPa à 4 g × 1,5 (admissible 400 MPa)
- Poutre moteur Ø14/12 sous poussée max arrière (2,4 kg × 1,5 à 0,35 m) : 100 MPa ; en Ø12/10 : 141 MPa → Ø14/12 retenu pour la rigidité en torsion

## Points de fonctionnement moteurs (par moteur, 6S)

| Phase | Puissance (W) | Courant (A) | Commentaire |
|---|---|---|---|
| Stationnaire | 154 | 7.0 | 4 moteurs, 6.1 g/W |
| Transition / rafale (plafond BATT_WATT_MAX) | 340 | 15.3 | pack 70 A continus, pointes courtes |
| Croisière, 2 moteurs avant | 50 | 2.3 | hélices arrière arrêtées et alignées |
| Croisière si 4 moteurs tournent | 29 | 1.3 | +15 % de traînée estimée |

## Second drone (micro quad 3,5", 250 g, 3S 850 mAh)

- Puissance stationnaire ≈ 38 W, énergie utile ≈ 7.5 Wh → **≈ 12 min** de vol
- Rôle : suivi du maître puis mission propre courte ; pas d'emport de charge.
