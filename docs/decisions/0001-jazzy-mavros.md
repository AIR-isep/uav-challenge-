# 0001 : ROS 2 Jazzy et MAVROS

**Décision (24/11/2026)** : le logiciel embarqué cible ROS 2 Jazzy sur Ubuntu 24.04 et dialogue
avec ArduPilot par MAVROS (MAVLink).

**Contexte.** Le PC de simulation et le Raspberry Pi 5 sont sous Ubuntu 24.04, où Jazzy est la
version de ROS 2 associée à Gazebo Harmonic. Le pont ROS 2 natif d'ArduPilot (DDS, `ardupilot_gz`)
n'est documenté que pour ROS 2 Humble (Ubuntu 22.04). MAVROS est disponible en paquet pour Jazzy
et fonctionne avec toutes les versions d'ArduPilot.

**Conséquences.**
- Le portable (WSL 22.04) reste une station sol en MAVLink, indépendante de la version de ROS.
- Le code de mission ne parle qu'à `isep_interfaces` et aux services MAVROS : passer au DDS
  natif plus tard ne touchera que `isep_bringup` et `mission_node.py`.
