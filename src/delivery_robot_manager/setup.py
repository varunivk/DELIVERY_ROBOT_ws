from setuptools import setup

package_name = 'delivery_robot_manager'

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
    description='Delivery task manager',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'delivery_manager = delivery_robot_manager.delivery_manager:main',
        ],
    },
)
