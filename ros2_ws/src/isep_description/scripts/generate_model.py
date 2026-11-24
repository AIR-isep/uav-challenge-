#!/usr/bin/env python3
"""Génère le modèle Gazebo isep_vtol et les sorties servo ArduPilot associées.

Source unique : config/isep_vtol.yaml (positions en mm dans le repère Fusion 360).
Sorties :
  - models/isep_vtol/model.sdf et model.config
  - <racine du dépôt>/ardupilot/params/generated/isep_vtol_servos.param

Usage :
  python3 generate_model.py                 # chemins par défaut
  python3 generate_model.py --config autre.yaml --check   # vérifie sans écrire
"""
from __future__ import annotations

import argparse
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

PKG_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = PKG_DIR.parents[2]
G = 9.80665

# Fonctions servo ArduPilot -> bit du masque Q_TILT_MASK (moteurs 1..12)
MOTOR_FUNCTION_TO_INDEX = {33: 1, 34: 2, 35: 3, 36: 4, 37: 5, 38: 6, 39: 7, 40: 8}


# ---------------------------------------------------------------------------
# Repères
# ---------------------------------------------------------------------------
class Frames:
    """Conversion repère Fusion (mm, nez en Y=0, +Y queue, +X gauche, +Z haut)
    vers repère Gazebo du modèle (m, origine au CG, X avant, Y gauche, Z haut)."""

    def __init__(self, cg_mm):
        self.cg = cg_mm

    def pos(self, p_mm):
        x, y, z = p_mm
        cx, cy, cz = self.cg
        return (-(y - cy) / 1000.0, (x - cx) / 1000.0, (z - cz) / 1000.0)

    @staticmethod
    def size(s_mm):
        sx, sy, sz = s_mm
        return (sy / 1000.0, sx / 1000.0, sz / 1000.0)

    @staticmethod
    def mirror(p_mm):
        return [-p_mm[0], p_mm[1], p_mm[2]]


# ---------------------------------------------------------------------------
# Petits utilitaires XML
# ---------------------------------------------------------------------------
def fmt(v):
    if isinstance(v, (list, tuple)):
        return " ".join(fmt(x) for x in v)
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, float):
        s = f"{v:.6g}"
        return "0" if s == "-0" else s
    return str(v)


def sub(parent, tag, text=None, **attrib):
    el = ET.SubElement(parent, tag, {k: fmt(v) for k, v in attrib.items()})
    if text is not None:
        el.text = fmt(text)
    return el


def pose(parent, xyz, rpy=(0.0, 0.0, 0.0), relative_to=None):
    attrs = {"relative_to": relative_to} if relative_to else {}
    return sub(parent, "pose", list(xyz) + list(rpy), **attrs)


def inertial(parent, mass, ixx, iyy, izz, com=(0.0, 0.0, 0.0)):
    ine = sub(parent, "inertial")
    pose(ine, com)
    sub(ine, "mass", mass)
    it = sub(ine, "inertia")
    for k, v in (("ixx", ixx), ("ixy", 0.0), ("ixz", 0.0), ("iyy", iyy), ("iyz", 0.0), ("izz", izz)):
        sub(it, k, v)
    return ine


def material(parent, rgb, alpha=1.0):
    m = sub(parent, "material")
    sub(m, "ambient", list(rgb) + [alpha])
    sub(m, "diffuse", list(rgb) + [alpha])
    sub(m, "specular", [0.2, 0.2, 0.2, alpha])


def lift_drag(model, link, area, cp, forward, upward, cla, a0, alpha_stall,
              cda=0.1, cla_stall=-3.85, cda_stall=-0.92, rho=1.2041,
              control_joint=None, rad_to_cl=None):
    p = sub(model, "plugin", filename="gz-sim-lift-drag-system", name="gz::sim::systems::LiftDrag")
    for k, v in (("a0", a0), ("alpha_stall", alpha_stall), ("cla", cla), ("cda", cda),
                 ("cma", 0.0), ("cla_stall", cla_stall), ("cda_stall", cda_stall),
                 ("cma_stall", 0.0), ("area", area), ("air_density", rho), ("cp", cp),
                 ("forward", forward), ("upward", upward), ("link_name", link)):
        sub(p, k, v)
    if control_joint:
        sub(p, "control_joint_name", control_joint)
        sub(p, "control_joint_rad_to_cl", rad_to_cl)
    return p


def revolute(model, name, parent, child, axis, lower, upper, damping, joint_pose=None):
    j = sub(model, "joint", name=name, type="revolute")
    if joint_pose is not None:
        pose(j, joint_pose[0], joint_pose[1], relative_to=joint_pose[2])
    sub(j, "parent", parent)
    sub(j, "child", child)
    ax = sub(j, "axis")
    sub(ax, "xyz", axis)
    lim = sub(ax, "limit")
    sub(lim, "lower", lower)
    sub(lim, "upper", upper)
    dyn = sub(ax, "dynamics")
    sub(dyn, "damping", damping)
    return j


def control(plugin, channel, joint, ctype, multiplier, offset, p, i, d, cmd_max, comment):
    plugin.append(ET.Comment(f" SERVO{channel + 1} : {comment} "))
    c = sub(plugin, "control", channel=channel)
    for k, v in (("jointName", joint), ("useForce", 1), ("multiplier", multiplier),
                 ("offset", offset), ("servo_min", 1000), ("servo_max", 2000),
                 ("type", ctype), ("p_gain", p), ("i_gain", i), ("d_gain", d),
                 ("i_max", 0), ("i_min", 0), ("cmd_max", cmd_max), ("cmd_min", -cmd_max)):
        sub(c, k, v)


def unit(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v)


# ---------------------------------------------------------------------------
# Construction du modèle
# ---------------------------------------------------------------------------
def build(cfg):
    fr = Frames(cfg["mass"]["cg_mm"])
    name = cfg["model_name"]
    prop = cfg["propulsion"]
    aero = cfg["aero"]
    rho = aero["air_density"]

    sdf = ET.Element("sdf", version="1.9")
    model = sub(sdf, "model", name=name)
    model.append(ET.Comment(" FICHIER GÉNÉRÉ par scripts/generate_model.py depuis config/isep_vtol.yaml : ne pas éditer "))
    pose(model, (0.0, 0.0, 0.0))

    # --- masses des sous-ensembles mobiles (pour placer le CDG du corps) ---
    movable = []  # (masse, position gazebo)
    rotors = prop["rotors"]
    def rotor_offset(r):
        # + : hélice au-dessus du pivot ; - : moteur suspendu sous le pivot
        return r.get("rotor_offset_mm", prop["rotor_offset_mm"]) / 1000.0

    for r in rotors.values():
        pv = fr.pos(r["pivot_mm"])
        movable.append((prop["nacelle_mass_kg"], pv))
        movable.append((prop["rotor_mass_kg"], (pv[0], pv[1], pv[2] + rotor_offset(r))))
    surf_mass = 0.01
    surfaces = []
    hinge_a = aero["ailerons"]["hinge_mm"]
    hinge_v = aero["vtail"]["hinge_mm"]
    for p in (hinge_a, fr.mirror(hinge_a), hinge_v, fr.mirror(hinge_v)):
        surfaces.append(fr.pos(p))
        movable.append((surf_mass, fr.pos(p)))
    movable.append((0.05, (0.0, 0.0, 0.0)))  # imu_link
    m_total = cfg["mass"]["total_kg"]
    m_mov = sum(m for m, _ in movable)
    m_base = m_total - m_mov
    com_base = tuple(-sum(m * p[i] for m, p in movable) / m_base for i in range(3))

    # --- corps principal ---
    base = sub(model, "link", name="base_link")
    I = cfg["mass"]["inertia"]
    inertial(base, m_base, I["ixx"], I["iyy"], I["izz"], com=com_base)
    vis = sub(base, "visual", name="airframe")
    cy, cz = cfg["mass"]["cg_mm"][1], cfg["mass"]["cg_mm"][2]
    pose(vis, (cy / 1000.0, 0.0, -cz / 1000.0), (0.0, 0.0, math.pi / 2))
    geo = sub(sub(vis, "geometry"), "mesh")
    sub(geo, "uri", f"model://{name}/meshes/{cfg['mesh']['file']}")
    sub(geo, "scale", [cfg["mesh"]["scale"]] * 3)
    material(vis, cfg["mesh"]["color"])
    for cname, (c_mm, s_mm) in cfg["collision_boxes_mm"].items():
        col = sub(base, "collision", name=f"{cname}_collision")
        pose(col, fr.pos(c_mm))
        sub(sub(sub(col, "geometry"), "box"), "size", fr.size(s_mm))
    for i, p_mm in enumerate(cfg["landing_points_mm"]):
        col = sub(base, "collision", name=f"landing_point_{i}")
        pose(col, fr.pos(p_mm))
        sub(sub(sub(col, "geometry"), "sphere"), "radius", 0.01)
        surf = sub(sub(sub(col, "surface"), "friction"), "ode")
        sub(surf, "mu", 0.8)
        sub(surf, "mu2", 0.8)

    _add_sensors(base, cfg, fr)

    # --- IMU (même schéma que les modèles officiels ArduPilot) ---
    imu = sub(model, "link", name="imu_link")
    inertial(imu, 0.05, 1e-5, 1e-5, 1e-5)
    s = sub(imu, "sensor", name="imu_sensor", type="imu")
    pose(s, (0, 0, 0), (math.pi, 0.0, 0.0))
    sub(s, "always_on", 1)
    sub(s, "update_rate", 1000.0)
    revolute(model, "imu_joint", "base_link", "imu_link", (0, 0, 1), 0.0, 0.0, 1.0)

    # --- rotors basculants ---
    tilt = prop["tilt"]
    yaw_deg = tilt["yaw_angle_deg"]
    blade_cla, blade_a0 = 4.25, 0.3
    rcp = prop["blade_cp_m"]
    w = prop["max_rad_s"]
    blade_area = prop["max_thrust_n"] / (rho * w * w * rcp * rcp * blade_cla * blade_a0)
    controls = []
    for key, r in rotors.items():
        pv = fr.pos(r["pivot_mm"])
        r_off = rotor_offset(r)
        nac, rot = f"nacelle_{key}", f"rotor_{key}"
        # nacelle (moteur + support), pivote autour de l'axe Y (vers la gauche)
        link = sub(model, "link", name=nac)
        pose(link, pv, relative_to="__model__")
        rad, ln = 0.019, 0.04
        mn = prop["nacelle_mass_kg"]
        inertial(link, mn, mn * (3 * rad ** 2 + ln ** 2) / 12, mn * (3 * rad ** 2 + ln ** 2) / 12, mn * rad ** 2 / 2,
                 com=(0.0, 0.0, r_off / 2))
        v = sub(link, "visual", name="motor")
        pose(v, (0.0, 0.0, r_off / 2))
        cyl = sub(sub(v, "geometry"), "cylinder")
        sub(cyl, "radius", rad)
        sub(cyl, "length", abs(r_off))
        material(v, (0.15, 0.15, 0.15))
        revolute(model, f"tilt_{key}_joint", "base_link", nac, (0, 1, 0),
                 -math.radians(yaw_deg + 2), math.radians(92), 0.05)
        # hélice
        link = sub(model, "link", name=rot)
        pose(link, (0.0, 0.0, r_off), relative_to=nac)
        mr = prop["rotor_mass_kg"]
        L = 0.254
        inertial(link, mr, 1e-6, mr * L * L / 12, mr * L * L / 12)
        v = sub(link, "visual", name="disc")
        cyl = sub(sub(v, "geometry"), "cylinder")
        sub(cyl, "radius", 0.127)
        sub(cyl, "length", 0.004)
        material(v, (0.1, 0.1, 0.1), alpha=0.35)
        revolute(model, f"{rot}_joint", nac, rot, (0, 0, 1), -1e16, 1e16, 0.002)
        s_ = 1.0 if r["spin"] == "ccw" else -1.0
        for sign in (1.0, -1.0):
            lift_drag(model, rot, blade_area, (sign * rcp, 0.0, 0.0), (0.0, sign * s_, 0.0), (0.0, 0.0, 1.0),
                      cla=blade_cla, a0=blade_a0, alpha_stall=1.4, cda=0.1, cla_stall=-0.025, cda_stall=0.0, rho=rho)
        controls.append((r["motor_servo"] - 1, f"{rot}_joint", "VELOCITY", s_ * w, 0.0, 0.2, 0.0, 0.0, 2.5,
                         f"moteur {key} (fonction {r['motor_function']}), {r['spin']}"))
        total = 90.0 + yaw_deg
        controls.append((r["tilt_servo"] - 1, f"tilt_{key}_joint", "POSITION", math.radians(total), -yaw_deg / total,
                         tilt["servo_p_gain"], 0.0, tilt["servo_d_gain"], tilt["servo_max_torque_nm"],
                         f"basculement {key} (fonction {r['tilt_function']}), {-yaw_deg:g}° à 90°"))

    # --- gouvernes (liens légers, invisibles : le STL est d'un seul bloc) ---
    a = aero["ailerons"]
    va = aero["vtail"]
    s2 = 1 / math.sqrt(2)
    surf_defs = [
        ("aileron_left", fr.pos(a["hinge_mm"]), (0, 1, 0), a, -1.0, a["left_servo"], "aileron gauche (fonction 4)"),
        ("aileron_right", fr.pos(fr.mirror(a["hinge_mm"])), (0, 1, 0), a, 1.0, a["right_servo"], "aileron droit (fonction 4)"),
        ("vtail_left", fr.pos(va["hinge_mm"]), (0, s2, s2), va, 1.0, va["left_servo"], "empennage en V gauche (fonction 79)"),
        ("vtail_right", fr.pos(fr.mirror(va["hinge_mm"])), (0, s2, -s2), va, 1.0, va["right_servo"], "empennage en V droit (fonction 80)"),
    ]
    for sname, hp, axis, spec, sign, servo, comment in surf_defs:
        link = sub(model, "link", name=f"{sname}_link")
        pose(link, hp, relative_to="__model__")
        inertial(link, surf_mass, 1e-5, 1e-5, 1e-5)
        lim = math.radians(spec["max_deflection_deg"])
        revolute(model, f"{sname}_joint", "base_link", f"{sname}_link", axis, -lim, lim, 0.1)
        controls.append((servo - 1, f"{sname}_joint", "POSITION", sign * 2 * lim, -0.5, 10.0, 0.0, 0.0, 2.5, comment))

    # --- portance ---
    wc = aero["wing_center"]
    lift_drag(model, "base_link", wc["area_m2"], fr.pos(wc["cp_mm"]), (1, 0, 0), (0, 0, 1),
              cla=wc["cla"], a0=wc["a0"], alpha_stall=wc["alpha_stall"], rho=rho)
    for side, cp_mm in (("left", a["cp_mm"]), ("right", fr.mirror(a["cp_mm"]))):
        lift_drag(model, "base_link", a["area_m2"], fr.pos(cp_mm), (1, 0, 0), (0, 0, 1),
                  cla=wc["cla"], a0=wc["a0"], alpha_stall=wc["alpha_stall"], rho=rho,
                  control_joint=f"aileron_{side}_joint", rad_to_cl=a["rad_to_cl"])
    for side, cp_mm, up in (("left", va["cp_mm"], (0, -s2, s2)), ("right", fr.mirror(va["cp_mm"]), (0, s2, s2))):
        lift_drag(model, "base_link", va["area_m2"], fr.pos(cp_mm), (1, 0, 0), up,
                  cla=va["cla"], a0=0.0, alpha_stall=0.3, rho=rho,
                  control_joint=f"vtail_{side}_joint", rad_to_cl=va["rad_to_cl"])

    # --- plugins ---
    sub(model, "plugin", filename="gz-sim-joint-state-publisher-system", name="gz::sim::systems::JointStatePublisher")
    ap = sub(model, "plugin", name="ArduPilotPlugin", filename="ArduPilotPlugin")
    for k, v in (("fdm_addr", "127.0.0.1"), ("fdm_port_in", cfg["ardupilot"]["fdm_port_in"]),
                 ("connectionTimeoutMaxCount", 5), ("lock_step", 1), ("have_32_channels", 0)):
        sub(ap, k, v)
    sub(ap, "modelXYZToAirplaneXForwardZDown", "0 0 0 180 0 0", degrees="true")
    sub(ap, "gazeboXYZToNED", "0 0 0 180 0 90", degrees="true")
    sub(ap, "imuName", "imu_sensor")
    for c in sorted(controls):
        control(ap, *c)

    info = {
        "m_base": m_base, "com_base": com_base, "blade_area": blade_area, "controls": sorted(controls),
        "fr": fr, "rotors": rotors,
    }
    return sdf, info


def _add_sensors(base, cfg, fr):
    sens = cfg.get("sensors", {})
    c = sens.get("camera", {})
    if c.get("enabled"):
        s = sub(base, "sensor", name="camera", type="camera")
        pose(s, fr.pos(c["pos_mm"]), (0.0, math.radians(c["pitch_down_deg"]), 0.0))
        sub(s, "always_on", 1)
        sub(s, "update_rate", c["rate_hz"])
        sub(s, "topic", c["topic"])
        cam = sub(s, "camera")
        sub(cam, "horizontal_fov", math.radians(c["hfov_deg"]))
        img = sub(cam, "image")
        sub(img, "width", c["width"])
        sub(img, "height", c["height"])
        sub(img, "format", "R8G8B8")
        clip = sub(cam, "clip")
        sub(clip, "near", 0.05)
        sub(clip, "far", 300.0)
    for key, n_samples, pitch in (("lidar_2d", None, 0.0), ("rangefinder_down", 1, math.pi / 2)):
        l_ = sens.get(key, {})
        if not l_.get("enabled"):
            continue
        s = sub(base, "sensor", name=key, type="gpu_lidar")
        pose(s, fr.pos(l_["pos_mm"]), (0.0, pitch, 0.0))
        sub(s, "always_on", 1)
        sub(s, "update_rate", l_["rate_hz"])
        sub(s, "topic", l_["topic"])
        lid = sub(s, "lidar")
        scan = sub(lid, "scan")
        h = sub(scan, "horizontal")
        n = n_samples or l_["samples"]
        sub(h, "samples", n)
        sub(h, "resolution", 1)
        sub(h, "min_angle", 0.0 if n == 1 else -math.pi)
        sub(h, "max_angle", 0.0 if n == 1 else math.pi)
        rng = sub(lid, "range")
        sub(rng, "min", l_.get("range_min_m", 0.15))
        sub(rng, "max", l_["range_max_m"])
        sub(rng, "resolution", 0.01)


def servo_params(cfg, info):
    lines = [
        "# FICHIER GÉNÉRÉ par ros2_ws/src/isep_description/scripts/generate_model.py",
        "# Affectation des sorties servo du modèle Gazebo isep_vtol. Ne pas éditer à la main.",
    ]
    funcs = {}
    prop = cfg["propulsion"]
    mask = 0
    for r in prop["rotors"].values():
        funcs[r["motor_servo"]] = r["motor_function"]
        funcs[r["tilt_servo"]] = r["tilt_function"]
        mask |= 1 << (MOTOR_FUNCTION_TO_INDEX[r["motor_function"]] - 1)
    a, v = cfg["aero"]["ailerons"], cfg["aero"]["vtail"]
    funcs[a["left_servo"]] = 4
    funcs[a["right_servo"]] = 4
    funcs[v["left_servo"]] = 79
    funcs[v["right_servo"]] = 80
    for n in range(1, 14):
        f = funcs.get(n, 0)
        lines.append(f"SERVO{n}_FUNCTION {f}")
        if f:
            lines.append(f"SERVO{n}_MIN 1000")
            lines.append(f"SERVO{n}_MAX 2000")
            lines.append(f"SERVO{n}_TRIM {1000 if 33 <= f <= 40 else 1500}")
            lines.append(f"SERVO{n}_REVERSED 0")
    lines.append(f"Q_TILT_MASK {mask}")
    lines.append(f"Q_TILT_YAW_ANGLE {prop['tilt']['yaw_angle_deg']}")
    return "\n".join(lines) + "\n"


def motor_matrix_lua(cfg, info):
    """Script Lua de mixage (Q_FRAME_CLASS 15) calculé depuis la géométrie réelle.

    Facteurs ArduPilot : roulis = +bras vers la gauche, tangage = +bras vers l'avant
    (même convention que AP_MotorsMatrix::add_motor). Lacet : 0, il est obtenu par le
    basculement différentiel des nacelles avant (Q_TILT_TYPE 2).
    Facteurs de gaz : choisis pour qu'une même commande de gaz donne un moment de
    tangage nul autour du CG (sum tf_i * x_i = 0), le moteur avant valant 1.
    """
    fr = info["fr"]
    motors = []
    for key, r in cfg["propulsion"]["rotors"].items():
        x, y, _ = fr.pos(r["pivot_mm"])
        motors.append((MOTOR_FUNCTION_TO_INDEX[r["motor_function"]] - 1, key, x, y))
    motors.sort()
    front = [m for m in motors if m[2] > 0]
    rear = [m for m in motors if m[2] <= 0]
    m_front = sum(m[2] for m in front)
    m_rear = -sum(m[2] for m in rear)
    tf = {m[0]: 1.0 for m in front}
    for m in rear:
        tf[m[0]] = m_front / m_rear / len(rear)
    lines = [
        "-- FICHIER GÉNÉRÉ par ros2_ws/src/isep_description/scripts/generate_model.py : ne pas éditer.",
        "-- Mixage moteur isep_vtol (tilt-tri), à charger avec Q_FRAME_CLASS 15 et SCR_ENABLE 1.",
        "-- add_motor_raw(index, roulis, tangage, lacet, ordre de test) ; index 0 = Motor1 (fonction 33).",
    ]
    for order, (idx, key, x, y) in enumerate(motors, start=1):
        lines.append(f"MotorsMatrix:add_motor_raw({idx}, {y:.4f}, {x:.4f}, 0.0, {order})  -- {key}")
    for idx, key, _, _ in motors:
        lines.append(f"MotorsMatrix:set_throttle_factor({idx}, {tf[idx]:.4f})  -- {key}")
    lines += [
        f'assert(MotorsMatrix:init({len(motors)}), "isep_vtol : échec de l\'initialisation de la matrice moteur")',
        'motors:set_frame_string("isep_vtol tilt-tri")',
        "",
    ]
    return "\n".join(lines)


def summary(cfg, info):
    fr = info["fr"]
    weight = cfg["mass"]["total_kg"] * G
    xs = {k: fr.pos(r["pivot_mm"])[0] for k, r in info["rotors"].items()}
    front = [k for k in xs if k.startswith("front")]
    x_front = sum(xs[k] for k in front) / len(front)
    x_rear = xs["rear"]
    rear_share = x_front / (x_front - x_rear)
    t_rear = weight * rear_share
    t_front = weight * (1 - rear_share) / len(front)
    tmax = cfg["propulsion"]["max_thrust_n"]
    out = [
        f"Masse du corps {info['m_base']:.3f} kg, CDG du corps décalé de {fmt(list(info['com_base']))} m",
        f"Surface de pale LiftDrag : {info['blade_area'] * 1e4:.2f} cm²",
        "Poussées en stationnaire (équilibre en tangage) :",
        f"  avant : {t_front:.1f} N chacune ({100 * t_front / tmax:.0f} % du max)",
        f"  arrière : {t_rear:.1f} N ({100 * t_rear / tmax:.0f} % du max)",
    ]
    if max(t_front, t_rear) > 0.75 * tmax:
        out.append("  ATTENTION : moins de 25 % de marge de poussée sur un moteur en stationnaire")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(PKG_DIR / "config" / "isep_vtol.yaml"))
    ap.add_argument("--model-dir", default=str(PKG_DIR / "models" / "isep_vtol"))
    ap.add_argument("--params-out", default=str(REPO_DIR / "ardupilot" / "params" / "generated" / "isep_vtol_servos.param"))
    ap.add_argument("--lua-out", default=str(REPO_DIR / "ardupilot" / "scripts" / "generated" / "isep_vtol_motors.lua"))
    ap.add_argument("--check", action="store_true", help="génère en mémoire et affiche le résumé, sans écrire")
    args = ap.parse_args(argv)

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    sdf, info = build(cfg)
    ET.indent(sdf, space="  ")
    xml = '<?xml version="1.0"?>\n' + ET.tostring(sdf, encoding="unicode") + "\n"
    params = servo_params(cfg, info)
    print(summary(cfg, info))
    if args.check:
        return 0

    model_dir = Path(args.model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    (model_dir / "model.sdf").write_text(xml, encoding="utf-8")
    (model_dir / "model.config").write_text(
        f"""<?xml version="1.0"?>
<model>
  <name>{cfg['model_name']}</name>
  <version>0.1</version>
  <sdf version="1.9">model.sdf</sdf>
  <author><name>Équipe AIR - ISEP</name></author>
  <description>VTOL tilt-tri du Dassault UAV Challenge, généré depuis config/isep_vtol.yaml</description>
</model>
""", encoding="utf-8")
    p_out = Path(args.params_out)
    p_out.parent.mkdir(parents=True, exist_ok=True)
    p_out.write_text(params, encoding="utf-8")
    lua_out = Path(args.lua_out)
    lua_out.parent.mkdir(parents=True, exist_ok=True)
    lua_out.write_text(motor_matrix_lua(cfg, info), encoding="utf-8")
    print(f"Écrit : {model_dir / 'model.sdf'}\nÉcrit : {p_out}\nÉcrit : {lua_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
