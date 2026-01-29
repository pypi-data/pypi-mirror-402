from cuipyd.ipane import IPane


class BaseLayout(IPane):
    """A widget that can container other Panes"""

    def __init__(
        self,
        name=None,
        max_height=None,
        min_height=None,
        max_width=None,
        min_width=None,
    ):
        super().__init__(
            name=name,
            max_height=max_height,
            min_height=min_height,
            max_width=max_width,
            min_width=min_width,
        )
        self._children = []

    def _add_child(self, child: IPane, **kwargs):
        child._set_parent(self)
        self._children.append(child)

    def _render_frame(self, time_delta):
        self._draw_title()
        if not self._is_active:
            return
        if not self._has_window():
            return

        for child in self._children:
            if not child._is_active:
                continue
            child._render_frame(time_delta)
        self._refresh()

    def _refresh(self):
        for child in self._children:
            if child._is_active:
                child._refresh()
        self._window.refresh()
