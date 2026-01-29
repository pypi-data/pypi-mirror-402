from cuipyd.ipane import IPane
from cuipyd.utils.direction import Direction


class Pane(IPane):

    def __init__(
        self,
        default_char=" ",
        name=None,
        max_height=None,
        min_height=None,
        max_width=None,
        min_width=None,
        title_position=Direction.TOP_LEFT,
        overlap_title=False,
        show_title=None,
    ):

        super().__init__(
            name=name,
            max_height=max_height,
            min_height=min_height,
            max_width=max_width,
            min_width=min_width,
            title_position=title_position,
            overlap_title=overlap_title,
            show_title=show_title,
        )
        self.default_char = default_char

    def _refresh(self):
        self._window.refresh()

    def render_frame(self, time_delta):
        y, x = self._get_raw_size()
        cmod = self._get_color_scheme().default_mod()
        for r in range(y):
            for c in range(x):
                self.add_str(self.default_char, r, c, cmod)

    def _render_frame(self, time_delta):
        if not self._has_window():
            return
        self.render_frame(time_delta)
        self._draw_title()
        self._refresh()
