# 0002 : configuration tilt-tri à lacet vectoriel

**Décision (24/11/2026)** : deux nacelles avant basculantes (hélice au-dessus du pivot) et un
moteur arrière suspendu sous son pivot (hélice vers le bas en VTOL, poussée vers le haut), qui
bascule de 90° pour pointer vers l'arrière en croisière (hélice propulsive). ArduPilot : `Q_FRAME_CLASS 7` (tri),
`Q_TILT_TYPE 2` (lacet par basculement différentiel des nacelles avant), `Q_TILT_MASK 11`
(moteurs 1, 2 et 4 basculants).

**Vérifié dans le code d'ArduPlane 4.7** (`tiltrotor.cpp`, `Tiltrotor::vectoring`) : en mode
vectoriel, la sortie `TiltMotorsRear` (45) suit l'angle de basculement commun, et les sorties
75/76 ajoutent l'écart de lacet. Les servos couvrent de −`Q_TILT_YAW_ANGLE` à 90°.

**Conséquences.** Trois moteurs au lieu de quatre (nomenclature à mettre à jour), lacet sans
servo de queue. Le simulateur interne d'ArduPilot a un modèle proche (`quadplane-tilttrivec`) pour
tester la logique avant Gazebo.
