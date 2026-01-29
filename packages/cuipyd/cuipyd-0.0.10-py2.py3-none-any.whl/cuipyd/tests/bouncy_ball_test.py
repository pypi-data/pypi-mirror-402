from cuipyd.main_window import MainWindow
from cuipyd.ipane import IPane
from cuipyd.pane import Pane
from cuipyd.tuples import MathTup
from cuipyd.layouts.directional_layout import HLayout


class TestPane(Pane):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class TestWindow(MainWindow):

    def __init__(self):
        super().__init__()
        self.gravity = 9.8
        self.max_width = 20.0
        self.max_height = 15.0
        self.ball_position = MathTup((2, 2))
        self.ball_velocity = MathTup((2, 10))
        self.layout = HLayout()
        self.pane = TestPane()
        self.layout._add_child(self.pane)
        self.set_root_layout(self.layout)

    def _render_frame(self, time_delta):
        gravity = MathTup((0, -self.gravity * time_delta))
        self.ball_velocity = gravity + self.ball_velocity
        self.ball_position = time_delta * self.ball_velocity + self.ball_position

        x, y = self.ball_position
        vx, vy = self.ball_velocity
        if x < 0 or x > self.max_width:
            self.ball_velocity = (-vx, vy)
        if y < 0 and vy < 0:
            self.ball_velocity = (vx, -vy * 0.90)

        max_rows, max_columns = self._get_size()
        h_prop = x / self.max_width
        column = int(max_columns * h_prop)

        v_prop = y / self.max_height
        row = max_rows - int(max_rows * v_prop)

        try:
            self._screen.clear()
            self._screen.addch(row, column, ord("O"))
            self._screen.refresh()
        except:
            pass


if __name__ == "__main__":
    TestWindow().run()
