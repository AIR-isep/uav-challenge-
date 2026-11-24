-- FICHIER GÉNÉRÉ par ros2_ws/src/isep_description/scripts/generate_model.py : ne pas éditer.
-- Mixage moteur isep_vtol (tilt-tri), à charger avec Q_FRAME_CLASS 15 et SCR_ENABLE 1.
-- add_motor_raw(index, roulis, tangage, lacet, ordre de test) ; index 0 = Motor1 (fonction 33).
MotorsMatrix:add_motor_raw(0, -0.3400, 0.1600, 0.0, 1)  -- front_right
MotorsMatrix:add_motor_raw(1, 0.3400, 0.1600, 0.0, 2)  -- front_left
MotorsMatrix:add_motor_raw(2, 0.0000, -0.7600, 0.0, 3)  -- rear
MotorsMatrix:set_throttle_factor(0, 1.0000)  -- front_right
MotorsMatrix:set_throttle_factor(1, 1.0000)  -- front_left
MotorsMatrix:set_throttle_factor(2, 0.4211)  -- rear
assert(MotorsMatrix:init(3), "isep_vtol : échec de l'initialisation de la matrice moteur")
motors:set_frame_string("isep_vtol tilt-tri")
