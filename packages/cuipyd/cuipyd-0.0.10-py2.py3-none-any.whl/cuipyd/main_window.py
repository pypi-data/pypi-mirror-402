import os
import curses
import time

from typing import Tuple
from contextlib import contextmanager

import setproctitle

from cuipyd.mouse import get_mouse_event, MouseEvent
from cuipyd.logging import log
from cuipyd.threads import StoppableLoopThread
from cuipyd.layouts.layout import BaseLayout
from cuipyd.colors.color_scheme import ColorScheme
from cuipyd.popups.popup import BasePopup


class MainWindow:

    def __init__(self, title: str = None, color_scheme: ColorScheme = None):
        self._children = []
        self._last_frame_time = time.time()
        self._min_frame_wait_time = 0.2
        self._prepare_curses()
        self._update_title(title)
        self._base_layout = None
        self._delayed_rendering = True
        if color_scheme is None:
            color_scheme = ColorScheme()
        self._color_scheme = color_scheme
        self._popup_stack = []

    def set_root_layout(self, layout: BaseLayout):
        self._base_layout = layout
        self._base_layout._set_parent(self)
        rows, cols = self._get_size()
        self._base_layout._update_window_size(rows, cols, 0, 0)

    def _get_color_scheme(self):
        return self._color_scheme

    @property
    def _root(self):
        return self

    @property
    def _window(self):
        return self._screen

    def _update_title(self, title):
        self._title = title
        if self._title:
            setproctitle.setproctitle(self._title)

    def _get_time_delta(self) -> float:
        now_time = time.time()
        time_delta = now_time - self._last_frame_time
        self._last_frame_time = now_time
        return time_delta

    def _render_loop(self) -> None:
        time.sleep(self._min_frame_wait_time)
        time_delta = self._get_time_delta()
        self._render_frame(time_delta)

    def _render_frame(self, time_delta):
        if self._has_popup():
            for popup in self._popup_stack:
                popup._render_frame(time_delta)
        else:
            if self._base_layout:
                self._base_layout._render_frame(time_delta)
        self._screen.refresh()
        # log("Render")

    def _start_rendering(self) -> None:
        if self._delayed_rendering:
            return
        self._render_thread = StoppableLoopThread(target=self._render_loop)
        self._render_thread.start()

    def _stop_rendering(self) -> None:
        if self._delayed_rendering:
            return
        self._render_thread.stop()
        self._render_thread.join()

    def terminate(self) -> None:
        curses.echo()
        curses.nocbreak()
        self._screen.keypad(False)
        curses.endwin()

    def _set_preparation_options(self) -> None:
        if curses.has_colors():
            curses.start_color()

        curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
        # curses.mousemask(1)
        print("\033[?1003h")  # enable mouse tracking with the XTERM API

        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        self._screen.keypad(True)

    def _prepare_curses(self) -> None:
        self._screen = curses.initscr()
        self._set_preparation_options()

    def _process_character(self, char) -> None:
        pass

    def _refresh(self):
        self._base_layout._refresh()

    def _refresh_main_window_size(self):
        size = self._get_size()
        if self._base_layout is not None:
            self._base_layout._update_window_size(size[0], size[1], 0, 0)

    @contextmanager
    def _pause_rendering(self):
        if self._delayed_rendering:
            yield
            return
        has_render_thread = hasattr(self, "_render_thread")
        if has_render_thread:
            self._render_thread.pause()
        yield
        if has_render_thread:
            self._render_thread.unpause()

    def _send_mouse_event(self, row: int, col: int, button):
        event = get_mouse_event(row, col, button)
        self._register_mouse_event(event)

    def _register_mouse_event(self, mouse_event: MouseEvent):
        row = mouse_event.row
        col = mouse_event.column

        if self._has_popup():
            top_popup = self._popup_stack[-1]
            p_rows, p_cols = top_popup._get_raw_size()
            s_row, s_col = top_popup._get_top_left()
            if row in range(s_row, s_row + p_rows) and col in range(
                s_col, s_col + p_cols
            ):
                mouse_event.row -= s_row
                mouse_event.column -= s_col
                top_popup._register_mouse_event(mouse_event)
                return
            top_popup._mouse_focus_ended()
        else:
            if self._base_layout._shift_down_from_title():
                new_r, new_c = self._base_layout._tweak_row_col(
                    mouse_event.row, mouse_event.column, reverse=True
                )
                mouse_event.row = new_r
                mouse_event.column = new_c

            self._base_layout._register_mouse_event(mouse_event)

    def _try_render_delayed(self):
        if self._delayed_rendering:
            self._render_frame(0)
            self._base_layout._refresh()

    def _has_popup(self):
        return len(self._popup_stack) > 0

    def _run_internal(self, *args, **kwargs) -> None:
        self._start_rendering()
        self._try_render_delayed()
        try:
            while True:
                ch = self._screen.getch()
                log(chr(ch))
                if ch == curses.KEY_RESIZE:
                    with self._pause_rendering():
                        log(str(self._base_layout))
                        self._refresh_main_window_size()

                elif ch == curses.KEY_MOUSE:
                    _, x, y, _, button = curses.getmouse()
                    self._send_mouse_event(y, x, button)
                else:
                    if chr(ch) == "q":
                        self._edit_file("test.txt")
                    try:
                        self._process_character(ch)
                    except KeyboardInterrupt:
                        self._stop_rendering()
                        self.terminate()

                self._try_render_delayed()

        except KeyboardInterrupt:
            self._stop_rendering()
            self.terminate()
        except Exception as e:
            self._stop_rendering()
            self.terminate()
            raise e

    def run(self):
        curses.wrapper(self._run_internal)

    """ Rows, Columns """

    def _get_size(self) -> Tuple[int, int]:
        return self._screen.getmaxyx()

    def _edit_file(self, filename):
        self._render_thread.pause()
        curses.def_prog_mode()
        curses.endwin()

        log("Start Editing")
        editor = os.environ.get("EDITOR", "vi")
        os.system("{} {}".format(editor, filename))
        log("Done Editing")

        curses.reset_prog_mode()
        self._refresh_main_window_size()
        self._window.refresh()
        self._render_thread.unpause()

        # For some reason to hide the cursor we need to do this
        curses.curs_set(1)
        curses.curs_set(0)

    def add_popup(self, popup: BasePopup):
        self._popup_stack.append(popup)
        popup._set_parent(self)
        rows, cols = self._get_size()
        prows, pcols = popup._get_popup_size(rows, cols)

        row_start = (rows - prows) // 2
        col_start = (cols - pcols) // 2
        popup._update_window_size(prows, pcols, row_start, col_start)

    def remove_popup(self, popup: BasePopup):
        for i in range(len(self._popup_stack)):
            check_popup = self._popup_stack[i]
            if check_popup == popup:
                self._popup_stack.pop(i)
                return

    def pop_popup(self):
        if self._popup_stack:
            self.remove_popup(self._popup_stack[-1])


if __name__ == "__main__":
    MainWindow().run()
