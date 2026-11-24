#!/usr/bin/env python3
"""Affiche en direct les sorties servo d'ArduPilot avec leur rôle, pour vérifier
les sens (nacelles, gouvernes) en simulation ou au banc, hélices démontées.

  python3 tools/check_servo_outputs.py                       # SITL, port SERIAL1
  python3 tools/check_servo_outputs.py --master /dev/ttyACM0 # carte de vol en USB

Nécessite pymavlink (installé avec MAVProxy).
"""
import argparse
import re
from pathlib import Path

from pymavlink import mavutil

FUNCTIONS = {4: "aileron", 33: "moteur 1 (avant droit)", 34: "moteur 2 (avant gauche)",
             36: "moteur 4 (arrière)", 45: "bascule arrière", 75: "bascule avant gauche",
             76: "bascule avant droite", 79: "V gauche", 80: "V droit", 28: "largage"}
REPO = Path(__file__).resolve().parents[1]


def load_roles(path: Path) -> dict[int, str]:
    roles = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"SERVO(\d+)_FUNCTION\s+(\d+)", line)
        if m and int(m.group(2)):
            roles[int(m.group(1))] = FUNCTIONS.get(int(m.group(2)), f"fonction {m.group(2)}")
    return roles


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--master", default="tcp:127.0.0.1:5762")
    ap.add_argument("--params", default=str(REPO / "ardupilot/params/generated/isep_vtol_servos.param"))
    args = ap.parse_args()
    roles = load_roles(Path(args.params))
    m = mavutil.mavlink_connection(args.master)
    m.wait_heartbeat()
    print(f"connecté au système {m.target_system} ; Ctrl+C pour quitter")
    while True:
        msg = m.recv_match(type="SERVO_OUTPUT_RAW", blocking=True)
        hb = m.messages.get("HEARTBEAT")
        mode = mavutil.mode_string_v10(hb) if hb else "?"
        cells = [f"{n:>2} {roles[n][:18]:<18} {getattr(msg, f'servo{n}_raw', 0):>4}" for n in sorted(roles)]
        print(f"\033[2J\033[Hmode {mode}\n" + "\n".join(cells), flush=True)


if __name__ == "__main__":
    main()
