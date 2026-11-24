# Banc d'essai moteur — notice de mise en place

Banc à bras pivotant 3:1 : le moteur est à 300 mm au-dessus de l'axe, le bas du bras à 100 mm en dessous appuie sur une cellule de charge barre 20 kg montée verticalement. La cellule voit trois fois la poussée : plage utile 6,6 kg, résolution bien meilleure que le gramme.

## Fichiers
- `cao/banc_essai.scad` : pièces paramétriques imprimables (OpenSCAD, menu Customizer, variable `PART`).
- `cao/stl_banc/` : STL de visualisation (sans perçages) et rendus `banc_rendus.png`.
- `banc_essai.ino` : programme Arduino (rampe automatique, journal CSV, homme mort).
- `analyse_banc.py` : moyennes par palier, courbes, verdict selon les critères de la Partie A.
- `exemple_synthetique_*.csv` : données fabriquées pour tester le script, **pas des mesures**.

## Liste d'achat (prix vérifiés le 4/11/2026 sauf mention)
| Article | Où | Prix |
|---|---|---|
| Cellule de charge barre 20 kg + module HX711 | gotronic.fr (la version 5 kg est à 7,50 € ; prendre la 20 kg, même format 80 × 12,7 mm) | ≈ 8 € |
| Arduino Nano Every | gotronic.fr | 15,45 € |
| Capteur de courant ACS758-50B (ou module INA226 + shunt 50 A 75 mV) | amazon.fr, non vérifié | ≈ 8 € |
| Résistances 100 kΩ et 10 kΩ (diviseur tension), condensateur 100 nF | fond de tiroir | 1 € |
| Capteur optique TCRT5000 (module avec comparateur) | amazon.fr, non vérifié | 3 € |
| 2 boutons poussoirs (START, STOP homme mort), fils, borniers | fond de tiroir | 3 € |
| Visserie M4 (axe 70 mm + écrous nylstop, 8 vis M4 × 16), M3 × 8 pour le moteur, M6 pour la table | quincaillerie | 6 € |
| Filament PETG-CF ≈ 350 g | stock | ≈ 15 € |
| **Total** | | **≈ 60 €** |

L'alimentation 6S vient d'une batterie LiPo/Li-ion 6S (stock FPV de Quentin) : jamais d'alimentation de labo sous-dimensionnée, les pointes dépassent 30 A.

## Montage
1. Imprimer : `base` (PETG, 4 parois, 30 %), 2 × `montant`, `bras` (couché, PETG-CF, 4 parois, 40 %), `poteau_cellule`, 2 × `bague_axe`.
2. Tarauder M4 le trou du bas du bras et y visser une vis M4 × 20 à tête bombée : c'est la vis de contact sur la cellule. Un élastique entre le haut du poteau et le bras assure un appui permanent de 100 à 200 g.
3. Fixer la cellule 20 kg par son extrémité **fixe** (2 vis M4) sur le poteau, flèche de la cellule vers le bras ; l'extrémité libre doit affleurer la vis de contact, jeu nul, sans précontrainte.
4. Axe M4 à travers montants et bras, bagues imprimées comme paliers, écrou nylstop sans serrer : le bras doit basculer sans frottement.
5. Visser la base sur une table lourde ou la lester à 10 kg ; l'hélice doit dépasser du bord de la table, **1 m libre devant et derrière**, personne dans le plan de l'hélice.
6. Câbler suivant l'en-tête de `banc_essai.ino` ; masse commune Arduino / ESC / capteurs ; l'ESC n'alimente pas l'Arduino.

## Procédure d'essai
1. Sans hélice : téléverser, ouvrir le moniteur série à 115 200 bauds, vérifier `volt_V` au multimètre, `t` pour tarer.
2. Étalonnage : poulie fixée dans l'axe de poussée, fil horizontal depuis le plateau moteur, masse connue de 1 000 g suspendue ; commande `c` puis `1000`. Vérifier ensuite avec 500 g et 2 000 g : erreur attendue < 2 %.
3. Hélice montée, lunettes, STOP tenu enfoncé par une seconde personne, `r` puis START : rampe de 1 100 à 1 800 µs par pas de 50 µs toutes les 4 s. Relâcher STOP arrête tout.
4. Enregistrer la sortie série dans `essai_<moteur>_<helice>.csv` (moniteur série > enregistrer, ou `python3 -m serial.tools.miniterm`).
5. `python3 analyse_banc.py essai_*.csv` : poussée max, g/W à 950 g (poussée de stationnaire par moteur), verdict.
6. Bruit : smartphone avec une application sonomètre à 10 m dans l'axe, palier à 950 g, noter dB(A) ; multiplier l'effet de 4 moteurs : +6 dB.
7. Température moteur après 2 min à 950 g (thermomètre IR) : < 70 °C.

## Critères de choix (Partie A, révisés avec le modèle de la Partie D)
Poussée max ≥ 1 700 g ; rendement ≥ 6 g/W à 950 g ; courant total 4 moteurs en stationnaire ≤ 50 % du courant continu du pack ; bruit extrapolé < 72 dB(A) à 10 m ; masse moteur + ESC + hélice ≤ 150 g ; prix des 4 postes ≤ 200 €.
