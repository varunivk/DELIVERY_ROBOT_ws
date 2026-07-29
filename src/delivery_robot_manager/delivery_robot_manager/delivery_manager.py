import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
from std_srvs.srv import Trigger
from std_msgs.msg import String
import threading
import time

from delivery_robot_manager.waypoints_store import WaypointsStore


class DeliveryManager(Node):
    def __init__(self):
        super().__init__('delivery_manager')
        self.cb_group = ReentrantCallbackGroup()

        self.store = WaypointsStore()
        self.current_x = -4.5
        self.current_y = 0.0
        self.mission_active = False
        self.cancelled = False
        self.last_marker = None
        self.expected_marker = None
        self.marker_received = threading.Event()

        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose',
                                        callback_group=self.cb_group)

        # Services (dashboard-triggered, per contract)
        self.create_service(Trigger, 'start_delivery', self.on_start_delivery,
                             callback_group=self.cb_group)
        self.create_service(Trigger, 'cancel_delivery', self.on_cancel_delivery,
                             callback_group=self.cb_group)
        self.create_service(Trigger, 'return_home', self.on_return_home,
                             callback_group=self.cb_group)
        self.create_service(Trigger, 'record_waypoint', self.on_record_waypoint,
                             callback_group=self.cb_group)

        # Topics
        self.create_subscription(String, 'request_delivery_points', self.on_request_points, 10)
        self.create_subscription(String, 'waypoint_name_to_record', self.on_waypoint_name, 10)
        self.create_subscription(String, 'marker_detected', self.on_marker_detected, 10)
        self.create_subscription(PoseStamped, '/current_pose_estimate', self.on_pose_update, 10)

        self.status_pub = self.create_publisher(String, 'mission_status', 10)

        self._pending_waypoint_name = None

        self.publish_status('Delivery manager ready. Waiting for dashboard commands.')

    # ---------- helpers ----------

    def publish_status(self, text: str):
        msg = String()
        msg.data = text
        self.status_pub.publish(msg)
        self.get_logger().info(text)

    def on_pose_update(self, msg: PoseStamped):
        self.current_x = msg.pose.position.x
        self.current_y = msg.pose.position.y

    def on_request_points(self, msg: String):
        # Comma-separated list e.g. "aisle1,dock"
        names = [n.strip() for n in msg.data.split(',') if n.strip()]
        added = self.store.request_delivery(names)
        self.store.reorder_by_distance(self.current_x, self.current_y)
        self.publish_status(f'Queued: {added}. Order (nearest-first): {self.store.pending_queue}')

    def on_waypoint_name(self, msg: String):
        self._pending_waypoint_name = msg.data.strip()

    def on_marker_detected(self, msg: String):
        self.last_marker = msg.data
        if self.expected_marker and msg.data == self.expected_marker:
            self.marker_received.set()

    # ---------- services ----------

    def on_record_waypoint(self, request, response):
        name = self._pending_waypoint_name
        if not name:
            response.success = False
            response.message = 'No waypoint name set. Publish to waypoint_name_to_record first.'
            return response
        self.store.record_waypoint(name, self.current_x, self.current_y)
        response.success = True
        response.message = f'Recorded waypoint "{name}" at ({self.current_x:.2f}, {self.current_y:.2f})'
        self.publish_status(response.message)
        self._pending_waypoint_name = None
        return response

    def on_start_delivery(self, request, response):
        if self.mission_active:
            response.success = False
            response.message = 'Mission already active.'
            return response
        if not self.store.pending_queue:
            response.success = False
            response.message = 'No delivery points queued. Use dashboard to select points first.'
            return response

        self.cancelled = False
        self.mission_active = True
        threading.Thread(target=self.run_mission, daemon=True).start()
        response.success = True
        response.message = f'Delivery mission started. Queue: {self.store.pending_queue}'
        return response

    def on_cancel_delivery(self, request, response):
        self.cancelled = True
        self.store.clear_queue()
        response.success = True
        response.message = 'Delivery cancelled, queue cleared.'
        self.publish_status(response.message)
        return response

    def on_return_home(self, request, response):
        self.store.pending_queue.insert(0, 'home')
        if not self.mission_active:
            self.cancelled = False
            self.mission_active = True
            threading.Thread(target=self.run_mission, daemon=True).start()
        response.success = True
        response.message = 'Returning home.'
        self.publish_status(response.message)
        return response

    # ---------- mission loop ----------

    def run_mission(self):
        while self.store.pending_queue and not self.cancelled:
            self.store.reorder_by_distance(self.current_x, self.current_y)
            target_name = self.store.pop_next()
            pose = self.store.get_pose(target_name)
            if pose is None:
                continue

            self.publish_status(f'Navigating to {target_name} at {pose}')
            success = self.send_nav_goal(pose[0], pose[1])

            if not success:
                self.publish_status(f'Navigation to {target_name} failed or was interrupted.')
                continue

            if target_name in ('aisle1', 'aisle2', 'dock'):
                self.expected_marker = target_name
                self.marker_received.clear()
                self.publish_status(f'Arrived at {target_name}. Waiting for marker confirmation...')
                got_marker = self.marker_received.wait(timeout=8.0)
                if got_marker:
                    self.store.mark_delivered(target_name)
                    self.publish_status(f'DELIVERED: {target_name} confirmed by marker detection.')
                else:
                    self.publish_status(f'WARNING: reached {target_name} but marker not confirmed (timeout).')
                self.expected_marker = None
            else:
                self.publish_status(f'Arrived at {target_name}.')

        self.mission_active = False
        if self.cancelled:
            self.publish_status('Mission cancelled.')
        else:
            self.publish_status('All queued deliveries complete. Idle.')

    def send_nav_goal(self, x: float, y: float) -> bool:
        if not self.nav_client.wait_for_server(timeout_sec=5.0):
            self.publish_status('Nav2 action server not available.')
            return False

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.orientation.w = 1.0

        send_future = self.nav_client.send_goal_async(goal_msg)
        rclpy.spin_until_future_complete(self, send_future, timeout_sec=5.0)
        goal_handle = send_future.result()
        if goal_handle is None or not goal_handle.accepted:
            return False

        result_future = goal_handle.get_result_async()
        while not result_future.done() and not self.cancelled:
            time.sleep(0.2)

        if self.cancelled:
            goal_handle.cancel_goal_async()
            return False

        result = result_future.result()
        self.current_x, self.current_y = x, y
        return result is not None


def main(args=None):
    rclpy.init(args=args)
    node = DeliveryManager()
    from rclpy.executors import MultiThreadedExecutor
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
