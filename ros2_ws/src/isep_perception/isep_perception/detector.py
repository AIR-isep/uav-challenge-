"""Détection de la cible rouge, sans dépendance ROS (testable avec numpy + OpenCV).

Méthode volontairement simple pour démarrer : seuillage HSV du rouge, plus grande
tache, confiance = taux de remplissage du rectangle englobant (une cible carrée
vue de dessus remplit ~100 % de son rectangle). À remplacer par YOLO quand le jeu
de données synthétiques sera prêt.
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class Detection:
    detected: bool
    confidence: float = 0.0
    u: float = 0.0          # -1 (gauche) .. 1 (droite)
    v: float = 0.0          # -1 (haut) .. 1 (bas)
    area_ratio: float = 0.0


def detect_red(bgr: np.ndarray, min_area_ratio: float = 2e-4) -> Detection:
    h, w = bgr.shape[:2]
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    low = cv2.inRange(hsv, (0, 120, 70), (10, 255, 255))
    high = cv2.inRange(hsv, (170, 120, 70), (180, 255, 255))
    mask = cv2.morphologyEx(low | high, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return Detection(False)
    c = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(c)
    ratio = area / float(w * h)
    if ratio < min_area_ratio:
        return Detection(False)
    x, y, bw, bh = cv2.boundingRect(c)
    fill = area / float(max(bw * bh, 1))
    m = cv2.moments(c)
    cx, cy = m["m10"] / m["m00"], m["m01"] / m["m00"]
    return Detection(True, float(np.clip(fill, 0.0, 1.0)), float(2 * cx / w - 1), float(2 * cy / h - 1), float(ratio))
