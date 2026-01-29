import curses
from typing import Tuple
from cuipyd.main_window import MainWindow
from cuipyd.pane import Pane
from cuipyd.layouts.tab_layout import TabLayout
from cuipyd.popups.popup import PopupBorderStyle
from cuipyd.popups.text_popup import TextPopup
from cuipyd.mouse import MouseEvent, MouseButton, MouseEventType
from cuipyd.widgets.spreadsheet import SpreadSheet

import time


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
                if char is None:
                    char = " "
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


class MySpreadSheet(SpreadSheet):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.time = False
        self._use_row_labels = False
        self._use_col_labels = False
        self._base_column_width = 8
        self._enable_negative_columns = False
        self._enable_negative_rows = False
        self._selected_cell = (50, 2)
        self._max_columns = 10
        self._data = {}

    def render_frame(self, time_delta):
        super().render_frame(time_delta)
        start_time = time.time()
        self._draw_grid()
        end_time = time.time()
        if self.time:
            raise Exception(end_time - start_time)

    def _get_cell_value(self, row: int, col: int):
        if row in self._data and col in self._data[row]:
            return self._data[row][col]
        return row + col

    def _process_mouse_action(self, cell_pos: Tuple[int, int], mouse_event: MouseEvent):
        row, col = cell_pos
        if mouse_event.event_type == MouseEventType.CLICKED:
            if row not in self._data:
                self._data[row] = {}
            self._data[row][col] = "Potato"


class ColorPane(Pane):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _register_mouse_event(self, mouse_event: MouseEvent):
        if mouse_event.is_null:
            return
        row = mouse_event.row
        column = mouse_event.column
        if mouse_event.button == MouseButton.LEFT_MOUSE:
            self._click_location = [row, column]
        self._render_frame(0)
        self._refresh()

    def render_frame(self, time_delta):
        super().render_frame(time_delta)
        if not self.default_char == " ":
            return
        # return
        y, x = self._get_size()
        cmod = self._get_color_scheme().default_mod()
        click_cmod = self._get_color_scheme().default_mod(invert=True)

        special_names = [
            "ACS_BBSS",
            "ACS_BLOCK",
            "ACS_BOARD",
            "ACS_BSBS",
            "ACS_BSSB",
            "ACS_BSSS",
            "ACS_BTEE",
            "ACS_BULLET",
            "ACS_CKBOARD",
            "ACS_DARROW",
            "ACS_DEGREE",
            "ACS_DIAMOND",
            "ACS_GEQUAL",
            "ACS_HLINE",
            "ACS_LANTERN",
            "ACS_LARROW",
            "ACS_LEQUAL",
            "ACS_LLCORNER",
            "ACS_LRCORNER",
            "ACS_LTEE",
            "ACS_NEQUAL",
            "ACS_PI",
            "ACS_PLMINUS",
            "ACS_PLUS",
            "ACS_RARROW",
            "ACS_RTEE",
            "ACS_S1",
            "ACS_S3",
            "ACS_S7",
            "ACS_S9",
            "ACS_SBBS",
            "ACS_SBSB",
            "ACS_SBSS",
            "ACS_SSBB",
            "ACS_SSBS",
            "ACS_SSSB",
            "ACS_SSSS",
            "ACS_STERLING",
            "ACS_TTEE",
            "ACS_UARROW",
            "ACS_ULCORNER",
            "ACS_URCORNER",
            "ACS_VLINE",
        ]

        ind = 0
        for r in range(y):
            for c in range(x):
                # char = curses_specials[ind % len(curses_specials)]
                special_name = special_names[r % len(special_names)]
                special_char = getattr(curses, special_name)
                self.add_str(special_name, r, 0)
                self.add_char(special_char, r, 2 + len(special_name), raw=True)


class TestPopup(TextPopup):

    def __init__(self, *args, **kwargs):
        kwargs["border_style"] = PopupBorderStyle.BLOCK
        super().__init__(*args, **kwargs)


class TestWindow(MainWindow):

    def __init__(self):
        super().__init__()
        self.layout = TabLayout(name="Tab Layout")
        self.set_root_layout(self.layout)
        self.popup = None
        self.spreadsheet = None

        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        for letter in list(letters):
            if letter == "B":
                pane = MySpreadSheet(name="Spradsheet")
                self.spreadsheet = pane
            elif letter == "C":
                pane = TestPane(name="TestPane", default_char="C")
            else:
                pane = ColorPane(default_char=letter, name="Pane{}".format(letter))
                if letter == "A":
                    pane._name = "Char Showcase"
                    pane.default_char = " "
                if letter == "B":
                    pane._name = "BIG NAME FOR B"
                if letter == "Y":
                    pane._name = "OTHER BIG NAME HERE"

            self.layout._add_child(pane)
        # self.layout._set_tab_active(23)
        # self.layout._set_tabs_on_top(False)

    def _process_character(self, char):
        if chr(char) == "b":
            self.layout._next_tab()
        if chr(char) == "B":
            self.layout._previous_tab()
        if chr(char) == "p":
            self.popup = TestPopup()
            self.add_popup(self.popup)
        if chr(char) == "P":
            self.pop_popup()
            # if self.popup:
            #    self.popup.close()
        if chr(char) == "w":
            self.spreadsheet.move_vertically(1)
        if chr(char) == "s":
            self.spreadsheet.move_vertically(-1)
        if chr(char) == "d":
            self.spreadsheet.move_horizontally(1)
        if chr(char) == "a":
            self.spreadsheet.move_horizontally(-1)
        if chr(char) == "t":
            self.spreadsheet.time = True


if __name__ == "__main__":
    TestWindow().run()
