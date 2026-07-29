import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger
from std_msgs.msg import String, Bool
from geometry_msgs.msg import Twist


class DashboardNode(Node):
    """Single shared rclpy node used by all three dashboard windows."""

    def __init__(self):
        super().__init__('delivery_dashboard_node')

        self.start_client = self.create_client(Trigger, 'start_delivery')
        self.cancel_client = self.create_client(Trigger, 'cancel_delivery')
        self.home_client = self.create_client(Trigger, 'return_home')
        self.record_client = self.create_client(Trigger, 'record_waypoint')

        self.request_points_pub = self.create_publisher(String, 'request_delivery_points', 10)
        self.waypoint_name_pub = self.create_publisher(String, 'waypoint_name_to_record', 10)
        self.mode_lock_pub = self.create_publisher(Bool, 'manual_override_lock', 10)
        self.cmd_vel_manual_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.status_text = 'Waiting for status...' 
        self.create_subscription(String, 'mission_status', self._on_status, 10)

    def _on_status(self, msg: String):
        self.status_text = msg.data

    # ---- convenience call wrappers (fire-and-forget style for GUI responsiveness) ----

    def call_trigger(self, client):
        if not client.service_is_ready():
            return False, 'Service not available'
        req = Trigger.Request()
        future = client.call_async(req)
        rclpy.spin_until_future_complete(self, future, timeout_sec=2.0)
        if future.result() is None:
            return False, 'No response'
        return future.result().success, future.result().message

    def start_delivery(self):
        return self.call_trigger(self.start_client)

    def cancel_delivery(self):
        return self.call_trigger(self.cancel_client)

    def return_home(self):
        return self.call_trigger(self.home_client)

    def record_waypoint(self, name: str):
        msg = String()
        msg.data = name
        self.waypoint_name_pub.publish(msg)
        return self.call_trigger(self.record_client)

    def request_points(self, names):
        msg = String()
        msg.data = ','.join(names)
        self.request_points_pub.publish(msg)

    def set_manual_mode(self, enabled: bool):
        msg = Bool()
        msg.data = enabled
        self.mode_lock_pub.publish(msg)

    def send_manual_twist(self, linear_x: float, angular_z: float):
        msg = Twist()
        msg.linear.x = float(linear_x)
        msg.linear.y = 0.0
        msg.linear.z = 0.0
        msg.angular.x = 0.0
        msg.angular.y = 0.0
        msg.angular.z = float(angular_z)
        self.cmd_vel_manual_pub.publish(msg)
