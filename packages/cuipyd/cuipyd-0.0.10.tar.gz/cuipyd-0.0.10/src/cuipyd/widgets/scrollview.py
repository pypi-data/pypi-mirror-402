from cuipyd.mouse import MouseButton, MouseEvent, MouseMod
from cuipyd.pane import Pane
from cuipyd.layouts import Layout


class ScrollView(Pane):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._top_left = (0, 0)

    def render_frame(self, time_delta):
        super().render_frame(time_delta)

    def scroll(self, row_delta:int, col_delta:int):
        r, c = self._top_left
        self._top_left = (r - row_delta, c + col_delta)

    def scroll_vertically(self, amt:int):
        self.scroll(amt, 0)

    def scroll_horizontally(self, amt:int):
        self.scroll(0, amt)

    def _register_mouse_event(self, mouse_event: MouseEvent):
        if mouse_event.is_null:
            return

        if mouse_event.mod == MouseMod.NONE:
            # Vertical Scroll
            if mouse_event.button == MouseButton.WHEEL_DOWN:
                self.scroll_vertically(-1)
            if mouse_event.button == MouseButton.WHEEL_UP:
                self.scroll_vertically(1)
        elif mouse_event.mod == MouseMod.CONTROL:
            # Horizontal Scroll
            if mouse_event.button == MouseButton.WHEEL_DOWN:
                self.scroll_horizontally(1)
            if mouse_event.button == MouseButton.WHEEL_UP:
                self.scroll_horizontally(-1)

        return super()._register_mouse_event(mouse_event)

