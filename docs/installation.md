# Installation

Trois machines, trois rôles :

| Machine | Système | Rôle |
|---|---|---|
| PC fixe | Ubuntu 24.04 natif, carte NVIDIA | simulation : ArduPilot SITL, Gazebo, ROS 2 Jazzy |
| PC portable | Windows + WSL Ubuntu 22.04 | station sol : Mission Planner (Windows) ou MAVProxy (WSL) |
| Raspberry Pi 5 | Ubuntu 24.04 | ordinateur de bord : ROS 2 Jazzy, MAVROS, perception, mission |

## PC fixe (Ubuntu 24.04)

### 1. Pilote graphique
`nvidia-smi` doit afficher la carte, et `glxinfo -B` doit indiquer `NVIDIA` avec OpenGL 4.6.
Sinon : `sudo ubuntu-drivers install` (ou `sudo apt install nvidia-driver-580`), puis redémarrer.

### 2. ArduPilot
```bash
cd ~ && git clone --recurse-submodules https://github.com/ArduPilot/ardupilot.git
cd ardupilot && Tools/environment_install/install-prereqs-ubuntu.sh -y
# fermer et rouvrir le terminal
cd ~/ardupilot && git checkout Plane-4.7.1 && git submodule update --init --recursive
./waf configure --board sitl && ./waf plane && ./waf copter
```

### 3. Gazebo Harmonic et plugin ArduPilot
```bash
sudo apt install -y gz-harmonic libgz-sim8-dev rapidjson-dev libopencv-dev \
  libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-bad gstreamer1.0-libav gstreamer1.0-gl
cd ~ && git clone https://github.com/ArduPilot/ardupilot_gazebo
cd ardupilot_gazebo && mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=RelWithDebInfo && make -j4
```
Ajouter à la **fin** de `~/.bashrc` (après toute ligne `source /opt/ros/...`) :
```bash
export GZ_SIM_SYSTEM_PLUGIN_PATH=$HOME/ardupilot_gazebo/build:$GZ_SIM_SYSTEM_PLUGIN_PATH
export GZ_SIM_RESOURCE_PATH=$HOME/ardupilot_gazebo/models:$HOME/ardupilot_gazebo/worlds:$GZ_SIM_RESOURCE_PATH
```

### 4. ROS 2 Jazzy, pont Gazebo et MAVROS
Dépôt ROS 2 : suivre <https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html>, puis :
```bash
sudo apt install -y ros-jazzy-desktop ros-jazzy-ros-gz ros-jazzy-mavros ros-jazzy-mavros-extras \
  ros-jazzy-cv-bridge python3-colcon-common-extensions python3-rosdep git-lfs
sudo rosdep init; rosdep update
sudo /opt/ros/jazzy/lib/mavros/install_geographiclib_datasets.sh   # obligatoire pour MAVROS
```

### 5. Ce dépôt
```bash
git lfs install
git clone <url du dépôt> ~/uav-challenge-isep && cd ~/uav-challenge-isep/ros2_ws
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -y
colcon build --symlink-install
echo "source ~/uav-challenge-isep/ros2_ws/install/setup.bash" >> ~/.bashrc
```

### Problèmes connus
- **`ModuleNotFoundError` en lançant `ros2`** : l'environnement Python d'ArduPilot (`venv-ardupilot`) masque celui de ROS. Faire `deactivate` dans ce terminal, ou recréer le venv avec `python3 -m venv --system-site-packages ~/venv-ardupilot`.
- **Gazebo affiche « Unable to find or download file »** : `GZ_SIM_RESOURCE_PATH` ne contient pas `ardupilot_gazebo/models` (vérifier avec `echo $GZ_SIM_RESOURCE_PATH`, et que les lignes de l'étape 3 sont bien en fin de `.bashrc`).
- **`apt` bloqué par `unattended-upgr`** : laisser finir, ou `sudo systemctl stop unattended-upgrades` s'il est en `--download-only`.

## PC portable (station sol)

Le portable n'a pas besoin de ROS : il parle au simulateur en MAVLink.
1. Sous Windows 11, dans `%USERPROFILE%\.wslconfig`, ajouter `networkingMode=mirrored` sous `[wsl2]`, puis `wsl --shutdown`.
2. Les deux PC sur le même réseau (pas le Wi-Fi de l'école, qui isole les appareils). Vérifier avec `ping` dans les deux sens.
3. Sur le PC fixe, lancer la simulation avec l'IP du portable : `GCS_IP=192.168.x.y sim/run_gazebo.sh` ou `gcs_ip:=192.168.x.y`.
4. Sur le portable : Mission Planner, connexion **UDP 14550** ; ou dans WSL `mavproxy.py --master udp:0.0.0.0:14550 --console --map`.

## Raspberry Pi 5 (plus tard)
Ubuntu 24.04 Server, ROS 2 Jazzy (`ros-jazzy-ros-base`), MAVROS, ce dépôt compilé sans `isep_description`.
Lancement : `ros2 launch isep_bringup real.launch.py`. Détails à écrire lors de l'intégration.
