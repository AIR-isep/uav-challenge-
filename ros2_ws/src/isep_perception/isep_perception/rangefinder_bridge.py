"""Nœud ROS 2 : télémètre vertical -> MAVROS -> ArduPilot (RNGFND1_TYPE = 10, MAVLink).

En simulation, la source est le rayon unique « rangefinder_down » de Gazebo
(sensor_msgs/LaserScan). Sur le vrai drone, le pilote du radar publiera un
sensor_msgs/Range sur le même topic de sortie : ce nœud ne servira plus.
"""
import math

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan, Range


def scan_to_range(scan: LaserScan) -> Range:
    r = Range()
    r.header = scan.header
    r.radiation_type = Range.INFRARED
    r.field_of_view = 0.05
    r.min_range = scan.range_min
    r.max_range = scan.range_max
    value = scan.ranges[0] if scan.ranges else math.inf
    # Hors portée : on signale max_range + 1, qu'ArduPilot ignore
    r.range = value if math.isfinite(value) and scan.range_min <= value <= scan.range_max else scan.range_max + 1.0
    return r


class RangefinderBridge(Node):
    def __init__(self):
        super().__init__("rangefinder_bridge")
        self.declare_parameter("input_topic", "/isep_vtol/rangefinder")
        self.declare_parameter("output_topic", "/mavros/distance_sensor/rangefinder_sub")
        self.pub = self.create_publisher(Range, self.get_parameter("output_topic").value, 10)
        self.create_subscription(LaserScan, self.get_parameter("input_topic").value,
                                 lambda m: self.pub.publish(scan_to_range(m)), qos_profile_sensor_data)


def main(args=None):
    rclpy.init(args=args)
    node = RangefinderBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
