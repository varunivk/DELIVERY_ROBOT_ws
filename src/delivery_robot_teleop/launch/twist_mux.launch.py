from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pkg = get_package_share_directory('delivery_robot_teleop')
    config = os.path.join(pkg, 'config', 'twist_mux.yaml')

    twist_mux_node = Node(
        package='twist_mux',
        executable='twist_mux',
        name='twist_mux',
        output='screen',
        parameters=[config],
        remappings=[('cmd_vel_out', 'cmd_vel')]
    )

    return LaunchDescription([twist_mux_node])