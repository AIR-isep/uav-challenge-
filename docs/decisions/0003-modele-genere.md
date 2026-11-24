# 0003 : modèle Gazebo généré depuis un fichier YAML

**Décision (24/11/2026)** : `model.sdf` n'est jamais édité à la main. Il est généré par
`isep_description/scripts/generate_model.py` depuis `config/isep_vtol.yaml`, qui produit aussi
l'affectation des sorties servo ArduPilot.

**Pourquoi.** Les positions se lisent dans Fusion 360 (mm, repère CAO) et le script fait la
conversion vers Gazebo. Le modèle et les paramètres ArduPilot ne peuvent pas diverger. La CI
vérifie que le fichier généré correspond à la configuration.
