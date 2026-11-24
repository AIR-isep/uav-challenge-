#!/usr/bin/env bash
# Vol simulé SANS Gazebo : modèle physique interne d'ArduPilot « quadplane-tilttrivec »
# (tilt-tri à lacet vectoriel, le plus proche de notre drone). Léger, idéal pour
# tester missions, transitions et failsafes.
#
#   sim/run_sitl_internal.sh                      # console + carte
#   GCS_IP=192.168.1.42 sim/run_sitl_internal.sh  # renvoie aussi la télémétrie vers le portable
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARDUPILOT_HOME="${ARDUPILOT_HOME:-$HOME/ardupilot}"

OUT_ARGS=()
if [[ -n "${GCS_IP:-}" ]]; then OUT_ARGS+=(--out "udp:${GCS_IP}:14550"); fi

cd "$ARDUPILOT_HOME"
exec Tools/autotest/sim_vehicle.py -v ArduPlane -f quadplane-tilttrivec \
  --add-param-file="$REPO/ardupilot/params/common.param" \
  --console --map "${OUT_ARGS[@]}" "$@"
