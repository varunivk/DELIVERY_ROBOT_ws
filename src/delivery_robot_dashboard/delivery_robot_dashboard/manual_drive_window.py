from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt


class ManualDriveWindow(QWidget):
    """Window 3: standalone arrow-button drive console. Always visible; safe to leave
    open in Autonomous mode since twist_mux ignores cmd_vel_manual unless the lock is set.
    """

    LINEAR_SPEED = 5
    ANGULAR_SPEED = 1

    def __init__(self, dashboard_node):
        super().__init__()
        self.node = dashboard_node
        self.setWindowTitle('Manual Drive Console')

        layout = QVBoxLayout()
        self.mode_label = QLabel('Mode: AUTONOMOUS (arrows inactive)')
        self.mode_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.mode_label)

        grid = QVBoxLayout()
        up_row = QHBoxLayout()
        up_btn = QPushButton('\u2191')
        up_row.addStretch()
        up_row.addWidget(up_btn)
        up_row.addStretch()
        grid.addLayout(up_row)

        mid_row = QHBoxLayout()
        left_btn = QPushButton('\u2190')
        stop_btn = QPushButton('STOP')
        right_btn = QPushButton('\u2192')
        mid_row.addWidget(left_btn)
        mid_row.addWidget(stop_btn)
        mid_row.addWidget(right_btn)
        grid.addLayout(mid_row)

        down_row = QHBoxLayout()
        down_btn = QPushButton('\u2193')
        down_row.addStretch()
        down_row.addWidget(down_btn)
        down_row.addStretch()
        grid.addLayout(down_row)

        layout.addLayout(grid)
        self.setLayout(layout)

        up_btn.pressed.connect(lambda: self.drive(self.LINEAR_SPEED, 0.0))
        down_btn.pressed.connect(lambda: self.drive(-self.LINEAR_SPEED, 0.0))
        left_btn.pressed.connect(lambda: self.drive(0.0, self.ANGULAR_SPEED))
        right_btn.pressed.connect(lambda: self.drive(0.0, -self.ANGULAR_SPEED))
        for btn in (up_btn, down_btn, left_btn, right_btn):
            btn.released.connect(self.stop)
        stop_btn.clicked.connect(self.stop)

        self.manual_active = False

    def set_mode_label(self, manual_active: bool):
        self.manual_active = manual_active
        text = 'Mode: MANUAL (arrows active)' if manual_active else 'Mode: AUTONOMOUS (arrows inactive)'
        self.mode_label.setText(text)

    def drive(self, linear_x, angular_z):
        self.node.send_manual_twist(linear_x, angular_z)

    def stop(self):
        self.node.send_manual_twist(0.0, 0.0)
