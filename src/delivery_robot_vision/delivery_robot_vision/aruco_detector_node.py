import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
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
        self.pub = self.create_publisher(String, '/marker_detected', 10)

        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

        if hasattr(cv2.aruco, 'DetectorParameters'):
            self.aruco_params = cv2.aruco.DetectorParameters()
        else:
            self.aruco_params = cv2.aruco.DetectorParameters_create()

        self.use_new_api = hasattr(cv2.aruco, 'ArucoDetector')
        if self.use_new_api:
            self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)
            self.get_logger().info(f'Using new OpenCV ArUco API: {cv2.__version__}')
        else:
            self.detector = None
            self.get_logger().info(f'Using old OpenCV ArUco API: {cv2.__version__}')

        self.last_published = None
        self.get_logger().info('ArUco detector node started, watching camera/image_raw')

    def image_cb(self, msg: Image):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().warn(f'cv_bridge conversion failed: {e}')
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        try:
            if self.use_new_api:
                corners, ids, _ = self.detector.detectMarkers(gray)
            else:
                corners, ids, _ = cv2.aruco.detectMarkers(
                    gray,
                    self.aruco_dict,
                    parameters=self.aruco_params
                )
        except Exception as e:
            self.get_logger().warn(f'ArUco detection failed: {e}')
            return

        if ids is not None and len(ids) > 0:
            marker_id = int(ids[0][0])
            name = MARKER_MAP.get(marker_id, f'unknown_{marker_id}')

            if name != self.last_published:
                out = String()
                out.data = name
                self.pub.publish(out)
                self.get_logger().info(f'Marker detected: {name} (id={marker_id})')
                self.last_published = name
        else:
            self.last_published = None


def main(args=None):
    rclpy.init(args=args)
    node = ArucoDetectorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()