#!/usr/bin/env python3

import yaml
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped, Quaternion
from nav2_msgs.action import FollowWaypoints
from tf_transformations import quaternion_from_euler


class RouteExecutor(Node):
    def __init__(self):
        super().__init__('route_executor')

        self.declare_parameter('routes_file', '')
        self.declare_parameter('route_name', 'delivery_loop')

        routes_file = self.get_parameter('routes_file').value
        self.route_name = self.get_parameter('route_name').value

        with open(routes_file, 'r') as f:
            self.data = yaml.safe_load(f)

        self.locations = self.data['locations']
        self.routes = self.data['routes']

        self.client = ActionClient(self, FollowWaypoints, '/follow_waypoints')
        self.get_logger().info('Waiting for /follow_waypoints action server...')
        self.client.wait_for_server()
        self.get_logger().info('Connected to /follow_waypoints')

        self.timer = self.create_timer(2.0, self.start_route)
        self.started = False

    def yaw_to_quaternion(self, yaw):
        q = quaternion_from_euler(0.0, 0.0, yaw)
        quat = Quaternion()
        quat.x = q[0]
        quat.y = q[1]
        quat.z = q[2]
        quat.w = q[3]
        return quat

    def make_pose(self, location_name):
        loc = self.locations[location_name]
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = float(loc['x'])
        pose.pose.position.y = float(loc['y'])
        pose.pose.position.z = 0.0
        pose.pose.orientation = self.yaw_to_quaternion(float(loc['yaw']))
        return pose

    def start_route(self):
        if self.started:
            return
        self.started = True
        self.timer.cancel()

        if self.route_name not in self.routes:
            self.get_logger().error(f'Route {self.route_name} not found')
            return

        waypoint_names = self.routes[self.route_name]
        poses = [self.make_pose(name) for name in waypoint_names]

        goal = FollowWaypoints.Goal()
        goal.poses = poses

        self.get_logger().info(f'Sending route: {self.route_name} -> {waypoint_names}')
        future = self.client.send_goal_async(goal, feedback_callback=self.feedback_cb)
        future.add_done_callback(self.goal_response_cb)

    def goal_response_cb(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Route goal rejected')
            return
        self.get_logger().info('Route goal accepted')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.result_cb)

    def feedback_cb(self, feedback_msg):
        self.get_logger().info(
            f'Current waypoint index: {feedback_msg.feedback.current_waypoint}'
        )

    def result_cb(self, future):
        result = future.result().result
        self.get_logger().info(f'Route finished. Missed waypoints: {list(result.missed_waypoints)}')


def main(args=None):
    rclpy.init(args=args)
    node = RouteExecutor()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()