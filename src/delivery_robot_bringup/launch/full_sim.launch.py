import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    gazebo_pkg = get_package_share_directory('delivery_robot_gazebo')
    nav2_pkg = get_package_share_directory('delivery_robot_nav2')
    teleop_pkg = get_package_share_directory('delivery_robot_teleop')

    spawn_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_pkg, 'launch', 'spawn_robot.launch.py')
        )
    )

    # Delay Nav2 + twist_mux slightly so Gazebo/robot spawn finishes first
    nav2_launch = TimerAction(
        period=5.0,
        actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav2_pkg, 'launch', 'nav2_bringup.launch.py')
            )
        )]
    )

    twist_mux_launch = TimerAction(
        period=5.0,
        actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(teleop_pkg, 'launch', 'twist_mux.launch.py')
            )
        )]
    )

    aruco_node = TimerAction(
        period=3.0,
        actions=[Node(
            package='delivery_robot_vision',
            executable='aruco_detector_node',
            output='screen'
        )]
    )

    delivery_manager_node = TimerAction(
        period=6.0,
        actions=[Node(
            package='delivery_robot_manager',
            executable='delivery_manager',
            output='screen'
        )]
    )

    dashboard_node = TimerAction(
        period=7.0,
        actions=[Node(
            package='delivery_robot_dashboard',
            executable='dashboard',
            output='screen'
        )]
    )

    return LaunchDescription([
        spawn_launch,
        nav2_launch,
        twist_mux_launch,
        aruco_node,
        delivery_manager_node,
        dashboard_node,
    ])
