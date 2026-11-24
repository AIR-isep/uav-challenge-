"""Nœud ROS 2 : image caméra -> isep_interfaces/Target (cible rouge)."""
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image

from isep_interfaces.msg import Target
from isep_perception.detector import detect_red


class TargetDetector(Node):
    def __init__(self):
        super().__init__("target_detector")
        self.declare_parameter("image_topic", "/isep_vtol/camera/image")
        self.declare_parameter("min_area_ratio", 2e-4)
        self.bridge = CvBridge()
        self.pub = self.create_publisher(Target, "/isep/target", 10)
        self.create_subscription(Image, self.get_parameter("image_topic").value, self._on_image, qos_profile_sensor_data)

    def _on_image(self, msg):
        bgr = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        d = detect_red(bgr, self.get_parameter("min_area_ratio").value)
        out = Target(header=msg.header, detected=d.detected, confidence=d.confidence,
                     u=d.u, v=d.v, area_ratio=d.area_ratio)
        self.pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = TargetDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
