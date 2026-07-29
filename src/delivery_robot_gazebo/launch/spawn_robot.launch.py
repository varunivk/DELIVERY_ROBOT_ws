import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    gz_pkg = get_package_share_directory('delivery_robot_gazebo')
    desc_pkg = get_package_share_directory('delivery_robot_description')

    world_path = os.path.join(gz_pkg, 'worlds', 'warehouse.sdf')
    xacro_file = os.path.join(desc_pkg, 'urdf', 'robot.urdf.xacro')

    robot_description = ParameterValue(
        Command(['xacro ', xacro_file]),
        value_type=str
    )

    gz_sim = ExecuteProcess(
        cmd=['gz', 'sim', '-r', world_path],
        output='screen'
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description}],
        output='screen'
    )

    spawn = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'delivery_robot',
            '-topic', 'robot_description',
            '-x', '-4.5',
            '-y', '0',
            '-z', '0.1'
        ],
        output='screen'
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry@gz.msgs.Odometry',
            '/tf@tf2_msgs/msg/TFMessage@gz.msgs.Pose_V',
            '/camera/image_raw@sensor_msgs/msg/Image@gz.msgs.Image',
        ],
        output='screen'
    )

    return LaunchDescription([
        gz_sim,
        robot_state_publisher,
        spawn,
        bridge
    ])
