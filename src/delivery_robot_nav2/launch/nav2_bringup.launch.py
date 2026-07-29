import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg = get_package_share_directory('delivery_robot_nav2')
    params_file = os.path.join(pkg, 'config', 'nav2_params.yaml')
    lifecycle_nodes = ['controller_server', 'planner_server', 'behavior_server', 'bt_navigator']

    # Static identity TF: map -> odom (no lidar/AMCL localization in this build)
    static_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom'],
        output='screen'
    )

    controller_server = Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        output='screen',
        parameters=[params_file, {'use_sim_time': True}],
        # Remap Nav2's velocity output to cmd_vel_nav so twist_mux (not Nav2) controls the real /cmd_vel
        remappings=[('cmd_vel', 'cmd_vel_nav')]
    )

    planner_server = Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        output='screen',
        parameters=[params_file, {'use_sim_time': True}]
    )

    behavior_server = Node(
        package='nav2_behaviors',
        executable='behavior_server',
        name='behavior_server',
        output='screen',
        parameters=[params_file, {'use_sim_time': True}]
    )

    bt_navigator = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        output='screen',
        parameters=[params_file, {'use_sim_time': True}]
    )

    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'autostart': True,
            'node_names': lifecycle_nodes
        }]
    )

    return LaunchDescription([
        static_tf, controller_server, planner_server,
        behavior_server, bt_navigator, lifecycle_manager
    ])
