# UAV Challenge ISEP : drone VTOL tilt-tri

Dépôt de l'équipe AIR (ISEP) pour le Dassault UAV Challenge 2026-27 : simulation,
paramètres ArduPilot et logiciel embarqué ROS 2 du drone principal **isep_vtol**.

| | |
|---|---|
| Cellule | aile volante à fuselage porteur, 1,60 m d'envergure, empennage en V, 4,3 kg |
| Propulsion | tilt-tri : 2 nacelles avant basculantes + 1 moteur arrière suspendu, qui bascule vers l'arrière en croisière |
| Autopilote | ArduPlane 4.7 (QuadPlane, `Q_FRAME_CLASS 7`, lacet vectoriel `Q_TILT_TYPE 2`) |
| Ordinateur de bord | Raspberry Pi 5, Ubuntu 24.04, ROS 2 Jazzy, MAVROS |
| Simulation | Gazebo Harmonic + plugin `ardupilot_gazebo` |

## Démarrage rapide (PC fixe Ubuntu 24.04)

Installation complète : [docs/installation.md](docs/installation.md). Ensuite, trois niveaux de simulation :

```bash
# 1. Logique de vol seule, sans 3D (le plus léger)
sim/run_sitl_internal.sh

# 2. Notre drone dans Gazebo, sans ROS
sim/run_gazebo.sh

# 3. Tout le système : Gazebo + SITL + MAVROS + perception + mission
cd ros2_ws && colcon build --symlink-install && source install/setup.bash
ros2 launch isep_bringup sim.launch.py mission:=true
ros2 service call /isep/start std_srvs/srv/Trigger      # dans un autre terminal
```

Ajoutez `GCS_IP=<ip du portable>` (scripts) ou `gcs_ip:=<ip>` (launch) pour recevoir la
télémétrie dans Mission Planner ou MAVProxy sur le portable (UDP 14550).

## Organisation

```
ardupilot/        paramètres (.param), missions (.waypoints)
  params/generated/   sorties servo générées depuis le modèle (ne pas éditer)
cad/              sources Fusion 360 (LFS), exports STL, anciennes sources OpenSCAD
docs/             installation, architecture, simulation, modèle, décisions
ros2_ws/src/
  isep_description/   modèle Gazebo isep_vtol + monde ; config/isep_vtol.yaml = source unique
  isep_interfaces/    messages MissionState, Target
  isep_bringup/       sim.launch.py, real.launch.py, pont Gazebo -> ROS 2
  isep_mission/       machine à états de mission (testée sans ROS)
  isep_perception/    détection de cible, télémètre -> ArduPilot
sim/              scripts de simulation, scénarios de test
sizing/ bench/    dimensionnement et banc d'essai moteur
tools/            vérification des sorties servo
```

## Règles de travail

- Une branche par fonctionnalité, relecture avant fusion dans `main`. La CI doit être verte.
- **Le modèle se modifie dans `config/isep_vtol.yaml`**, puis `python3 ros2_ws/src/isep_description/scripts/generate_model.py`. La CI refuse un `model.sdf` qui ne correspond pas à la config.
- Unités SI, repères ROS (ENU monde, FLU drone). La conversion vers NED/FRD d'ArduPilot est faite par MAVROS, nulle part ailleurs.
- Gros fichiers (`.f3d`, `.stl`, rosbags) : Git LFS (`git lfs install` une fois par machine).
- Chaque essai (simulation ou vol) : rosbag + log ArduPilot + `.param` du jour, archivés sur le Drive.

## État actuel (v0.1)

Le modèle Gazebo et les paramètres de départ sont **générés mais pas encore validés en vol simulé** :
suivre la procédure de [docs/simulation.md](docs/simulation.md#valider-le-modèle-isep_vtol) avant de s'y fier.
Hypothèses à confirmer (centre de gravité, poussée moteur, inerties) : [docs/modele_isep_vtol.md](docs/modele_isep_vtol.md).
