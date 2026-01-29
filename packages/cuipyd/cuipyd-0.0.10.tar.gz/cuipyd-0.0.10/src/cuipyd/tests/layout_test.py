from cuipyd.main_window import MainWindow
from cuipyd.pane import Pane
from cuipyd.layouts.directional_layout import VLayout, HLayout
from cuipyd.mouse import MouseEvent
from cuipyd.utils.direction import Direction


class TestPane(Pane):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._click_location = None
        self.scroll = False
        self.mouse_event = [None, None, None]

    def _register_mouse_event(self, mouse_event: MouseEvent):
        row = mouse_event.row
        column = mouse_event.column
        self._click_location = (row, column)
        if mouse_event.is_null:
            self.mouse_event = [None, None, None]
        else:
            self.mouse_event = [
                mouse_event.button,
                mouse_event.event_type,
                mouse_event.mod,
            ]

    def render_frame(self, time_delta):
        y, x = self._get_size()
        cmod = self._get_color_scheme().default_mod()
        click_cmod = self._get_color_scheme().default_mod(invert=True)
        for r in range(y):
            for c in range(x):
                char = self.default_char
                mod = cmod
                if self._click_location:
                    row, col = self._click_location
                    if r == row and c == col:
                        mod = click_cmod
                # self._window.addstr(r, c, self.default_char, mod)
                if self.scroll:
                    char = "M"
                self.add_str(char, r, c, mod)
        self.add_str(" ".join([str(s) for s in self.mouse_event]), 2, 2, mod)


class TestWindow(MainWindow):

    def __init__(self):
        super().__init__()
        self.layout = HLayout(name="Base Layout")
        self.set_root_layout(self.layout)
        self._delayed_rendering = True

        self.pane = TestPane(default_char="x", name="Xs", min_width=60)
        self.inner_layout = VLayout(name="Right Layout")

        self.layout._add_child(self.pane, min_width=60)
        # self.layout._add_child(self.pane2)
        self.layout._add_child(self.inner_layout)

        self.pane2 = TestPane(default_char="", name="Circles", max_height=7)
        self.pane3 = TestPane(
            default_char="i",
            name="Eyes",
            title_position=Direction.BOTTOM,
            overlap_title=True,
        )
        self.pane4 = TestPane(
            default_char="A",
            name="A",
            title_position=Direction.TOP_RIGHT,
            overlap_title=False,
        )

        self.layout_three = HLayout(name="HLayout")

        self.inner_layout._add_child(self.pane2)
        self.inner_layout._add_child(self.layout_three)

        self.layout_three._add_child(self.pane3)
        self.layout_three._add_child(self.pane4)

    def _process_character(self, char):
        ch = chr(char)
        cs = [c._get_size() for c in self._children]
        self._root._refresh()


if __name__ == "__main__":
    TestWindow().run()
