import curses
from enum import Enum
from cuipyd.pane import Pane
from cuipyd.mouse import MouseEvent, MouseEventType


class PopupBorderStyle(Enum):
    DEFAULT = 0
    BLOCK = 1
    CHECKER = 2
    SMALL_BLOCK = 3
    BARBED = 4


class BasePopup(Pane):

    def __init__(
        self,
        title=None,
        name=None,
        max_height=None,
        min_height=None,
        max_width=None,
        min_width=None,
        row_percent_size=None,
        col_percent_size=None,
        border_style=PopupBorderStyle.DEFAULT,
    ):
        super().__init__(
            name=name,
            max_height=max_height,
            min_height=min_height,
            max_width=max_width,
            min_width=min_width,
        )
        self.title = title
        self._row_percent_size = row_percent_size
        self._col_percent_size = col_percent_size
        self._exit_highlighted = False
        self._border_style = border_style

    def _mouse_focus_ended(self):
        self._exit_highlighted = False

    def _register_mouse_event(self, mouse_event: MouseEvent):
        row = mouse_event.row
        col = mouse_event.column
        if row == 0 and col in [0, 1, 2]:
            self._exit_highlighted = True
            if mouse_event.event_type == MouseEventType.CLICKED:
                self.close()
        else:
            self._exit_highlighted = False

    def _pre_close(self):
        pass

    def close(self):
        self._pre_close()
        self._parent.remove_popup(self)

    def _get_popup_size(self, parent_rows, parent_cols):
        raw_rows, raw_cols = self._get_raw_size()
        row_pct = 0.6
        col_pct = 0.75
        if self._row_percent_size:
            row_pct = self._row_percent_size
        if self._col_percent_size:
            col_pct = self._col_percent_size

        num_rows = int(row_pct * raw_rows)
        num_cols = int(col_pct * raw_cols)

        if self._min_height and num_rows < self._min_height:
            num_rows = self._min_height
        if self._max_height and num_rows > self._max_height:
            num_rows = self._max_height

        if self._min_width and num_cols < self._min_width:
            num_cols = self._min_width
        if self._max_width and num_cols > self._max_width:
            num_cols = self._max_width

        if num_rows > raw_rows:
            num_rows = raw_rows
        if num_cols > raw_cols:
            num_cols = raw_cols

        return num_rows, num_cols

    def _get_size(self):
        raw_rows, raw_cols = self._get_raw_size()
        return raw_rows - 2, raw_cols - 2

    def _tweak_row_col(self, row, col):
        return row + 1, col + 1

    def _draw_border(self):
        y, x = self._get_raw_size()

        ul = curses.ACS_ULCORNER
        ur = curses.ACS_URCORNER
        ll = curses.ACS_LLCORNER
        lr = curses.ACS_LRCORNER
        lvl = curses.ACS_VLINE
        rvl = curses.ACS_VLINE
        uhl = curses.ACS_HLINE
        lhl = curses.ACS_HLINE

        mod = self._get_color_scheme().default_mod()
        if self._border_style == PopupBorderStyle.SMALL_BLOCK:
            ul = curses.ACS_BLOCK
            ur = curses.ACS_BLOCK
            ll = curses.ACS_BLOCK
            lr = curses.ACS_BLOCK
            lvl = curses.ACS_BLOCK
            rvl = curses.ACS_BLOCK
            uhl = curses.ACS_BLOCK
            lhl = curses.ACS_BLOCK

        elif self._border_style == PopupBorderStyle.CHECKER:
            ul = curses.ACS_BOARD
            ur = curses.ACS_BOARD
            ll = curses.ACS_BOARD
            lr = curses.ACS_BOARD
            lvl = curses.ACS_BOARD
            rvl = curses.ACS_BOARD
            uhl = curses.ACS_BOARD
            lhl = curses.ACS_BOARD

        elif self._border_style == PopupBorderStyle.BLOCK:
            mod = self._get_color_scheme().default_mod(invert=True)
            ul = ord(" ")
            ur = ord(" ")
            ll = ord(" ")
            lr = ord(" ")
            lvl = ord(" ")
            rvl = ord(" ")
            uhl = ord(" ")
            lhl = ord(" ")

        elif self._border_style == PopupBorderStyle.BARBED:
            ul = curses.ACS_PLUS
            ur = curses.ACS_PLUS
            ll = curses.ACS_PLUS
            lr = curses.ACS_PLUS
            lvl = curses.ACS_SBSS
            rvl = curses.ACS_SSSB
            uhl = curses.ACS_SSBS
            lhl = curses.ACS_BSSS

        # Draw Corners
        self._window.addch(0, 0, ul, mod)
        self._window.addch(0, x - 1, ur, mod)
        self._window.addch(y - 1, 0, ll, mod)
        try:
            self._window.addch(y - 1, x - 1, lr, mod)
        except:
            pass

        for row in range(1, y - 1):
            self._window.addch(row, 0, lvl, mod)
            self._window.addch(row, x - 1, rvl, mod)

        for col in range(1, x - 1):
            self._window.addch(0, col, uhl, mod)
            self._window.addch(y - 1, col, lhl, mod)

        # self._window.addch(0, 1, ord('X'), mod)
        if self._exit_highlighted:
            mod = self._get_color_scheme().header_mod(invert=True)

        self._window.addstr(0, 0, "[X]", mod)

    def render_frame(self, time_delta):
        super().render_frame(time_delta)
        self._draw_border()
