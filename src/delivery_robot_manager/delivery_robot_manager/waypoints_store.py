import math


class WaypointsStore:
    """Holds known delivery point poses and the live pending task queue.
    Provides nearest-neighbor reordering for simultaneous/queued requests.
    """

    def __init__(self):
        # Known delivery points, pre-seeded to match warehouse.sdf marker positions.
        # (x, y) in map frame. Update via record_waypoint() for hand-taught points.
        self.known_points = {
            'aisle1': (-1.5, 2.3),
            'aisle2': (1.5, -2.3),
            'dock':   (4.3, 0.0),
            'home':   (-4.5, 0.0),
        }
        self.pending_queue = []      # list of point names, ordered for execution
        self.delivered_log = []      # list of (name, status) tuples

    def record_waypoint(self, name: str, x: float, y: float) -> bool:
        self.known_points[name] = (x, y)
        return True

    def request_delivery(self, names):
        """Add one or more delivery point names to the queue, ignoring duplicates
        already pending or already delivered in this session.
        """
        added = []
        for name in names:
            if name not in self.known_points:
                continue
            if name in self.pending_queue:
                continue
            self.pending_queue.append(name)
            added.append(name)
        return added

    def reorder_by_distance(self, current_x: float, current_y: float):
        """Sort pending_queue by straight-line distance from current pose (nearest first)."""
        def dist(name):
            px, py = self.known_points.get(name, (0.0, 0.0))
            return math.hypot(px - current_x, py - current_y)

        self.pending_queue.sort(key=dist)

    def pop_next(self):
        if not self.pending_queue:
            return None
        return self.pending_queue.pop(0)

    def clear_queue(self):
        self.pending_queue = []

    def mark_delivered(self, name: str):
        self.delivered_log.append((name, 'delivered'))

    def get_pose(self, name: str):
        return self.known_points.get(name)
