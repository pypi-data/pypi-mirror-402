from cuipyd.layouts.layout import BaseLayout
from cuipyd.utils.general import ignore_exceptions
from cuipyd.mouse import MouseEvent, MouseButton


class TabLayout(BaseLayout):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._active_tab = 0
        self._show_tabs = True
        self._tabs_on_top = True
        self._tab_coordinates = {}

    def _set_tabs_on_top(self, tabs_on_top):
        self._tabs_on_top = tabs_on_top
        self._resize()

    def _add_child(self, child, **kwargs):
        super()._add_child(child, **kwargs)
        child._show_title = False

        self._set_tab_active(0)
        self._resize()

    def _set_tab_active(self, index: int):
        index = index % len(self._children)
        for i in range(len(self._children)):
            child = self._children[i]
            if i == index:
                child._is_active = True
            else:
                child._is_active = False
        self._active_tab = index
        # self._children[index]._window.refresh()
        # self._window.refresh()

    def _next_tab(self):
        self._set_tab_active(self._active_tab + 1)

    def _previous_tab(self):
        self._set_tab_active(self._active_tab - 1)

    def _update_window_size(self, rows, cols, r_pos, c_pos):
        super()._update_window_size(rows, cols, r_pos, c_pos)
        self._resize()

    def _resize(self):
        rows, cols = self._get_raw_size()
        row_pos = 0
        col_pos = 0
        if self._show_tabs:
            rows -= 1
            if self._tabs_on_top:
                row_pos = 1

        if self._shift_down_from_title():
            rows -= 1
            row_pos = self._tweak_row_col(row_pos, 0)[0]

        for child in self._children:
            child._update_window_size(rows, cols, row_pos, col_pos)

    def _get_left_triangle(self):
        if self._tabs_on_top:
            return " "
        else:
            return " "

    def _get_right_triangle(self):
        if self._tabs_on_top:
            return " "
        else:
            return " "

    def _get_tab_row(self):
        return 0 if self._tabs_on_top else self._get_raw_size()[0] - 1

    def _get_tab_str_length(self, tab_index: int):
        return 4 + len(self._children[tab_index]._name)

    def _draw_single_tab(self, column: int, tab_index: int):
        row = self._get_tab_row()
        left_triangle = self._get_left_triangle()
        right_triangle = self._get_right_triangle()
        tab_name = self._children[tab_index]._name
        tab_text = left_triangle + tab_name + right_triangle
        color_mod = self._get_color_scheme().default_mod(invert=True)
        if tab_index == self._active_tab:
            color_mod = self._get_color_scheme().important_mod(invert=True)
        self.add_str(tab_text, row, column, color_mod)

        self._tab_coordinates[tab_index] = (column, column + len(tab_text))

        return column + len(tab_text)

    def _get_tab_sizes(self):
        sizes = []
        for i in range(len(self._children)):
            sizes.append(self._get_tab_str_length(i))
        return sizes

    def _draw_tabs(self):
        self._tab_coordinates = {}
        sizes = self._get_tab_sizes()
        screen_width = self._get_raw_size()[1]
        col = 0

        # All tabs fit in screen
        if sum(sizes) < screen_width:
            for i in range(len(self._children)):
                col = self._draw_single_tab(col, i)
            return

        shown_tabs = [self._get_tab_str_length(self._active_tab)]
        lower_ind = self._active_tab
        higher_ind = self._active_tab + 1
        did_lower = True
        while sum(sizes[lower_ind:higher_ind]) < screen_width - 2:
            if did_lower:
                if higher_ind < len(self._children):
                    higher_ind += 1
                did_lower = False
            else:
                if lower_ind - 1 >= 0:
                    lower_ind -= 1
                did_lower = True
            if lower_ind == 0 and higher_ind == len(self._children) - 1:
                break

        if did_lower:
            lower_ind += 1
        else:
            higher_ind -= 1

        right_arrow = " "
        left_arrow = " "

        row = self._get_tab_row()
        col = 0
        color_mod = self._get_color_scheme().default_mod()
        if lower_ind != 0:
            self.add_str(left_arrow, row, 0, color_mod)
            col += 2

        if higher_ind == len(self._children):
            tab_text_size = sum(sizes[lower_ind:higher_ind])
            start_offset = (screen_width - 1) - tab_text_size
            old_start = col
            col = start_offset
            num_spaces = col - old_start
            self.add_str(" " * num_spaces, row, old_start, color_mod)

        for i in range(lower_ind, higher_ind):
            col = self._draw_single_tab(col, i)

        num_spaces = (screen_width - 2) - col
        self.add_str(" " * num_spaces, row, col, color_mod)

        if higher_ind != len(self._children):
            with ignore_exceptions():
                self.add_str(right_arrow, row, screen_width - 2, color_mod)
        else:
            num_spaces = screen_width - col
            with ignore_exceptions():
                self.add_str(" " * num_spaces, row, col, color_mod)

    def _render_frame(self, time_delta):
        self._draw_tabs()
        super()._render_frame(time_delta)

    def _process_tab_click(self, column, mouse_event: MouseEvent):
        if mouse_event.button == MouseButton.LEFT_MOUSE:
            for tab_index in self._tab_coordinates:
                start, end = self._tab_coordinates[tab_index]
                if column in range(start, end):
                    self._set_tab_active(tab_index)
                    break

    def _register_mouse_event(self, mouse_event: MouseEvent):
        row = mouse_event.row
        column = mouse_event.column
        if not self._children:
            return

        y, x = self._get_size()
        if row == 0 and self._tabs_on_top:
            self._process_tab_click(column, mouse_event)
            return
        if row == y - 1 and not self._tabs_on_top:
            self._process_tab_click(column, mouse_event)
            return

        if self._tabs_on_top:
            mouse_event.row -= 1

        clear_mouse_event = MouseEvent.get_null()
        for ind in range(len(self._children)):
            child = self._children[ind]
            if ind == self._active_tab:
                if child._shift_down_from_title():
                    new_r, new_c = child._tweak_row_col(
                        mouse_event.row, mouse_event.column, reverse=True
                    )
                    mouse_event.row = new_r
                    mouse_event.column = new_c

                child._register_mouse_event(mouse_event)
            else:
                child._register_mouse_event(clear_mouse_event)
        self._refresh()
