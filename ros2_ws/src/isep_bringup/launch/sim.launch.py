"""Simulation complète : Gazebo (isep_vtol) + ArduPlane SITL + MAVROS + nœuds ISEP.

  ros2 launch isep_bringup sim.launch.py
  ros2 launch isep_bringup sim.launch.py gcs_ip:=192.168.1.42   # télémétrie vers le portable
  ros2 launch isep_bringup sim.launch.py gui:=false mission:=true

Liaisons :
  SITL SERIAL0 tcp:5760 -> MAVROS (qui relaie vers la station sol si gcs_ip est donné)
  SITL SERIAL1 tcp:5762 -> libre pour MAVProxy : mavproxy.py --master tcp:127.0.0.1:5762
"""
import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (AppendEnvironmentVariable, DeclareLaunchArgument, ExecuteProcess,
                            IncludeLaunchDescription, OpaqueFunction, TimerAction)
from launch.launch_description_sources import AnyLaunchDescriptionSource, PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

HOME = (-35.363262, 149.165237, 584.0, 0.0)   # identique au monde isep_runway


def _truthy(v: str) -> bool:
    return v.lower() in ("1", "true", "yes", "on")


def setup(context):
    lc = {k: LaunchConfiguration(k).perform(context) for k in (
        "gui", "gcs_ip", "mission", "perception", "wipe", "ardupilot_home", "ardupilot_gazebo", "mission_file")}
    bringup = Path(get_package_share_directory("isep_bringup"))
    desc = Path(get_package_share_directory("isep_description"))
    ap_home = Path(os.path.expanduser(lc["ardupilot_home"]))
    ap_gz = Path(os.path.expanduser(lc["ardupilot_gazebo"]))
    params = bringup / "ardupilot" / "params"
    perception = _truthy(lc["perception"])

    actions = [
        AppendEnvironmentVariable("GZ_SIM_RESOURCE_PATH", str(ap_gz / "models")),
        AppendEnvironmentVariable("GZ_SIM_RESOURCE_PATH", str(ap_gz / "worlds")),
        AppendEnvironmentVariable("GZ_SIM_SYSTEM_PLUGIN_PATH", str(ap_gz / "build")),
    ]

    # --- Gazebo ---
    gz_args = f"-r -v3 {desc / 'worlds' / 'isep_runway.sdf'}"
    if not _truthy(lc["gui"]):
        gz_args = "-s " + gz_args
    actions.append(IncludeLaunchDescription(
        PythonLaunchDescriptionSource(str(Path(get_package_share_directory("ros_gz_sim")) / "launch" / "gz_sim.launch.py")),
        launch_arguments={"gz_args": gz_args, "on_exit_shutdown": "true"}.items()))

    # --- ArduPlane SITL (modèle JSON = physique Gazebo) ---
    defaults = [ap_home / "Tools/autotest/default_params/quadplane.parm",
                params / "isep_vtol_gz.param",
                params / "generated" / "isep_vtol_servos.param",
                params / "common.param"]
    if perception:
        defaults.append(params / "rangefinder_mavlink.param")
    workdir = Path.home() / ".ros" / "isep_sitl"
    workdir.mkdir(parents=True, exist_ok=True)
    cmd = [str(ap_home / "build/sitl/bin/arduplane"), "--model", "JSON", "--speedup", "1", "--slave", "0",
           "--defaults", ",".join(str(d) for d in defaults), "--sim-address=127.0.0.1", "-I0",
           "--home", ",".join(str(v) for v in HOME)]
    if _truthy(lc["wipe"]):
        cmd.append("-w")
    actions.append(TimerAction(period=3.0, actions=[
        ExecuteProcess(cmd=cmd, cwd=str(workdir), output="screen", name="arduplane_sitl")]))

    # --- MAVROS ---
    gcs_url = f"udp://@{lc['gcs_ip']}:14550" if lc["gcs_ip"] else ""
    actions.append(TimerAction(period=5.0, actions=[IncludeLaunchDescription(
        AnyLaunchDescriptionSource(str(Path(get_package_share_directory("mavros")) / "launch" / "apm.launch")),
        launch_arguments={"fcu_url": "tcp://127.0.0.1:5760", "gcs_url": gcs_url,
                          "tgt_system": "1", "tgt_component": "1"}.items())]))

    # --- Pont Gazebo -> ROS 2 ---
    actions.append(Node(package="ros_gz_bridge", executable="parameter_bridge", name="gz_bridge",
                        parameters=[{"config_file": str(bringup / "config" / "gz_bridge.yaml")}],
                        output="screen"))

    sim_time = {"use_sim_time": True}
    if perception:
        actions += [
            Node(package="isep_perception", executable="rangefinder_bridge", parameters=[sim_time], output="screen"),
            Node(package="isep_perception", executable="target_detector", parameters=[sim_time], output="screen"),
        ]
    if _truthy(lc["mission"]):
        mission_file = lc["mission_file"] or str(bringup / "ardupilot" / "missions" / "01_trajectoire_A.waypoints")
        actions.append(Node(package="isep_mission", executable="mission_node", output="screen",
                            parameters=[sim_time, {"mission_file": mission_file}]))
    return actions


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("gui", default_value="true", description="fenêtre Gazebo"),
        DeclareLaunchArgument("gcs_ip", default_value="", description="IP de la station sol (portable)"),
        DeclareLaunchArgument("mission", default_value="false", description="lancer isep_mission"),
        DeclareLaunchArgument("mission_file", default_value="", description="fichier .waypoints"),
        DeclareLaunchArgument("perception", default_value="true", description="détecteur + télémètre"),
        DeclareLaunchArgument("wipe", default_value="true", description="repartir des fichiers .param"),
        DeclareLaunchArgument("ardupilot_home", default_value=os.environ.get("ARDUPILOT_HOME", "~/ardupilot")),
        DeclareLaunchArgument("ardupilot_gazebo", default_value=os.environ.get("ARDUPILOT_GAZEBO", "~/ardupilot_gazebo")),
        OpaqueFunction(function=setup),
    ])
