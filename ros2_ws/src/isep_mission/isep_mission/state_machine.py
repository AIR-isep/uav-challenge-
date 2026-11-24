"""Machine à états de mission, sans dépendance ROS (testable avec pytest seul).

Le nœud ROS (mission_node.py) remplit un objet Inputs à chaque tick, appelle
MissionStateMachine.step() et exécute les actions renvoyées (services MAVROS).

Déroulé nominal :
  IDLE --(ordre de départ)--> UPLOAD_MISSION --(mission acceptée)--> ARMING
  ARMING --(mode AUTO + armé)--> MISSION --(posé + désarmé)--> DONE
  MISSION --(cible vue)--> TARGET_FOUND --(largage demandé)--> MISSION
Toute reprise de main par un failsafe d'ArduPilot (RTL, QRTL, QLAND...) pendant
la mission fait passer en FAILSAFE : le nœud n'envoie alors plus aucun ordre.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class State(str, Enum):
    IDLE = "IDLE"
    UPLOAD_MISSION = "UPLOAD_MISSION"
    ARMING = "ARMING"
    MISSION = "MISSION"
    TARGET_FOUND = "TARGET_FOUND"
    FAILSAFE = "FAILSAFE"
    DONE = "DONE"
    ABORTED = "ABORTED"


# Modes ArduPlane qui signalent qu'un failsafe a pris la main
FAILSAFE_MODES = frozenset({"RTL", "QRTL", "QLAND", "LOITER_TO_QLAND"})


@dataclass
class Inputs:
    now: float                      # secondes (horloge ROS)
    connected: bool = False         # MAVROS voit l'autopilote
    armed: bool = False
    mode: str = ""
    landed: bool = True             # ExtendedState.landed_state == ON_GROUND
    start_requested: bool = False   # service /isep/start appelé
    mission_upload_ok: bool | None = None   # résultat du dernier envoi, None si en cours
    target_detected: bool = False
    target_confidence: float = 0.0


@dataclass
class Config:
    arming_retry_s: float = 2.0
    arming_max_attempts: int = 10
    upload_timeout_s: float = 15.0
    target_min_confidence: float = 0.6
    drop_enabled: bool = True


@dataclass
class MissionStateMachine:
    config: Config = field(default_factory=Config)
    state: State = State.IDLE
    detail: str = "en attente de l'ordre de départ"
    _entered_at: float = 0.0
    _last_attempt: float = -1e9
    _attempts: int = 0
    _dropped: bool = False
    _was_airborne: bool = False

    # ------------------------------------------------------------------
    def _go(self, state: State, now: float, detail: str, actions: list):
        self.state, self.detail, self._entered_at = state, detail, now
        self._attempts, self._last_attempt = 0, -1e9
        actions.append(("log", f"{state.value} : {detail}"))

    def step(self, i: Inputs) -> list[tuple]:
        """Fait avancer la machine d'un pas. Renvoie la liste des actions à exécuter :
        ("upload_mission",), ("set_mode", "AUTO"), ("arm", True), ("drop",), ("log", texte)."""
        a: list[tuple] = []
        s = self.state

        if not i.connected and s not in (State.IDLE, State.DONE, State.ABORTED, State.FAILSAFE):
            if not i.armed and s in (State.UPLOAD_MISSION, State.ARMING):
                self._go(State.ABORTED, i.now, "liaison autopilote perdue avant le décollage", a)
            return a

        if s == State.IDLE:
            if i.start_requested:
                if not i.connected:
                    a.append(("log", "départ refusé : autopilote non connecté"))
                else:
                    self._go(State.UPLOAD_MISSION, i.now, "envoi de la mission", a)
                    a.append(("upload_mission",))

        elif s == State.UPLOAD_MISSION:
            if i.mission_upload_ok is True:
                self._go(State.ARMING, i.now, "mission acceptée, passage en AUTO et armement", a)
            elif i.mission_upload_ok is False:
                self._go(State.ABORTED, i.now, "mission refusée par l'autopilote", a)
            elif i.now - self._entered_at > self.config.upload_timeout_s:
                self._go(State.ABORTED, i.now, "pas de réponse à l'envoi de mission", a)

        elif s == State.ARMING:
            if i.armed and i.mode == "AUTO":
                self._was_airborne = False
                self._go(State.MISSION, i.now, "mission en cours", a)
            elif i.now - self._last_attempt >= self.config.arming_retry_s:
                if self._attempts >= self.config.arming_max_attempts:
                    self._go(State.ABORTED, i.now, "armement impossible (vérifier les pré-armements)", a)
                else:
                    self._attempts += 1
                    self._last_attempt = i.now
                    if i.mode != "AUTO":
                        a.append(("set_mode", "AUTO"))
                    if not i.armed:
                        a.append(("arm", True))

        elif s in (State.MISSION, State.TARGET_FOUND):
            if not i.landed:
                self._was_airborne = True
            if i.mode in FAILSAFE_MODES:
                self._go(State.FAILSAFE, i.now, f"l'autopilote a pris la main ({i.mode})", a)
            elif self._was_airborne and i.landed and not i.armed:
                self._go(State.DONE, i.now, "posé et désarmé", a)
            elif s == State.MISSION and i.target_detected and i.target_confidence >= self.config.target_min_confidence:
                self._go(State.TARGET_FOUND, i.now, f"cible vue (confiance {i.target_confidence:.2f})", a)
                if self.config.drop_enabled and not self._dropped:
                    self._dropped = True
                    a.append(("drop",))
            elif s == State.TARGET_FOUND and not i.target_detected:
                self._go(State.MISSION, i.now, "cible hors champ, mission poursuivie", a)

        elif s == State.FAILSAFE:
            if i.landed and not i.armed:
                self._go(State.DONE, i.now, "posé après failsafe", a)

        return a
