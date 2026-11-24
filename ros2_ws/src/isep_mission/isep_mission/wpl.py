"""Lecture des fichiers de mission QGC WPL 110 (.waypoints, format Mission Planner)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MissionItem:
    seq: int
    current: bool
    frame: int
    command: int
    param1: float
    param2: float
    param3: float
    param4: float
    lat: float
    lon: float
    alt: float
    autocontinue: bool


def parse_wpl(text: str) -> list[MissionItem]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    if not lines or not lines[0].startswith("QGC WPL"):
        raise ValueError("en-tête 'QGC WPL 110' absent")
    items = []
    for n, ln in enumerate(lines[1:], start=2):
        f = ln.split("\t") if "\t" in ln else ln.split()
        if len(f) != 12:
            raise ValueError(f"ligne {n} : 12 champs attendus, {len(f)} trouvés")
        items.append(MissionItem(
            seq=int(f[0]), current=f[1] == "1", frame=int(f[2]), command=int(f[3]),
            param1=float(f[4]), param2=float(f[5]), param3=float(f[6]), param4=float(f[7]),
            lat=float(f[8]), lon=float(f[9]), alt=float(f[10]), autocontinue=f[11] == "1",
        ))
    for expected, it in enumerate(items):
        if it.seq != expected:
            raise ValueError(f"numérotation discontinue : {it.seq} au lieu de {expected}")
    return items


def load_wpl(path: str | Path) -> list[MissionItem]:
    return parse_wpl(Path(path).read_text(encoding="utf-8"))
