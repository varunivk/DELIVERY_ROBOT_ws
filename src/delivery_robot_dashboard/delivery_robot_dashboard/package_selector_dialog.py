from PyQt5.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QPushButton, QLabel


class PackageSelectorDialog(QDialog):
    """Window 2: popup for selecting which delivery point(s) to queue."""

    def __init__(self, dashboard_node, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Select Delivery Points')
        self.node = dashboard_node

        layout = QVBoxLayout()
        layout.addWidget(QLabel('Choose one or more delivery points:'))

        self.checkboxes = {}
        for point in ['aisle1', 'aisle2', 'dock']:
            cb = QCheckBox(point.capitalize())
            self.checkboxes[point] = cb
            layout.addWidget(cb)

        confirm_btn = QPushButton('Confirm & Queue')
        confirm_btn.clicked.connect(self.confirm)
        layout.addWidget(confirm_btn)

        self.setLayout(layout)

    def confirm(self):
        selected = [name for name, cb in self.checkboxes.items() if cb.isChecked()]
        if selected:
            self.node.request_points(selected)
        self.accept()
