"""S-Graphs launch for RA-L frontend-only wall-plane comparison.

This launch mirrors the official S-Graphs launch structure but exposes the
optimization timer as an explicit argument. For Step 7A we keep external
odometry and disable the periodic graph optimization timer so the recorded
planes are closer to frontend/map-update outputs than backend-optimized map
products.
"""

import os

from ament_index_python import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument("lidar_topic", default_value="/velodyne/points"),
            DeclareLaunchArgument("odom_topic", default_value="/odometry"),
            DeclareLaunchArgument("imu_topic", default_value="imu/data"),
            DeclareLaunchArgument("base_frame", default_value="body"),
            DeclareLaunchArgument("odom_frame", default_value="odom"),
            DeclareLaunchArgument("map_frame", default_value="map"),
            DeclareLaunchArgument("compute_odom", default_value="false"),
            DeclareLaunchArgument("namespace", default_value=""),
            DeclareLaunchArgument("room_segmentation", default_value="old"),
            DeclareLaunchArgument("keyframe_delta", default_value="2.0"),
            DeclareLaunchArgument("viz_dense_map", default_value="false"),
            DeclareLaunchArgument("debug_mode", default_value="false"),
            DeclareLaunchArgument(
                "enable_optimization_timer",
                default_value="false",
                description="Disable periodic graph optimization for frontend comparison.",
            ),
            OpaqueFunction(function=launch_sgraphs),
        ]
    )


def launch_reasoning():
    reasoning_dir = get_package_share_directory("situational_graphs_reasoning")
    reasoning_launch_file = os.path.join(
        reasoning_dir, "launch", "situational_graphs_reasoning.launch.py"
    )
    return IncludeLaunchDescription(PythonLaunchDescriptionSource(reasoning_launch_file))


def launch_sgraphs(context, *args, **kwargs):
    pkg_dir = get_package_share_directory("lidar_situational_graphs")
    prefiltering_param_file = os.path.join(pkg_dir, "config", "prefiltering.yaml")
    scan_matching_param_file = os.path.join(pkg_dir, "config", "scan_matching.yaml")
    s_graphs_param_file = os.path.join(pkg_dir, "config", "s_graphs.yaml")

    lidar_topic_arg = LaunchConfiguration("lidar_topic").perform(context)
    odom_topic_arg = LaunchConfiguration("odom_topic").perform(context)
    imu_topic_arg = LaunchConfiguration("imu_topic").perform(context)
    base_frame_arg = LaunchConfiguration("base_frame").perform(context)
    odom_frame_arg = LaunchConfiguration("odom_frame").perform(context)
    map_frame_arg = LaunchConfiguration("map_frame").perform(context)
    compute_odom_arg = LaunchConfiguration("compute_odom").perform(context)
    namespace_arg = LaunchConfiguration("namespace").perform(context)
    room_segmentation_arg = LaunchConfiguration("room_segmentation").perform(context)
    keyframe_delta_arg = float(LaunchConfiguration("keyframe_delta").perform(context))
    viz_dense_map_arg = LaunchConfiguration("viz_dense_map").perform(context)
    debug_mode_arg = LaunchConfiguration("debug_mode").perform(context)
    enable_optimization_timer_arg = (
        LaunchConfiguration("enable_optimization_timer").perform(context).lower()
        in ("1", "true", "yes", "on")
    )

    prefiltering_cmd = Node(
        package="lidar_situational_graphs",
        executable="s_graphs_prefiltering_node",
        namespace=namespace_arg,
        parameters=[prefiltering_param_file, {"base_link_frame": base_frame_arg}],
        output="screen",
        remappings=[
            ("velodyne_points", lidar_topic_arg),
            ("imu/data", imu_topic_arg),
        ],
        prefix=["bash -c 'exec 2>/dev/null; $0 $@'"],
    )

    scan_matching_cmd = Node(
        package="lidar_situational_graphs",
        executable="s_graphs_scan_matching_odometry_node",
        namespace=namespace_arg,
        parameters=[scan_matching_param_file],
        remappings=[("odom", odom_topic_arg)],
        output="screen",
        condition=IfCondition(compute_odom_arg),
    )

    if room_segmentation_arg == "old":
        room_segmentation_cmd = Node(
            package="lidar_situational_graphs",
            executable="s_graphs_room_segmentation_node",
            namespace=namespace_arg,
            parameters=[{"vertex_neigh_thres": 2}],
            output="screen",
        )
    else:
        room_segmentation_cmd = launch_reasoning()

    floor_plan_cmd = Node(
        package="lidar_situational_graphs",
        executable="s_graphs_floor_plan_node",
        namespace=namespace_arg,
        parameters=[
            {
                "vertex_neigh_thres": 2,
                "keyframe_delta_trans": keyframe_delta_arg,
            }
        ],
        output="screen",
    )

    s_graphs_cmd = Node(
        package="lidar_situational_graphs",
        executable="s_graphs_node",
        namespace=namespace_arg,
        parameters=[
            s_graphs_param_file,
            {
                "odom_frame_id": odom_frame_arg,
                "map_frame_id": map_frame_arg,
                "keyframe_delta_trans": keyframe_delta_arg,
                "keyframe_delta_angle": keyframe_delta_arg,
                "viz_dense_map": viz_dense_map_arg,
                "enable_optimization_timer": enable_optimization_timer_arg,
            },
        ],
        output={"stdout": "screen", "stderr": "screen"},
        prefix=["gdbserver localhost:3000"] if debug_mode_arg == "true" else None,
        remappings=[("odom", odom_topic_arg)],
    )

    return [
        prefiltering_cmd,
        scan_matching_cmd,
        room_segmentation_cmd,
        floor_plan_cmd,
        s_graphs_cmd,
    ]
