"""Nœud ROS 2 de mission : relie la machine à états à ArduPilot via MAVROS.

Entrées : /mavros/state, /mavros/extended_state, /isep/target, service /isep/start
Sorties : /isep/mission_state, services MAVROS (mission/push, set_mode, cmd/arming, cmd/command)
"""
from __future__ import annotations

import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger
from mavros_msgs.msg import ExtendedState, State as MavState, Waypoint
from mavros_msgs.srv import CommandBool, CommandLong, SetMode, WaypointPush

from isep_interfaces.msg import MissionState, Target
from isep_mission.state_machine import Config, Inputs, MissionStateMachine
from isep_mission.wpl import load_wpl

MAV_CMD_DO_SET_SERVO = 183


class MissionNode(Node):
    def __init__(self):
        super().__init__("isep_mission")
        self.declare_parameter("mission_file", "")
        self.declare_parameter("drop_servo", 12)
        self.declare_parameter("drop_pwm", 1900)
        self.declare_parameter("drop_enabled", True)
        self.declare_parameter("target_min_confidence", 0.6)
        self.declare_parameter("mavros_ns", "/mavros")

        ns = self.get_parameter("mavros_ns").value
        cfg = Config(
            drop_enabled=self.get_parameter("drop_enabled").value,
            target_min_confidence=self.get_parameter("target_min_confidence").value,
        )
        self.sm = MissionStateMachine(config=cfg)
        self.mav = MavState()
        self.landed = True
        self.target = Target()
        self.start_requested = False
        self.upload_ok = None

        self.create_subscription(MavState, f"{ns}/state", self._on_state, 10)
        self.create_subscription(ExtendedState, f"{ns}/extended_state", self._on_ext, 10)
        self.create_subscription(Target, "/isep/target", self._on_target, 10)
        self.pub = self.create_publisher(MissionState, "/isep/mission_state", 10)
        self.create_service(Trigger, "/isep/start", self._on_start)

        self.cli_push = self.create_client(WaypointPush, f"{ns}/mission/push")
        self.cli_mode = self.create_client(SetMode, f"{ns}/set_mode")
        self.cli_arm = self.create_client(CommandBool, f"{ns}/cmd/arming")
        self.cli_cmd = self.create_client(CommandLong, f"{ns}/cmd/command")

        self.create_timer(0.2, self._tick)
        self.get_logger().info("prêt ; lancer la mission avec : ros2 service call /isep/start std_srvs/srv/Trigger")

    # --- entrées -------------------------------------------------------
    def _on_state(self, msg):
        self.mav = msg

    def _on_ext(self, msg):
        self.landed = msg.landed_state == ExtendedState.LANDED_STATE_ON_GROUND

    def _on_target(self, msg):
        self.target = msg

    def _on_start(self, _req, resp):
        self.start_requested = True
        resp.success = True
        resp.message = f"demande enregistrée (état actuel : {self.sm.state.value})"
        return resp

    # --- boucle --------------------------------------------------------
    def _tick(self):
        now = self.get_clock().now().nanoseconds * 1e-9
        inputs = Inputs(
            now=now, connected=self.mav.connected, armed=self.mav.armed, mode=self.mav.mode,
            landed=self.landed, start_requested=self.start_requested,
            mission_upload_ok=self.upload_ok, target_detected=self.target.detected,
            target_confidence=self.target.confidence,
        )
        self.start_requested = False
        for action in self.sm.step(inputs):
            self._execute(action)
        out = MissionState()
        out.header.stamp = self.get_clock().now().to_msg()
        out.state = self.sm.state.value
        out.detail = self.sm.detail
        self.pub.publish(out)

    def _execute(self, action):
        kind = action[0]
        if kind == "log":
            self.get_logger().info(action[1])
        elif kind == "upload_mission":
            self._upload_mission()
        elif kind == "set_mode":
            self._call(self.cli_mode, SetMode.Request(custom_mode=action[1]), "set_mode")
        elif kind == "arm":
            self._call(self.cli_arm, CommandBool.Request(value=action[1]), "arming")
        elif kind == "drop":
            req = CommandLong.Request(command=MAV_CMD_DO_SET_SERVO,
                                      param1=float(self.get_parameter("drop_servo").value),
                                      param2=float(self.get_parameter("drop_pwm").value))
            self._call(self.cli_cmd, req, "largage")

    def _upload_mission(self):
        self.upload_ok = None
        path = self.get_parameter("mission_file").value
        try:
            items = load_wpl(path)
        except (OSError, ValueError) as e:
            self.get_logger().error(f"mission illisible ({path}) : {e}")
            self.upload_ok = False
            return
        req = WaypointPush.Request(start_index=0)
        for it in items:
            wp = Waypoint(frame=it.frame, command=it.command, is_current=it.current,
                          autocontinue=it.autocontinue, param1=it.param1, param2=it.param2,
                          param3=it.param3, param4=it.param4, x_lat=it.lat, y_long=it.lon, z_alt=it.alt)
            req.waypoints.append(wp)

        def done(fut):
            res = fut.result()
            self.upload_ok = bool(res and res.success)
            self.get_logger().info(f"mission envoyée : {len(items)} points, succès={self.upload_ok}")

        self._call(self.cli_push, req, "mission/push", done)

    def _call(self, client, req, label, on_done=None):
        if not client.service_is_ready():
            self.get_logger().warn(f"service {label} indisponible (MAVROS lancé ?)")
            if label == "mission/push":
                self.upload_ok = False
            return
        fut = client.call_async(req)
        if on_done:
            fut.add_done_callback(on_done)


def main(args=None):
    rclpy.init(args=args)
    node = MissionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
