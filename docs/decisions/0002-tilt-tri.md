# 0002 : configuration tilt-tri à lacet vectoriel

**Décision (24/11/2026)** : deux nacelles avant basculantes (hélice au-dessus du pivot) et un
moteur arrière suspendu sous son pivot (hélice vers le bas en VTOL, poussée vers le haut), qui
bascule de 90° pour pointer vers l'arrière en croisière (hélice propulsive). ArduPilot : `Q_FRAME_CLASS 15` (matrice moteur par script Lua),
`Q_TILT_TYPE 2` (lacet par basculement différentiel des nacelles avant), `Q_TILT_MASK 7`
(moteurs 1, 2 et 3 basculants).

**Vérifié dans le code d'ArduPlane 4.7** (`tiltrotor.cpp`, `Tiltrotor::vectoring`) : en mode
vectoriel, la sortie `TiltMotorsRear` (45) suit l'angle de basculement commun, et les sorties
75/76 ajoutent l'écart de lacet. Les servos couvrent de −`Q_TILT_YAW_ANGLE` à 90°.

**Conséquences.** Trois moteurs au lieu de quatre (nomenclature à mettre à jour), lacet sans
servo de queue. Le simulateur interne d'ArduPilot a un modèle proche (`quadplane-tilttrivec`) pour
tester la logique avant Gazebo.

**Mise à jour (24/11/2026) : matrice moteur personnalisée.** Avec le mixeur tri standard
(`Q_FRAME_CLASS 7`), le drone basculait vers l'avant dès le décollage en simulation : ce mixeur
suppose un moteur arrière deux fois plus loin du CG que les moteurs avant, alors qu'ici il est
4,7 fois plus loin (0,76 m contre 0,16 m). Le générateur produit maintenant
`ardupilot/scripts/generated/isep_vtol_motors.lua`, avec des facteurs de roulis et de tangage
tirés de la géométrie réelle et un facteur de gaz de 0,42 sur le moteur arrière, pour qu'une
même commande de gaz ne crée pas de couple de tangage. Sur la vraie carte : copier ce script
dans `APM/scripts/` de la carte SD.
