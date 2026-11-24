# Cible détectée dans l'image (isep_perception)
std_msgs/Header header
bool detected
float32 confidence  # 0 à 1
float32 u           # position horizontale normalisée, -1 (gauche) à 1 (droite)
float32 v           # position verticale normalisée, -1 (haut) à 1 (bas)
float32 area_ratio  # surface de la cible / surface de l'image
