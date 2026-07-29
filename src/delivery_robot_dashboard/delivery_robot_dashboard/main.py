import sys
import threading
import rclpy
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from delivery_robot_dashboard.dashboard_node import DashboardNode
from delivery_robot_dashboard.mission_control_window import MissionControlWindow
from delivery_robot_dashboard.manual_drive_window import ManualDriveWindow


def main():
    rclpy.init()
    node = DashboardNode()

    app = QApplication(sys.argv)

    manual_window = ManualDriveWindow(node)
    mission_window = MissionControlWindow(node, manual_window)

    mission_window.show()
    manual_window.show()

    # Spin rclpy alongside the Qt event loop without blocking the GUI
    spin_timer = QTimer()
    spin_timer.timeout.connect(lambda: rclpy.spin_once(node, timeout_sec=0.0))
    spin_timer.start(50)

    exit_code = app.exec_()

    node.destroy_node()
    rclpy.shutdown()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
