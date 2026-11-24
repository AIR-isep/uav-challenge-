# Résultats dimensionnement v3

## Référence convergée

- Masse au décollage : **3.789 kg** (structure 1165 g, pack 6S2P Samsung 50S 958 g)
- Aile : 0.418 m², envergure **1.71 m**, corde 24 cm, charge alaire 9.07 kg/m²
- Croisière 15.0 m/s : CL 0.65, finesse 11.0, **101 W**
- Stationnaire : **618 W**, 6.1 g/W, 27.9 A sur 6S ; poussée/poids moteurs 2.53
- Pack 6S2P Samsung 50S : 70 A continus = 1512 W ; poussée/poids atteignable sous cette limite **1.82** ; régler BATT_WATT_MAX ≈ 1360 W
- Autonomie avec réserve : **75.3 min**, distance **65.0 km**
- Longeron : Ø14/12 mm à 385 MPa
- Coût déclaré : **998 €** ; score dimensionnement : **93.0 pts**

## Itérations

| Tour | Masse entrée (kg) | S (m²) | Envergure (m) | Structure (g) | Pack | Pack (g) | Masse sortie (kg) | Coût (€) |
|---|---|---|---|---|---|---|---|---|
| 0 | 2.666 | 0.294 | 1.43 | 989 | 6S2P Samsung 50S | 958 | 3.613 | 998 |
| 1 | 3.613 | 0.399 | 1.67 | 1140 | 6S2P Samsung 50S | 958 | 3.764 | 998 |
| 2 | 3.764 | 0.415 | 1.7 | 1162 | 6S2P Samsung 50S | 958 | 3.785 | 998 |
| 3 | 3.785 | 0.418 | 1.71 | 1165 | 6S2P Samsung 50S | 958 | 3.789 | 998 |

## Coût déclaré (référence)

| Poste | € |
|---|---|
| Moteurs x4 | 108.00 |
| ESC | 44.90 |
| Hélices (3 paires) | 28.17 |
| Contrôleur de vol | 48.90 |
| GPS | 33.00 |
| Récepteur | 0.00 |
| Servos basculement x2 | 34.58 |
| Servos gouvernes x4 | 65.56 |
| Ordinateur de bord | 163.00 |
| LiDAR | 81.12 |
| Caméra | 30.90 |
| wiring | 40.00 |
| drop_mech | 20.00 |
| structure_mat | 150.00 |
| misc | 5.00 |
| Second drone | 90.00 |
| Pack batterie | 54.84 |
| **Total** | **998** |

## Points détaillés (référence)

- 15 min (I) : 3
- 30 min (N) : 5
- 60 min (N) : 10
- 10 km (I) : 5
- 30 km (N) : 10
- 150 g charge (I) : 5
- 500 g charge (N) : 5
- Bruit < 75 dB (I) : 5
- Décollage/atterrissage auto voilure fixe (N) : 10
- Vertical VTOL (N) : 10
- Plateforme voilure fixe (N) : 10
- Second drone embarqué (N) : 5
- Économies de dotation (I) : 0.0
- Dépenses de l'équipe = 0 € (I) : 10

## Variantes

| Variante | Masse (kg) | Envergure (m) | P stat. (W) | T/W sous limite pack | Autonomie (min) | Distance (km) | Coût (€) | Score | Δ score |
|---|---|---|---|---|---|---|---|---|---|
| v3 référence | 3.789 | 1.71 | 618 | 1.82 | 75.3 | 65.0 | 998 | 93.0 | 0.0 |
| Moteurs 3110 légers | 3.595 | 1.67 | 635 | 1.78 | 78.6 | 68.1 | 1056 | ÉLIMINÉ | - |
| Moteurs T-Motor V3115 | 3.765 | 1.71 | 613 | 1.83 | 75.9 | 65.6 | 1090 | ÉLIMINÉ | - |
| FC Kakute H743-Wing | 3.793 | 1.71 | 619 | 1.81 | 75.2 | 64.9 | 1069 | ÉLIMINÉ | - |
| LiDAR D500 léger | 3.712 | 1.69 | 600 | 1.85 | 77.3 | 66.9 | 1053 | ÉLIMINÉ | - |
| Pack 6S1P Molicel P45B (léger, puissance limitée) | 3.214 | 1.58 | 483 | 1.59 | 34.2 | 28.1 | 978 | 73.4 | -19.6 |
| Pack 6S1P Molicel P50B | 3.23 | 1.58 | 487 | 1.7 | 39.2 | 32.6 | 996 | 83.1 | -9.9 |
| Pack 6S2P Samsung 40T5 | 3.713 | 1.69 | 600 | 1.85 | 58.8 | 50.2 | 993 | 83.1 | -9.9 |
| 4 moteurs basculants | 3.981 | 1.75 | 666 | 1.73 | 70.4 | 60.7 | 1033 | ÉLIMINÉ | - |
| Sans second drone | 3.497 | 1.64 | 548 | 1.97 | 83.5 | 72.5 | 908 | 84.8 | -8.2 |
| Caméra HQ + 16 mm | 4.015 | 1.76 | 675 | 1.71 | 69.6 | 59.9 | 1081 | ÉLIMINÉ | - |
| Jetson prêtée | 3.888 | 1.73 | 643 | 1.77 | 72.7 | 62.7 | 835 | 96.3 | 3.3 |
| Pi 5 8 Go | 3.789 | 1.71 | 618 | 1.82 | 75.3 | 65.0 | 1050 | ÉLIMINÉ | - |
| Tout neuf (RX 25 €, second drone 150 €) | 3.789 | 1.71 | 618 | 1.82 | 75.3 | 65.0 | 1083 | ÉLIMINÉ | - |
| Pack 6S2P Molicel P45B | 3.728 | 1.7 | 604 | 2.18 | 67.7 | 58.2 | 1000 | ÉLIMINÉ | - |
| AR 8 (envergure plus grande) | 3.824 | 1.84 | 627 | 1.8 | 78.1 | 67.6 | 998 | 93.0 | 0.0 |
| Croisière 13 m/s | 3.789 | 1.71 | 618 | 1.82 | 87.6 | 66.0 | 998 | 93.0 | 0.0 |

## Sensibilités

| Scénario | Masse (kg) | Envergure (m) | Autonomie (min) | Distance (km) | Score |
|---|---|---|---|---|---|
| Référence | 3.789 | 1.71 | 75.3 | 65.0 | 93.0 |
| Traînée parasite +30 % | 3.789 | 1.71 | 64.7 | 55.6 | 93.0 |
| Rendement croisière 0,40 | 3.789 | 1.71 | 60.8 | 52.0 | 93.0 |
| CLmax 1,0 (profil moins bon) | 3.943 | 1.91 | 68.0 | 58.5 | 93.0 |
| Peau d'aile 0,8 mm | 3.936 | 1.74 | 71.5 | 61.7 | 93.0 |
| Aile entièrement moussée | 4.123 | 1.78 | 67.1 | 57.7 | 93.0 |
| Charge larguée 150 g | 3.672 | 1.68 | 78.4 | 67.9 | 88.0 |
| Allongement 8 | 3.824 | 1.84 | 78.1 | 67.6 | 93.0 |
| Allongement 6 | 3.776 | 1.58 | 71.0 | 61.2 | 93.0 |

## Vent (aller-retour, croisière constante)

| Vent (m/s) | Distance aller-retour (km) |
|---|---|
| 0 | 65.1 |
| 3 | 62.5 |
| 5 | 57.8 |
| 8 | 46.6 |