from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg = get_package_share_directory('delivery_robot_description')
    xacro_file = os.path.join(pkg, 'urdf', 'robot.urdf.xacro')
    robot_description = Command(['xacro ', xacro_file])

    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description}],
            output='screen'
        ),
        Node(
            package='joint_state_publisher',
            executable='joint_state_publisher',
            output='screen'
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            output='screen'
        ),
    ])
