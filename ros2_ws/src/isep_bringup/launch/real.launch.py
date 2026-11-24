"""Vol réel, sur le Raspberry Pi 5 : MAVROS sur le port série de la carte de vol + nœuds ISEP.

  ros2 launch isep_bringup real.launch.py
  ros2 launch isep_bringup real.launch.py fcu_url:=/dev/ttyAMA0:921600 mission:=true

Côté ArduPilot : le port série relié au Pi doit avoir SERIALn_PROTOCOL = 2 (MAVLink2)
et SERIALn_BAUD = 921.
"""
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    bringup = Path(get_package_share_directory("isep_bringup"))
    default_mission = str(bringup / "ardupilot" / "missions" / "01_trajectoire_A.waypoints")
    return LaunchDescription([
        DeclareLaunchArgument("fcu_url", default_value="/dev/ttyAMA0:921600"),
        DeclareLaunchArgument("gcs_url", default_value="udp-b://@:14550",
                              description="diffusion de la télémétrie sur le Wi-Fi de bord"),
        DeclareLaunchArgument("image_topic", default_value="/camera/image_raw"),
        DeclareLaunchArgument("mission", default_value="false"),
        DeclareLaunchArgument("mission_file", default_value=default_mission),
        IncludeLaunchDescription(
            AnyLaunchDescriptionSource(str(Path(get_package_share_directory("mavros")) / "launch" / "apm.launch")),
            launch_arguments={"fcu_url": LaunchConfiguration("fcu_url"), "gcs_url": LaunchConfiguration("gcs_url"),
                              "tgt_system": "1", "tgt_component": "1"}.items()),
        Node(package="isep_perception", executable="target_detector", output="screen",
             parameters=[{"image_topic": LaunchConfiguration("image_topic")}]),
        Node(package="isep_mission", executable="mission_node", output="screen",
             parameters=[{"mission_file": LaunchConfiguration("mission_file")}],
             condition=IfCondition(LaunchConfiguration("mission"))),
    ])
