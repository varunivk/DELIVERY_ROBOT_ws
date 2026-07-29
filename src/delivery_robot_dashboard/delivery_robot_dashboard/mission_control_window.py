from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTextEdit, QRadioButton, QButtonGroup, QLineEdit)
from PyQt5.QtCore import QTimer

from delivery_robot_dashboard.package_selector_dialog import PackageSelectorDialog


class MissionControlWindow(QWidget):
    """Window 1: main dashboard. Mode toggle, package selection, mission buttons, live log."""

    def __init__(self, dashboard_node, manual_window):
        super().__init__()
        self.node = dashboard_node
        self.manual_window = manual_window
        self.setWindowTitle('Mission Control - WareBot')

        layout = QVBoxLayout()

        # Mode section
        layout.addWidget(QLabel('<b>Mode</b>'))
        mode_row = QHBoxLayout()
        self.auto_radio = QRadioButton('Autonomous')
        self.manual_radio = QRadioButton('Manual')
        self.auto_radio.setChecked(True)
        group = QButtonGroup(self)
        group.addButton(self.auto_radio)
        group.addButton(self.manual_radio)
        mode_row.addWidget(self.auto_radio)
        mode_row.addWidget(self.manual_radio)
        layout.addLayout(mode_row)
        self.auto_radio.toggled.connect(self.on_mode_changed)

        # Waypoint tools
        layout.addWidget(QLabel('<b>Waypoint Tools</b>'))
        wp_row = QHBoxLayout()
        self.wp_name_input = QLineEdit()
        self.wp_name_input.setPlaceholderText('Waypoint name e.g. aisle1')
        record_btn = QPushButton('Record Current Position')
        wp_row.addWidget(self.wp_name_input)
        wp_row.addWidget(record_btn)
        layout.addLayout(wp_row)
        record_btn.clicked.connect(self.on_record_waypoint)

        # Mission control section
        layout.addWidget(QLabel('<b>Mission Control</b>'))
        select_btn = QPushButton('Select Package / Destination')
        select_btn.clicked.connect(self.on_select_package)
        layout.addWidget(select_btn)

        btn_row = QHBoxLayout()
        start_btn = QPushButton('Start Delivery')
        cancel_btn = QPushButton('Cancel')
        home_btn = QPushButton('Return Home')
        btn_row.addWidget(start_btn)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(home_btn)
        layout.addLayout(btn_row)
        start_btn.clicked.connect(self.on_start)
        cancel_btn.clicked.connect(self.on_cancel)
        home_btn.clicked.connect(self.on_home)

        # Status log
        layout.addWidget(QLabel('<b>Status Log</b>'))
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        layout.addWidget(self.log_box)

        self.setLayout(layout)

        self._last_status = None
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.poll_status)
        self.poll_timer.start(500)

    def poll_status(self):
        text = self.node.status_text
        if text != self._last_status:
            self.log_box.append(text)
            self._last_status = text

    def on_mode_changed(self):
        manual_enabled = self.manual_radio.isChecked()
        self.node.set_manual_mode(manual_enabled)
        self.manual_window.set_mode_label(manual_enabled)
        self.log_box.append(f'Mode switched to {"MANUAL" if manual_enabled else "AUTONOMOUS"}')

    def on_select_package(self):
        dlg = PackageSelectorDialog(self.node, self)
        dlg.exec_()

    def on_record_waypoint(self):
        name = self.wp_name_input.text().strip()
        if not name:
            self.log_box.append('Enter a waypoint name first.')
            return
        success, message = self.node.record_waypoint(name)
        self.log_box.append(message)

    def on_start(self):
        success, message = self.node.start_delivery()
        self.log_box.append(message)

    def on_cancel(self):
        success, message = self.node.cancel_delivery()
        self.log_box.append(message)

    def on_home(self):
        success, message = self.node.return_home()
        self.log_box.append(message)
