from setuptools import setup

package_name = 'delivery_robot_vision'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='student',
    maintainer_email='you@example.com',
    description='ArUco marker detection node',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'aruco_detector_node = delivery_robot_vision.aruco_detector_node:main',
        ],
    },
)
