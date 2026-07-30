from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pkg_share = get_package_share_directory('delivery_robot_manager')
    routes_file = os.path.join(pkg_share, 'config', 'routes.yaml')

    return LaunchDescription([
        Node(
            package='delivery_robot_manager',
            executable='route_executor',
            name='route_executor',
            output='screen',
            parameters=[{
                'routes_file': routes_file,
                'route_name': 'delivery_loop'
            }]
        )
    ])