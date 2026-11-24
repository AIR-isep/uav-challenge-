import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")
from isep_perception.detector import detect_red  # noqa: E402


def grass(h=480, w=640):
    img = np.zeros((h, w, 3), np.uint8)
    img[:] = (40, 120, 40)  # BGR vert
    return img


def test_no_target():
    assert not detect_red(grass()).detected


def test_red_square_found_and_centered():
    img = grass()
    img[200:280, 400:480] = (20, 20, 220)  # carré rouge, centre (440, 240)
    d = detect_red(img)
    assert d.detected and d.confidence > 0.9
    assert d.u == pytest.approx(2 * 439.5 / 640 - 1, abs=0.01)
    assert d.v == pytest.approx(0.0, abs=0.01)


def test_tiny_blob_ignored():
    img = grass()
    img[10:12, 10:12] = (20, 20, 220)
    assert not detect_red(img).detected
