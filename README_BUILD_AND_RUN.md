# Delivery Robot Warehouse Sim - Build & Run Instructions

## 1. Copy into your workspace
Extract this zip so the `src/` contents land in `~/delivery_robot_ws/src/`
(merge with the already-scaffolded folders from setup_all_packages.sh).

## 2. Install dependencies
sudo apt update
sudo apt install -y ros-jazzy-navigation2 ros-jazzy-nav2-bringup ros-jazzy-twist-mux \
  ros-jazzy-ros-gz ros-jazzy-teleop-twist-keyboard ros-jazzy-xacro \
  ros-jazzy-robot-state-publisher ros-jazzy-joint-state-publisher \
  ros-jazzy-topic-tools ros-jazzy-cv-bridge python3-opencv python3-pyqt5 \
  python3-colcon-common-extensions

## 3. Build
cd ~/delivery_robot_ws
colcon build --symlink-install
source install/setup.bash

## 4. Test in stages (recommended order)

### Stage A - URDF check (no Gazebo)
ros2 launch delivery_robot_description display.launch.py
# Confirm robot model + wheels + sensors show in RViz (add RobotModel display, fixed frame = base_link)

### Stage B - Spawn in warehouse
ros2 launch delivery_robot_gazebo spawn_robot.launch.py
# Confirm Gazebo opens with robot in warehouse, shelves visible, obstacle box present

### Stage C - Manual drive test
ros2 topic pub /cmd_vel_manual geometry_msgs/msg/Twist "{linear: {x: 0.2}}" --once
ros2 topic pub /manual_override_lock std_msgs/msg/Bool "{data: true}" --once
# Robot should move forward when lock=true; ignored when lock=false

### Stage D - Nav2 + twist_mux
ros2 launch delivery_robot_nav2 nav2_bringup.launch.py
ros2 launch delivery_robot_teleop twist_mux.launch.py
ros2 topic pub /manual_override_lock std_msgs/msg/Bool "{data: false}" --once
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  "{pose: {header: {frame_id: map}, pose: {position: {x: 1.5, y: -2.3}}}}"
# Robot should autonomously navigate, avoiding obstacle_box via ultrasonic RangeSensorLayer

### Stage E - ArUco detection
ros2 run delivery_robot_vision aruco_detector_node
ros2 topic echo /marker_detected
# Drive/navigate robot near a marker plane, confirm topic publishes aisle1/aisle2/dock

### Stage F - Delivery manager
ros2 run delivery_robot_manager delivery_manager
ros2 topic pub /request_delivery_points std_msgs/msg/String "{data: 'aisle1,dock'}" --once
ros2 service call /start_delivery std_srvs/srv/Trigger
ros2 topic echo /mission_status

### Stage G - Dashboard
ros2 run delivery_robot_dashboard dashboard
# Two windows should open: Mission Control + Manual Drive Console
# Use "Select Package" popup, Start Delivery, toggle Manual/Autonomous, arrow buttons

## 5. Full one-command demo launch
ros2 launch delivery_robot_bringup full_sim.launch.py

## Known simplifications (mention in report)
- No LiDAR/AMCL/map server - static identity map->odom TF used, odom treated as ground truth in sim
- No EKF sensor fusion - future work
- Custom lightweight warehouse SDF (primitives only, no meshes) instead of AWS warehouse assets
- Delivery confirmed by goal-reached + ArUco marker detection (marker IDs 0/1/2 = aisle1/aisle2/dock)
- Nearest-neighbor task ordering for simultaneous delivery requests (waypoints_store.reorder_by_distance)
- Marker aruco_dict = DICT_4X4_50; ensure Gazebo marker plane textures actually use matching tag images
  (replace the plain white plane material in warehouse.sdf with an actual ArUco tag texture/material
  before the vision demo - this is the one piece NOT auto-generated and needs a texture file dropped in)
