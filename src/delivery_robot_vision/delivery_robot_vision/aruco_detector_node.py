import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String, Int32
from cv_bridge import CvBridge
import cv2

MARKER_MAP = {
    0: 'aisle1',
    1: 'aisle2',
    2: 'dock',
}

class ArucoDetectorNode(Node):
    def __init__(self):
        super().__init__('aruco_detector_node')

        self.bridge = CvBridge()
        self.sub = self.create_subscription(Image, 'camera/image_raw', self.image_cb, 10)
        self.name_pub = self.create_publisher(String, '/marker_detected', 10)
        self.id_pub = self.create_publisher(Int32, '/marker_id_detected', 10)

        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

        if hasattr(cv2.aruco, 'DetectorParameters'):
            self.aruco_params = cv2.aruco.DetectorParameters()
        else:
            self.aruco_params = cv2.aruco.DetectorParameters_create()

        self.use_new_api = hasattr(cv2.aruco, 'ArucoDetector')
        if self.use_new_api:
            self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)
        else:
            self.detector = None

        self.last_marker = None
        self.stable_count = 0
        self.required_stable_frames = 3

    def image_cb(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            if self.use_new_api:
                corners, ids, _ = self.detector.detectMarkers(gray)
            else:
                corners, ids, _ = cv2.aruco.detectMarkers(
                    gray, self.aruco_dict, parameters=self.aruco_params
                )

            if ids is None or len(ids) == 0:
                self.last_marker = None
                self.stable_count = 0
                return

            marker_id = int(ids[0][0])

            if marker_id == self.last_marker:
                self.stable_count += 1
            else:
                self.last_marker = marker_id
                self.stable_count = 1

            if self.stable_count >= self.required_stable_frames:
                name = MARKER_MAP.get(marker_id, f'unknown_{marker_id}')

                id_msg = Int32()
                id_msg.data = marker_id
                self.id_pub.publish(id_msg)

                name_msg = String()
                name_msg.data = name
                self.name_pub.publish(name_msg)

                self.get_logger().info(f'Stable marker detected: {name} (id={marker_id})')
                self.stable_count = 0

        except Exception as e:
            self.get_logger().warn(f'ArUco detection failed: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = ArucoDetectorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()