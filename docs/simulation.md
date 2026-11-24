# Simulation

## Trois niveaux

| Niveau | Commande | Physique | Pour tester |
|---|---|---|---|
| 1. SITL interne | `sim/run_sitl_internal.sh` | modèle `quadplane-tilttrivec` intégré à ArduPilot | missions, transitions, failsafes, géofence |
| 2. Gazebo sans ROS | `sim/run_gazebo.sh` | **notre** drone (`isep_vtol`) | comportement de la cellule, réglages |
| 3. Système complet | `ros2 launch isep_bringup sim.launch.py` | notre drone + capteurs | perception, machine à états, MAVROS |

Le niveau 1 tourne même sans carte graphique. Les niveaux 2 et 3 utilisent les mêmes fichiers `.param`.

Avec le niveau 3, MAVROS occupe le port TCP 5760 du SITL. Pour piloter à la main en parallèle :
`mavproxy.py --master tcp:127.0.0.1:5762 --console --map`.

## Valider le modèle isep_vtol

Le modèle est **généré mais pas encore validé**. Avant toute autre utilisation, dérouler ces étapes
avec `sim/run_gazebo.sh` (fenêtre Gazebo + console MAVProxy) et, dans un autre terminal,
`python3 tools/check_servo_outputs.py` pour voir les sorties PWM avec leur rôle.

Les gouvernes sont invisibles (le STL est d'un seul bloc) ; pour voir leurs angles :
`gz topic -e -t /world/isep_runway/model/isep_vtol/joint_state`.

1. **Chargement.** Le drone apparaît posé sur la piste, sans erreur rouge `ArduPilotPlugin` dans le terminal Gazebo. La console MAVProxy reçoit le GPS et l'EKF s'initialise.
2. **Nacelles en VTOL.** En `mode QSTABILIZE`, désarmé : les deux moteurs avant pointent vers le haut, le moteur arrière est suspendu sous son pivot, hélice vers le bas (PWM des servos de bascule vers 1100, soit 0°).
3. **Nacelles en avion.** `mode FBWA` : les deux nacelles avant basculent vers l'avant, le moteur arrière pivote pour pointer vers l'arrière, en propulsion (PWM vers 2000, soit 90°). Revenir en `mode QSTABILIZE`.
4. **Gouvernes**, en `mode FBWA` désarmé :
   - `rc 1 1900` (roulis à droite) : aileron droit bord de fuite vers le haut, gauche vers le bas ;
   - manche de profondeur en montée : les deux panneaux du V bord de fuite vers le haut.
   Sinon, inverser le signe concerné dans `generate_model.py` (simulation) ou `SERVOn_REVERSED` (vrai drone).
5. **Stationnaire.** `mode QLOITER`, `arm throttle`, `rc 3 1700` puis `rc 3 1500` à 10 m. Le drone doit tenir sa position. Tester le lacet avec `rc 4 1700` : les nacelles avant doivent basculer en sens opposé et le nez tourner à droite.
6. **Transition et mission.** `wp load <dépôt>/ardupilot/missions/01_trajectoire_A.waypoints`, `mode AUTO`, `arm throttle` : décollage vertical, transition, circuit, atterrissage vertical.
7. **Réglage.** `QAUTOTUNE` en stationnaire, puis `AUTOTUNE` en avion. Recopier les gains obtenus dans `ardupilot/params/isep_vtol_gz.param`.

| Symptôme | Cause probable | Correction |
|---|---|---|
| Se retourne dès le décollage | sens de rotation ou ordre des moteurs | `spin` et `motor_servo` dans `isep_vtol.yaml` |
| Tourne sur lui-même en stationnaire | lacet vectoriel inversé | inverser les rôles 75/76 des deux nacelles avant |
| Cabre ou pique fort à la transition | centre de gravité ou centre de poussée | `cg_mm`, `cp_mm` dans `isep_vtol.yaml` |
| Refuse d'armer, « Rangefinder » | `rangefinder_mavlink.param` chargé sans ROS | ne le charger qu'avec `sim.launch.py` |
| Le SITL attend indéfiniment | Gazebo n'envoie rien sur le port 9002 | vérifier `GZ_SIM_SYSTEM_PLUGIN_PATH` (plugin compilé) |

Après chaque modification de `config/isep_vtol.yaml` : `python3 ros2_ws/src/isep_description/scripts/generate_model.py`
(le script affiche aussi les poussées nécessaires en stationnaire).

## Scénarios de test

| N° | Scénario | Comment le provoquer | Réussi si |
|---|---|---|---|
| 01 | Trajectoire A | mission `01_trajectoire_A.waypoints` en AUTO | écart max < 1 m (log) |
| 02 | Perte radio | en vol : `param set SIM_RC_FAIL 1` | RTL puis atterrissage vertical sans intervention |
| 03 | Géofence | en vol, sortir à plus de 300 m du départ | RTL déclenché |
| 04 | Batterie basse | en vol : `param set BATT_LOW_MAH 9900` (seuil atteint presque aussitôt) | passage en LOITER_TO_QLAND |
| 05 | Transition | AUTO, décollage vertical puis premier point | perte d'altitude < 5 m |
| 06 | Largage | niveau 3, cible rouge à 30 m sur la piste | largage déclenché au-dessus de la cible |
| 07 | Suivi par le second drone | SITL ArduCopter `-I1` avec `follower_copter.param` | distance 5 ± 2 m pendant 3 min |
| 08 | Mission complète | niveau 3, `mission:=true` puis `/isep/start` | tous les états parcourus en moins de 12 min |
| 09 | Coupure d'urgence | au banc, pas en simulation | coupure en moins de 1 s |

Les scénarios 01 à 05 marchent aussi au niveau 1.
