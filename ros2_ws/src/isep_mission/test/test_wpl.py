from pathlib import Path

import pytest

from isep_mission.wpl import load_wpl, parse_wpl

REPO = Path(__file__).resolve().parents[4]


def test_repo_missions_parse():
    files = sorted((REPO / "ardupilot" / "missions").glob("*.waypoints"))
    assert files, "aucune mission dans ardupilot/missions"
    for f in files:
        items = load_wpl(f)
        assert items[0].command == 16, f"{f.name} : l'élément 0 doit être le point HOME"
        cmds = [it.command for it in items]
        assert 84 in cmds, f"{f.name} : pas de VTOL_TAKEOFF (84)"
        assert cmds[-1] in (85, 20, 21), f"{f.name} : la mission doit finir par un atterrissage ou un RTL"
        if cmds[-1] == 85 and items[-2].command == 16:
            from math import cos, hypot, radians
            a, b = items[-2], items[-1]
            d = hypot((a.lat - b.lat) * 111320, (a.lon - b.lon) * 111320 * cos(radians(b.lat)))
            assert d > 80, f"{f.name} : dernier point à {d:.0f} m de VTOL_LAND, ArduPlane refuse d armer sous ~55 m"


def test_bad_header():
    with pytest.raises(ValueError):
        parse_wpl("hello\n0\t1\t0\t16\t0\t0\t0\t0\t0\t0\t0\t1\n")


def test_bad_sequence():
    txt = "QGC WPL 110\n0\t1\t0\t16\t0\t0\t0\t0\t0\t0\t0\t1\n2\t0\t3\t16\t0\t0\t0\t0\t0\t0\t10\t1\n"
    with pytest.raises(ValueError):
        parse_wpl(txt)
