#!/usr/bin/env bash
# Vol simulé AVEC Gazebo, sans ROS : notre modèle isep_vtol dans le monde isep_runway.
# Prérequis : ArduPilot compilé dans ~/ardupilot, plugin ardupilot_gazebo compilé
# dans ~/ardupilot_gazebo (voir docs/installation.md).
#
#   sim/run_gazebo.sh                       # Gazebo + SITL + MAVProxy
#   GCS_IP=192.168.1.42 sim/run_gazebo.sh   # + télémétrie vers le portable
#   HEADLESS=1 sim/run_gazebo.sh            # sans fenêtre Gazebo (serveur seul)
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARDUPILOT_HOME="${ARDUPILOT_HOME:-$HOME/ardupilot}"
AP_GZ="${ARDUPILOT_GAZEBO:-$HOME/ardupilot_gazebo}"
DESC="$REPO/ros2_ws/src/isep_description"
P="$REPO/ardupilot/params"

export GZ_SIM_RESOURCE_PATH="$DESC/models:$DESC/worlds:$AP_GZ/models:$AP_GZ/worlds:${GZ_SIM_RESOURCE_PATH:-}"
export GZ_SIM_SYSTEM_PLUGIN_PATH="$AP_GZ/build:${GZ_SIM_SYSTEM_PLUGIN_PATH:-}"

# Le modèle doit être à jour avec config/isep_vtol.yaml
python3 "$DESC/scripts/generate_model.py" >/dev/null

GZ_ARGS=(-v3 -r "$DESC/worlds/isep_runway.sdf")
if [[ "${HEADLESS:-0}" == "1" ]]; then GZ_ARGS=(-s "${GZ_ARGS[@]}"); fi
gz sim "${GZ_ARGS[@]}" &
GZ_PID=$!
trap 'kill $GZ_PID 2>/dev/null || true' EXIT
sleep 5

OUT_ARGS=()
if [[ -n "${GCS_IP:-}" ]]; then OUT_ARGS+=(--out "udp:${GCS_IP}:14550"); fi

# Dossier de travail du SITL : le script de mixage moteur doit être dans ./scripts
WORK="$HOME/.isep_sitl"
mkdir -p "$WORK/scripts"
cp "$REPO/ardupilot/scripts/generated/isep_vtol_motors.lua" "$WORK/scripts/"

cd "$ARDUPILOT_HOME"
# -w : on repart toujours des fichiers .param (pas de réglages restés en mémoire)
Tools/autotest/sim_vehicle.py -v ArduPlane -f quadplane --model JSON -w --use-dir="$WORK" \
  --add-param-file="$P/isep_vtol_gz.param" \
  --add-param-file="$P/generated/isep_vtol_servos.param" \
  --add-param-file="$P/common.param" \
  --console --map "${OUT_ARGS[@]}" "$@"
